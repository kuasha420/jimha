use rodio::buffer::SamplesBuffer;
use rodio::{DeviceSinkBuilder, MixerDeviceSink, Player};
use std::num::NonZero;
use std::sync::{Arc, Mutex};

pub const PENTATONIC_FREQUENCIES: [f32; 11] = [
    261.63,  // C4
    293.66,  // D4
    329.63,  // E4
    392.00,  // G4
    440.00,  // A4
    523.25,  // C5
    587.33,  // D5
    659.25,  // E5
    783.99,  // G5
    880.00,  // A5
    1046.50, // C6
];

pub const SAMPLE_RATE: u32 = 44_100;
pub const MAX_PEDIATRIC_VOLUME: f32 = 0.80;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InstrumentKind {
    Celesta,
    Marimba,
    Kalimba,
    MusicBox,
}

impl InstrumentKind {
    pub fn parse(s: &str) -> Self {
        match s.to_ascii_lowercase().as_str() {
            "marimba" => Self::Marimba,
            "kalimba" => Self::Kalimba,
            "music_box" => Self::MusicBox,
            _ => Self::Celesta,
        }
    }

    pub fn params(&self) -> (&'static [f32], &'static [f32], f32, f32, f32) {
        // (multipliers, gains, decay_body_rate, decay_shimmer_rate, attack_seconds)
        match self {
            Self::Celesta => (
                &[1.0, 2.0, 3.0, 4.2, 5.4],
                &[1.0, 0.35, 0.18, 0.10, 0.05],
                2.5,
                5.5,
                0.004,
            ),
            Self::Marimba => (
                &[1.0, 3.0, 9.2, 12.0],
                &[1.0, 0.40, 0.08, 0.03],
                4.5,
                9.0,
                0.002,
            ),
            Self::Kalimba => (
                &[1.0, 2.76, 5.4, 8.1],
                &[1.0, 0.25, 0.15, 0.06],
                2.0,
                4.0,
                0.005,
            ),
            Self::MusicBox => (
                &[1.0, 2.0, 3.0, 4.0, 6.0],
                &[1.0, 0.50, 0.30, 0.15, 0.08],
                1.8,
                3.0,
                0.001,
            ),
        }
    }
}

#[derive(Debug)]
struct AudioEngineInner {
    pcm_cache: Mutex<Vec<Vec<f32>>>,
    device_sink: Option<MixerDeviceSink>,
    note_index: Mutex<usize>,
    current_instrument: Mutex<InstrumentKind>,
}

#[derive(Debug, Clone)]
pub struct NativeAudioEngine {
    inner: Arc<AudioEngineInner>,
}

impl Default for NativeAudioEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl NativeAudioEngine {
    pub fn new() -> Self {
        let device_sink = DeviceSinkBuilder::open_default_sink().ok();

        let mut pcm_cache = Vec::with_capacity(PENTATONIC_FREQUENCIES.len());
        for &freq in &PENTATONIC_FREQUENCIES {
            pcm_cache.push(Self::synthesize_chime_pcm(freq, InstrumentKind::Celesta));
        }

        let inner = AudioEngineInner {
            pcm_cache: Mutex::new(pcm_cache),
            device_sink,
            note_index: Mutex::new(0),
            current_instrument: Mutex::new(InstrumentKind::Celesta),
        };

        Self {
            inner: Arc::new(inner),
        }
    }

    pub fn set_instrument(&self, instrument: &str) {
        let kind = InstrumentKind::parse(instrument);
        let mut cur = match self.inner.current_instrument.lock() {
            Ok(g) => g,
            Err(p) => p.into_inner(),
        };
        if *cur == kind {
            return;
        }
        *cur = kind;
        drop(cur);

        let mut new_cache = Vec::with_capacity(PENTATONIC_FREQUENCIES.len());
        for &freq in &PENTATONIC_FREQUENCIES {
            new_cache.push(Self::synthesize_chime_pcm(freq, kind));
        }

        let mut cache_guard = match self.inner.pcm_cache.lock() {
            Ok(g) => g,
            Err(p) => p.into_inner(),
        };
        *cache_guard = new_cache;
    }

    pub fn synthesize_chime_pcm(freq: f32, instrument: InstrumentKind) -> Vec<f32> {
        let sample_rate = SAMPLE_RATE as f32;
        let duration = 0.85f32;
        let total_samples = (sample_rate * duration) as usize;
        let mut samples = Vec::with_capacity(total_samples * 2);

        let (mults, gains, decay_body_rate, decay_shimmer_rate, attack_sec) = instrument.params();
        let phase_offset = std::f32::consts::PI * 0.08;

        // 90Hz highpass filter coefficient (R = exp(-2*pi*90/44100)) to protect small handheld drivers
        let hp_r = 0.98726f32;
        let mut prev_x_l = 0.0f32;
        let mut prev_y_l = 0.0f32;
        let mut prev_x_r = 0.0f32;
        let mut prev_y_r = 0.0f32;

        for s in 0..total_samples {
            let t = s as f32 / sample_rate;
            let attack = (t / attack_sec).min(1.0);
            let decay_body = (-decay_body_rate * t).exp();
            let decay_shimmer = (-decay_shimmer_rate * t).exp();

            let mut sum_l = 0.0f32;
            let mut sum_r = 0.0f32;

            for (h, (&mult, &gain)) in mults.iter().zip(gains.iter()).enumerate() {
                let decay = if mult <= 2.0 {
                    decay_body
                } else {
                    decay_shimmer
                };
                let phase_l = if h == 2 { phase_offset } else { 0.0 };
                let phase_r = if h == 0 {
                    phase_offset * 0.5
                } else if h == 3 {
                    phase_offset
                } else {
                    0.0
                };

                let val = (2.0 * std::f32::consts::PI * (mult * freq) * t).sin() * gain * decay;
                sum_l += (val + phase_l.sin() * 0.1) * decay;
                sum_r += (val + phase_r.sin() * 0.1) * decay;
            }

            let raw_l = attack * sum_l * 0.45;
            let raw_r = attack * sum_r * 0.45;

            // Apply 90Hz rumble high-pass filter
            let hp_l = raw_l - prev_x_l + hp_r * prev_y_l;
            prev_x_l = raw_l;
            prev_y_l = hp_l;

            let hp_r_sample = raw_r - prev_x_r + hp_r * prev_y_r;
            prev_x_r = raw_r;
            prev_y_r = hp_r_sample;

            let left = hp_l.clamp(-1.0, 1.0);
            let right = hp_r_sample.clamp(-1.0, 1.0);
            samples.push(left);
            samples.push(right);
        }

        samples
    }

    pub fn play_chime_index(&self, index: usize, volume: Option<f32>) {
        let Some(sink) = &self.inner.device_sink else {
            return;
        };

        let idx = index % PENTATONIC_FREQUENCIES.len();
        let samples = {
            let cache_guard = match self.inner.pcm_cache.lock() {
                Ok(g) => g,
                Err(p) => p.into_inner(),
            };
            cache_guard[idx].clone()
        };
        let vol = volume
            .unwrap_or(MAX_PEDIATRIC_VOLUME)
            .clamp(0.0, MAX_PEDIATRIC_VOLUME);

        let channels = match NonZero::new(2) {
            Some(c) => c,
            None => return,
        };
        let sample_rate = match NonZero::new(SAMPLE_RATE) {
            Some(sr) => sr,
            None => return,
        };

        let source = SamplesBuffer::new(channels, sample_rate, samples);
        let player = Player::connect_new(sink.mixer());
        player.set_volume(vol);
        player.append(source);
        player.detach();
    }

    pub fn play_key(&self, key_text: &str) {
        let mut idx_lock = match self.inner.note_index.lock() {
            Ok(guard) => guard,
            Err(poisoned) => poisoned.into_inner(),
        };

        let idx = if key_text.is_empty() {
            *idx_lock % PENTATONIC_FREQUENCIES.len()
        } else {
            let first_char = key_text.chars().next().unwrap_or('A') as usize;
            (first_char + *idx_lock) % PENTATONIC_FREQUENCIES.len()
        };
        *idx_lock = (*idx_lock + 1) % PENTATONIC_FREQUENCIES.len();
        drop(idx_lock);

        self.play_chime_index(idx, None);
    }

    pub fn play_fanfare(&self) {
        let engine = self.clone();
        std::thread::spawn(move || {
            for idx in [5, 7, 8, 10] {
                engine.play_chime_index(idx, None);
                std::thread::sleep(std::time::Duration::from_millis(80));
            }
        });
    }

    pub fn play_startup(&self) {
        let engine = self.clone();
        std::thread::spawn(move || {
            for idx in [0, 3, 5] {
                engine.play_chime_index(idx, None);
                std::thread::sleep(std::time::Duration::from_millis(100));
            }
        });
    }

    pub fn play_bgm_drop(&self) {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::SystemTime::UNIX_EPOCH)
            .map_or(0, |d| d.subsec_nanos() as usize);
        let idx = now % PENTATONIC_FREQUENCIES.len();
        self.play_chime_index(idx, Some(0.12));
    }

    pub fn play_chord(&self, indices: &[usize], volume: Option<f32>) {
        if indices.is_empty() {
            return;
        }
        let voice_vol = volume
            .unwrap_or(MAX_PEDIATRIC_VOLUME)
            .clamp(0.0, MAX_PEDIATRIC_VOLUME)
            / (indices.len() as f32).sqrt();
        for &idx in indices {
            self.play_chime_index(idx, Some(voice_vol));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pentatonic_frequencies_count() {
        assert_eq!(PENTATONIC_FREQUENCIES.len(), 11);
    }

    #[test]
    fn test_synthesize_chime_pcm_length_and_stereo() {
        for kind in [
            InstrumentKind::Celesta,
            InstrumentKind::Marimba,
            InstrumentKind::Kalimba,
            InstrumentKind::MusicBox,
        ] {
            let samples = NativeAudioEngine::synthesize_chime_pcm(440.0, kind);
            let expected_frames = (SAMPLE_RATE as f32 * 0.85) as usize;
            assert_eq!(samples.len(), expected_frames * 2);

            // Assert all samples are within valid [-1.0, 1.0] range
            for &sample in &samples {
                assert!((-1.0..=1.0).contains(&sample));
            }
        }
    }

    #[test]
    fn test_native_audio_engine_methods_headless() {
        let engine = NativeAudioEngine::new();
        engine.set_instrument("kalimba");
        engine.set_instrument("marimba");
        engine.set_instrument("music_box");
        engine.set_instrument("celesta");
        engine.play_chime_index(0, Some(0.5));
        engine.play_key("A");
        engine.play_bgm_drop();
        engine.play_startup();
        engine.play_fanfare();
        engine.play_chord(&[0, 3, 5], Some(0.6));
        engine.play_chord(&[], None);
    }
}
