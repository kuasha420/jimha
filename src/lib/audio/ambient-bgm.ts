import { MelodySequencer, type MelodicTrack } from './melody-sequencer';

export type BgmMode = 'idle' | 'playing' | 'ui';

/**
 * AmbientBgmEngine: Web Audio ambient music-box engine integrating MelodySequencer.
 * Drives dynamic melodic themes with pedal bass and interactive ducking.
 */
export class AmbientBgmEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private filterNode: BiquadFilterNode | null = null;
  private mode: BgmMode = 'idle';
  private isRunning: boolean = false;
  private sequencer: MelodySequencer;

  constructor(ctx?: AudioContext | null) {
    this.sequencer = new MelodySequencer({
      playWebNote: (frequency: number, volume: number) => {
        this.playWebNote(frequency, volume);
      },
    });

    if (ctx) {
      this.initNodes(ctx);
    }
  }

  public setContext(ctx: AudioContext): void {
    if (this.ctx === ctx && this.masterGain) return;
    this.ctx = ctx;
    this.initNodes(ctx);
  }

  private initNodes(ctx: AudioContext): void {
    this.ctx = ctx;
    if (typeof ctx.createGain !== 'function') return;

    if (!this.filterNode && ctx.createBiquadFilter) {
      this.filterNode = ctx.createBiquadFilter();
      this.filterNode.type = 'lowpass';
      this.filterNode.frequency.setValueAtTime(3000, ctx.currentTime);
    }

    if (!this.masterGain && ctx.createGain) {
      this.masterGain = ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.15, ctx.currentTime);
    }

    if (this.filterNode && this.masterGain) {
      try {
        this.filterNode.connect(this.masterGain);
        this.masterGain.connect(ctx.destination);
      } catch (err) {
        console.warn('[AmbientBgmEngine] Failed to connect audio graph nodes:', err);
      }
    }
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.sequencer.start();
  }

  public stop(): void {
    this.isRunning = false;
    this.sequencer.stop();
  }

  public setTrack(track: MelodicTrack): void {
    this.sequencer.setTrack(track);
  }

  public getTrack(): MelodicTrack {
    return this.sequencer.getTrack();
  }

  public setMode(mode: BgmMode): void {
    this.mode = mode;
    this.sequencer.setMode(mode);
    this.applyModeParameters();
  }

  public getMode(): BgmMode {
    return this.mode;
  }

  public notifyInput(): void {
    if (this.mode === 'idle') {
      this.setMode('playing');
    }
    this.sequencer.notifyInput();
  }

  private applyModeParameters(): void {
    if (!this.ctx || !this.filterNode) return;
    const now = this.ctx.currentTime;
    let targetCutoff = 3000;
    if (this.mode === 'playing') {
      targetCutoff = 650;
    } else if (this.mode === 'ui') {
      targetCutoff = 750;
    }

    try {
      if (typeof this.filterNode.frequency.setTargetAtTime === 'function') {
        this.filterNode.frequency.setTargetAtTime(targetCutoff, now, 0.3);
      } else {
        this.filterNode.frequency.setValueAtTime(targetCutoff, now);
      }
    } catch (err) {
      console.warn('[AmbientBgmEngine] Failed to schedule audio parameter transition:', err);
    }
  }

  private playWebNote(freq: number, volume: number): void {
    if (!this.ctx || !this.filterNode) return;
    if (this.ctx.state === 'suspended') return;

    try {
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const noteGain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now);

      noteGain.gain.setValueAtTime(0.0001, now);
      noteGain.gain.linearRampToValueAtTime(volume, now + 0.04);
      noteGain.gain.exponentialRampToValueAtTime(0.0001, now + 1.8);

      osc.connect(noteGain);
      noteGain.connect(this.filterNode);

      osc.start(now);
      osc.stop(now + 1.9);
    } catch (err) {
      console.warn('[AmbientBgmEngine] Failed to trigger ambient note:', err);
    }
  }
}
