use std::fs;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};

const PENTATONIC_FREQUENCIES: [f32; 11] = [
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

#[derive(Debug)]
struct AudioEngineInner {
    cache_dir: PathBuf,
    proc_pool: Mutex<Vec<Child>>,
    note_index: Mutex<usize>,
    player_bin: Option<PathBuf>,
}

#[derive(Debug, Clone)]
pub struct NativeAudioEngine {
    inner: Arc<AudioEngineInner>,
}

fn resolve_cache_dir() -> PathBuf {
    if let Ok(xdg) = std::env::var("XDG_CACHE_HOME") {
        if !xdg.is_empty() {
            return PathBuf::from(xdg).join("jimha").join("audio_cache_v2");
        }
    }
    if let Ok(home) = std::env::var("HOME") {
        return PathBuf::from(home)
            .join(".cache")
            .join("jimha")
            .join("audio_cache_v2");
    }
    PathBuf::from("/tmp").join("jimha").join("audio_cache_v2")
}

impl Default for NativeAudioEngine {
    fn default() -> Self {
        Self::new()
    }
}

impl NativeAudioEngine {
    pub fn new() -> Self {
        let cache_dir = resolve_cache_dir();
        let _ = fs::create_dir_all(&cache_dir);

        let player =
            crate::kiosk::find_binary("pw-play").or_else(|| crate::kiosk::find_binary("paplay"));

        let inner = AudioEngineInner {
            cache_dir,
            proc_pool: Mutex::new(Vec::new()),
            note_index: Mutex::new(0),
            player_bin: player,
        };

        let engine = Self {
            inner: Arc::new(inner),
        };

        // Pre-warm chime WAV files in cache directory
        engine.ensure_chime_cache();
        engine
    }

    fn ensure_chime_cache(&self) {
        for (i, &freq) in PENTATONIC_FREQUENCIES.iter().enumerate() {
            let wav_path = self
                .inner
                .cache_dir
                .join(format!("chime_{}_{}.wav", i, freq as u32));
            if !wav_path.exists() {
                Self::write_chime_wav(&wav_path, freq);
            }
        }
    }

    fn write_chime_wav(path: &PathBuf, freq: f32) {
        let sample_rate = 44100u32;
        let duration = 0.85f32;
        let total_samples = (sample_rate as f32 * duration) as usize;
        let mut samples_i16 = Vec::with_capacity(total_samples * 2);

        let mults = [1.0f32, 2.0, 3.0, 4.2, 5.4];
        let gains = [1.0f32, 0.35, 0.18, 0.10, 0.05];
        let phase_offset = std::f32::consts::PI * 0.08;

        for s in 0..total_samples {
            let t = s as f32 / sample_rate as f32;
            let attack = (t / 0.004).min(1.0);
            let decay_body = (-2.5 * t).exp();
            let decay_shimmer = (-5.5 * t).exp();

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

            let left = (attack * sum_l * 0.45 * 32767.0).clamp(-32768.0, 32767.0) as i16;
            let right = (attack * sum_r * 0.45 * 32767.0).clamp(-32768.0, 32767.0) as i16;
            samples_i16.push(left);
            samples_i16.push(right);
        }

        // Standard 44-byte Stereo 16-bit PCM WAV header
        let byte_rate: u32 = sample_rate * 4;
        let block_align: u16 = 4;
        let data_size: u32 = (samples_i16.len() * 2) as u32;
        let file_size: u32 = 36 + data_size;

        let mut header = Vec::with_capacity(44);
        header.extend_from_slice(b"RIFF");
        header.extend_from_slice(&file_size.to_le_bytes());
        header.extend_from_slice(b"WAVEfmt ");
        header.extend_from_slice(&16u32.to_le_bytes()); // Subchunk1Size (16 for PCM)
        header.extend_from_slice(&1u16.to_le_bytes()); // AudioFormat (1 = PCM)
        header.extend_from_slice(&2u16.to_le_bytes()); // NumChannels (2)
        header.extend_from_slice(&sample_rate.to_le_bytes());
        header.extend_from_slice(&byte_rate.to_le_bytes());
        header.extend_from_slice(&block_align.to_le_bytes());
        header.extend_from_slice(&16u16.to_le_bytes()); // BitsPerSample
        header.extend_from_slice(b"data");
        header.extend_from_slice(&data_size.to_le_bytes());

        let mut file_bytes = header;
        for sample in samples_i16 {
            file_bytes.extend_from_slice(&sample.to_le_bytes());
        }
        let _ = fs::write(path, file_bytes);
    }

    pub fn play_chime_index(&self, index: usize, volume: Option<f32>) {
        let player = match &self.inner.player_bin {
            Some(p) => p,
            None => return,
        };

        let idx = index % PENTATONIC_FREQUENCIES.len();
        let freq = PENTATONIC_FREQUENCIES[idx];
        let wav_path = self
            .inner
            .cache_dir
            .join(format!("chime_{}_{}.wav", idx, freq as u32));
        if !wav_path.exists() {
            Self::write_chime_wav(&wav_path, freq);
        }

        let Some(wav_str) = wav_path.to_str() else {
            return;
        };

        let vol = volume.unwrap_or(0.8).clamp(0.0, 1.0);

        // Clean dead processes in pool and enforce voice stealing (max 4 concurrent voices)
        if let Ok(mut pool) = self.inner.proc_pool.lock() {
            pool.retain_mut(|p| p.try_wait().is_ok_and(|s| s.is_none()));
            while pool.len() >= 4 {
                if let Some(mut oldest) = pool.drain(..1).next() {
                    let _ = oldest.kill();
                }
            }

            let is_pw = player.to_string_lossy().contains("pw-play");
            let mut cmd = Command::new(player);
            if is_pw {
                let vol_arg = format!("--volume={vol:.2}");
                cmd.args(["--media-role=Game", &vol_arg, wav_str]);
            } else {
                cmd.args(["--media-role=Game", wav_str]);
            }
            if let Ok(child) = cmd
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn()
            {
                pool.push(child);
            }
        }
    }

    pub fn play_key(&self, key_text: &str) {
        let mut idx_lock = self
            .inner
            .note_index
            .lock()
            .expect("fatal invariant: note_index mutex poisoned");
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
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolve_cache_dir() {
        let dir = resolve_cache_dir();
        assert!(dir.to_string_lossy().contains("audio_cache_v2"));
    }

    #[test]
    fn test_write_chime_wav_valid_riff_header() {
        let temp_dir = std::env::temp_dir();
        let test_path = temp_dir.join(format!("test_chime_{}.wav", std::process::id()));
        NativeAudioEngine::write_chime_wav(&test_path, 440.0);

        assert!(test_path.exists());
        let bytes = std::fs::read(&test_path).expect("read test wav");
        assert!(bytes.len() >= 44);

        assert_eq!(&bytes[0..4], b"RIFF");
        assert_eq!(&bytes[8..12], b"WAVE");
        assert_eq!(&bytes[12..16], b"fmt ");

        let audio_format = u16::from_le_bytes(bytes[20..22].try_into().unwrap());
        assert_eq!(audio_format, 1);

        let channels = u16::from_le_bytes(bytes[22..24].try_into().unwrap());
        assert_eq!(channels, 2);

        let sample_rate = u32::from_le_bytes(bytes[24..28].try_into().unwrap());
        assert_eq!(sample_rate, 44100);

        let bits_per_sample = u16::from_le_bytes(bytes[34..36].try_into().unwrap());
        assert_eq!(bits_per_sample, 16);

        assert_eq!(&bytes[36..40], b"data");

        let _ = std::fs::remove_file(test_path);
    }

    #[test]
    fn test_native_audio_engine_methods() {
        let engine = NativeAudioEngine::new();
        engine.play_chime_index(0, Some(0.5));
        engine.play_key("A");
        engine.play_bgm_drop();
        engine.play_startup();
        engine.play_fanfare();
    }
}
