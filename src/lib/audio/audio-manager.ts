import { PENTATONIC_FREQUENCIES, getFrequencyForKey, type FrequencySelection } from './frequencies';
import { synthesizeChimeSamples } from './synth-dsp';
import { CHIME_WORKLET_PROCESSOR_CODE } from './chime-worklet';
import { getInstrumentConfig, type InstrumentId } from '../content/instruments';

export class JimhaAudioManager {
  private ctx: AudioContext | null = null;
  private workletNode: AudioWorkletNode | null = null;
  private bufferCache: Map<number, AudioBuffer> = new Map();
  private noteIndex: number = 0;
  private isUnlocked: boolean = false;
  private workletLoaded: boolean = false;
  private instrument: InstrumentId = 'celesta';
  private unlockPromise: Promise<boolean> | null = null;

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
        const AudioCtxClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (!AudioCtxClass) return false;
        this.ctx = new AudioCtxClass();
      }

      if (this.ctx.state === 'suspended') {
        await this.ctx.resume();
      }

      this.isUnlocked = true;

      // Always pre-warm fallback AudioBuffers first so sound is available immediately
      this.ensureBufferCache();

      if (!this.workletLoaded && this.ctx.audioWorklet) {
        await this.loadWorklet();
      }

      return true;
    } catch (err) {
      console.debug('[JimhaAudio] unlock failed:', err);
      return false;
    }
  }

  private async loadWorklet(): Promise<void> {
    if (!this.ctx || !this.ctx.audioWorklet) return;

    try {
      const blob = new Blob([CHIME_WORKLET_PROCESSOR_CODE], { type: 'application/javascript' });
      const workletUrl = URL.createObjectURL(blob);
      await this.ctx.audioWorklet.addModule(workletUrl);
      URL.revokeObjectURL(workletUrl);

      const node = new AudioWorkletNode(this.ctx, 'jimha-chime-processor', {
        numberOfInputs: 0,
        numberOfOutputs: 1,
        outputChannelCount: [2]
      });

      node.onprocessorerror = (err) => {
        console.warn('[JimhaAudio] worklet processor error, falling back to AudioBuffer:', err);
        this.workletLoaded = false;
        if (this.workletNode) {
          try {
            this.workletNode.disconnect();
          } catch (_) {}
          this.workletNode = null;
        }
      };

      node.connect(this.ctx.destination);
      this.workletNode = node;
      this.workletLoaded = true;
    } catch (err) {
      console.debug('[JimhaAudio] loadWorklet failed, using buffer fallback:', err);
      this.workletLoaded = false;
      this.workletNode = null;
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

    // Trigger audio playback
    this.playFrequency(selection.frequency);

    return selection;
  }

  public playFrequency(frequency: number): void {
    if (!this.ctx) {
      // Fire-and-forget lazy unlock
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

    // 1. Dedicated AudioWorklet synthesis pathway (high priority)
    if (this.workletLoaded && this.workletNode) {
      try {
        const config = getInstrumentConfig(this.instrument);
        this.workletNode.port.postMessage({
          type: 'trigger',
          frequency,
          instrument: this.instrument,
          sampleRate: this.ctx.sampleRate || 44100,
          multipliers: config.harmonicMultipliers,
          gains: config.harmonicGains,
          decayBodyRate: config.decayBodyRate,
          decayShimmerRate: config.decayShimmerRate,
          attackSeconds: config.attackSeconds,
        });
        return;
      } catch (err) {
        console.warn('[JimhaAudio] worklet postMessage failed, falling back to AudioBuffer:', err);
        this.workletLoaded = false;
        this.workletNode = null;
      }
    }

    // 2. High-performance pre-warmed AudioBuffer fallback pathway (bulletproof guarantee)
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
      source.connect(this.ctx.destination);
      source.start();
    } catch (err) {
      console.debug('[JimhaAudio] buffer source playback failed:', err);
    }
  }

  public async close(): Promise<void> {
    if (this.workletNode) {
      this.workletNode.disconnect();
      this.workletNode = null;
    }
    if (this.ctx) {
      await this.ctx.close();
      this.ctx = null;
    }
    this.bufferCache.clear();
    this.isUnlocked = false;
    this.workletLoaded = false;
  }
}
