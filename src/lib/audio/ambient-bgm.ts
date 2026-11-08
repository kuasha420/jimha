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
  private highPassFilter: BiquadFilterNode | null = null;
  private droneOsc: OscillatorNode | null = null;
  private droneGain: GainNode | null = null;
  private recoveryTimer: ReturnType<typeof setTimeout> | null = null;
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
    if (this.isRunning) {
      this.startDrone();
    }
  }

  private initNodes(ctx: AudioContext): void {
    this.ctx = ctx;
    if (typeof ctx.createGain !== 'function') return;

    if (!this.filterNode && ctx.createBiquadFilter) {
      this.filterNode = ctx.createBiquadFilter();
      this.filterNode.type = 'lowpass';
      this.filterNode.frequency.setValueAtTime(2500, ctx.currentTime);
    }

    if (!this.masterGain) {
      this.masterGain = ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.14, ctx.currentTime);
    }

    if (!this.highPassFilter && ctx.createBiquadFilter) {
      this.highPassFilter = ctx.createBiquadFilter();
      this.highPassFilter.type = 'highpass';
      this.highPassFilter.frequency.setValueAtTime(90, ctx.currentTime);
      this.highPassFilter.Q?.setValueAtTime(0.707, ctx.currentTime);
    }

    this.connectGraph(ctx);
  }

  private connectGraph(ctx: AudioContext): void {
    if (!this.filterNode || !this.masterGain) return;
    try {
      this.filterNode.connect(this.masterGain);
      if (this.highPassFilter) {
        this.masterGain.connect(this.highPassFilter);
        this.highPassFilter.connect(ctx.destination);
      } else {
        this.masterGain.connect(ctx.destination);
      }
    } catch (err) {
      console.warn('[AmbientBgmEngine] Failed to connect audio graph nodes:', err);
    }
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.startDrone();
    this.sequencer.start();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.recoveryTimer) {
      clearTimeout(this.recoveryTimer);
      this.recoveryTimer = null;
    }
    this.stopDrone();
    this.sequencer.stop();
  }

  private startDrone(): void {
    if (!this.ctx || !this.filterNode || this.droneOsc) return;
    if (typeof this.ctx.createOscillator !== 'function') return;

    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(130.81, this.ctx.currentTime); // C3 pedal drone
      gain.gain.setValueAtTime(0.018, this.ctx.currentTime);
      osc.connect(gain);
      gain.connect(this.filterNode);
      osc.start();
      this.droneOsc = osc;
      this.droneGain = gain;
    } catch (err) {
      console.debug('[AmbientBgmEngine] Failed to initialize drone oscillator:', err);
    }
  }

  private stopDrone(): void {
    if (this.droneOsc) {
      try {
        this.droneOsc.stop();
        this.droneOsc.disconnect();
      } catch {
        // ignore
      }
      this.droneOsc = null;
    }
    if (this.droneGain) {
      try {
        this.droneGain.disconnect();
      } catch {
        // ignore
      }
      this.droneGain = null;
    }
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
    if (this.recoveryTimer) {
      clearTimeout(this.recoveryTimer);
      this.recoveryTimer = null;
    }

    if (this.mode !== 'ui') {
      this.setMode('playing');
      this.recoveryTimer = setTimeout(() => {
        if (this.mode === 'playing') {
          this.setMode('idle');
        }
      }, 3500);
    }

    this.sequencer.notifyInput();
  }

  private applyModeParameters(): void {
    if (!this.ctx || !this.filterNode || !this.masterGain) return;
    const now = this.ctx.currentTime;
    let targetCutoff = 2500;
    let targetGain = 0.14;

    if (this.mode === 'playing') {
      targetCutoff = 450;
      targetGain = 0.05;
    } else if (this.mode === 'ui') {
      targetCutoff = 600;
      targetGain = 0.06;
    }

    const timeConstant = this.mode === 'playing' ? 0.2 : 1.5;

    try {
      if (typeof this.filterNode.frequency.setTargetAtTime === 'function') {
        this.filterNode.frequency.setTargetAtTime(targetCutoff, now, timeConstant);
      } else {
        this.filterNode.frequency.setValueAtTime(targetCutoff, now);
      }

      if (typeof this.masterGain.gain.setTargetAtTime === 'function') {
        this.masterGain.gain.setTargetAtTime(targetGain, now, timeConstant);
      } else {
        this.masterGain.gain.setValueAtTime(targetGain, now);
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
