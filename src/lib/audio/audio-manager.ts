import { PENTATONIC_FREQUENCIES, getFrequencyForKey, type FrequencySelection } from './frequencies';
import { synthesizeChimeSamples } from './synth-dsp';
import { type InstrumentId } from '../content/instruments';
import { AmbientBgmEngine, type BgmMode } from './ambient-bgm';

let cachedInvoke: ((cmd: string, args?: Record<string, unknown>) => Promise<unknown>) | null = null;

function invokeNativeAudio(keyText: string): void {
  if (typeof window === 'undefined' || !('__TAURI_INTERNALS__' in window)) return;
  if (cachedInvoke) {
    cachedInvoke('audio_play_key', { key: keyText }).catch(() => {});
  } else {
    import('@tauri-apps/api/core')
      .then(({ invoke }) => {
        cachedInvoke = invoke;
        invoke('audio_play_key', { key: keyText }).catch(() => {});
      })
      .catch(() => {});
  }
}

export class JimhaAudioManager {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private bufferCache: Map<number, AudioBuffer> = new Map();
  private noteIndex: number = 0;
  private instrument: InstrumentId = 'celesta';
  private unlockPromise: Promise<boolean> | null = null;
  private ambientBgm: AmbientBgmEngine = new AmbientBgmEngine();

  constructor() {
    // Lazily initialized on first interaction or explicitly via unlock()
  }

  public unlock(): Promise<boolean> {
    if (this.unlockPromise) {
      return this.unlockPromise;
    }
    this.unlockPromise = this.doUnlock().finally(() => {
      this.unlockPromise = null;
    });
    return this.unlockPromise;
  }

  private async doUnlock(): Promise<boolean> {
    if (typeof window === 'undefined') return false;

    try {
      if (!this.ctx) {
        const AudioCtxClass =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (!AudioCtxClass) return false;
        this.ctx = new AudioCtxClass();
      }

      if (!this.masterGain && this.ctx.createGain) {
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.setValueAtTime(0.8, this.ctx.currentTime);
        this.masterGain.connect(this.ctx.destination);
      }

      if (this.ctx.state === 'suspended') {
        await this.ctx.resume();
      }

      this.ensureBufferCache();
      this.ambientBgm.setContext(this.ctx);
      this.ambientBgm.start();
      return true;
    } catch (err) {
      console.debug('[JimhaAudio] unlock failed:', err);
      return false;
    }
  }

  public setInstrument(instrument: InstrumentId): void {
    if (this.instrument === instrument) return;
    this.instrument = instrument;
    this.bufferCache.clear();
    this.ensureBufferCache();
  }

  public getInstrument(): InstrumentId {
    return this.instrument;
  }

  public ensureBufferCache(): void {
    if (!this.ctx) return;

    const sr = this.ctx.sampleRate || 44100;
    for (const freq of PENTATONIC_FREQUENCIES) {
      if (!this.bufferCache.has(freq)) {
        const synth = synthesizeChimeSamples(freq, sr, 0.85, this.instrument);
        const buffer = this.ctx.createBuffer(2, synth.left.length, sr);
        buffer.getChannelData(0).set(synth.left);
        buffer.getChannelData(1).set(synth.right);
        this.bufferCache.set(freq, buffer);
      }
    }
  }

  public playKey(keyText: string = ''): FrequencySelection {
    const selection = getFrequencyForKey(keyText, this.noteIndex);
    this.noteIndex = (this.noteIndex + 1) % PENTATONIC_FREQUENCIES.length;

    // Duck ambient background music when active key input occurs
    this.ambientBgm.notifyInput();

    // 1. Native PipeWire stream via Tauri (0ms latency, bypasses browser sandbox)
    invokeNativeAudio(keyText);

    // 2. In-browser Web Audio pre-cached buffer playback
    this.playFrequency(selection.frequency);

    return selection;
  }

  public playFrequency(frequency: number): void {
    if (!this.ctx) {
      this.unlock()
        .then(() => this.dispatchAudio(frequency))
        .catch((err) => {
          console.debug('[JimhaAudio] lazy unlock failed:', err);
        });
      return;
    }

    if (this.ctx.state === 'suspended') {
      this.ctx
        .resume()
        .then(() => this.dispatchAudio(frequency))
        .catch((err) => {
          console.debug('[JimhaAudio] resume failed:', err);
        });
      return;
    }

    this.dispatchAudio(frequency);
  }

  private dispatchAudio(frequency: number): void {
    if (!this.ctx) return;
    this.playBuffer(frequency);
  }

  private playBuffer(frequency: number): void {
    if (!this.ctx) return;

    let buffer = this.bufferCache.get(frequency);
    if (!buffer) {
      const sr = this.ctx.sampleRate || 44100;
      const synth = synthesizeChimeSamples(frequency, sr, 0.85, this.instrument);
      buffer = this.ctx.createBuffer(2, synth.left.length, sr);
      buffer.getChannelData(0).set(synth.left);
      buffer.getChannelData(1).set(synth.right);
      this.bufferCache.set(frequency, buffer);
    }

    try {
      const source = this.ctx.createBufferSource();
      source.buffer = buffer;
      if (this.masterGain) {
        source.connect(this.masterGain);
      } else {
        source.connect(this.ctx.destination);
      }
      source.start();
    } catch (err) {
      console.debug('[JimhaAudio] buffer source playback failed:', err);
    }
  }

  public setAudioMode(mode: BgmMode): void {
    this.ambientBgm.setMode(mode);
  }

  public playStartupChime(): void {
    const chord = [261.63, 392.0, 523.25];
    chord.forEach((freq, idx) => {
      setTimeout(() => {
        this.playFrequency(freq);
      }, idx * 100);
    });
  }

  public playCelebrationFanfare(): void {
    const fanfare = [523.25, 659.25, 783.99, 1046.5];
    fanfare.forEach((freq, idx) => {
      setTimeout(() => {
        this.playFrequency(freq);
      }, idx * 80);
    });
  }

  public playStickerTapSound(index: number = 0): void {
    const highPentatonic = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5];
    const freq = highPentatonic[index % highPentatonic.length] ?? 523.25;
    this.playFrequency(freq);
  }

  public async close(): Promise<void> {
    this.ambientBgm.stop();
    if (this.masterGain) {
      try {
        this.masterGain.disconnect();
      } catch (_) {}
      this.masterGain = null;
    }
    if (this.ctx) {
      await this.ctx.close();
      this.ctx = null;
    }
    this.bufferCache.clear();
  }
}
