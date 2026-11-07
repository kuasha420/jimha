import { PENTATONIC_FREQUENCIES } from './frequencies';

export type BgmMode = 'idle' | 'playing' | 'ui';

/**
 * AmbientBgmEngine: Zero-dependency Web Audio ambient generative music box engine.
 * Generates gentle, calming pentatonic chime drops and dynamically adapts/ducks
 * based on toddler activity and modal state.
 */
export class AmbientBgmEngine {
  private ctx: AudioContext | null = null;
  private masterGain: GainNode | null = null;
  private filterNode: BiquadFilterNode | null = null;
  private mode: BgmMode = 'idle';
  private isRunning: boolean = false;
  private dropTimer: ReturnType<typeof setTimeout> | null = null;
  private idleRestoreTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(ctx?: AudioContext | null) {
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
      this.filterNode.frequency.setValueAtTime(3200, ctx.currentTime);
    }

    if (!this.masterGain && ctx.createGain) {
      this.masterGain = ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.15, ctx.currentTime);
    }

    if (this.filterNode && this.masterGain) {
      try {
        this.filterNode.connect(this.masterGain);
        this.masterGain.connect(ctx.destination);
      } catch (_) {}
    }
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.scheduleNextDrop();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.dropTimer) {
      clearTimeout(this.dropTimer);
      this.dropTimer = null;
    }
    if (this.idleRestoreTimer) {
      clearTimeout(this.idleRestoreTimer);
      this.idleRestoreTimer = null;
    }
  }

  public setMode(mode: BgmMode): void {
    this.mode = mode;
    this.applyModeParameters();
  }

  public getMode(): BgmMode {
    return this.mode;
  }

  public notifyInput(): void {
    if (!this.isRunning) return;
    if (this.mode === 'ui') return; // In UI modal mode, preserve lowpass profile

    if (this.mode !== 'playing') {
      this.setMode('playing');
    }

    if (this.idleRestoreTimer) {
      clearTimeout(this.idleRestoreTimer);
    }

    this.idleRestoreTimer = setTimeout(() => {
      if (this.isRunning && this.mode === 'playing') {
        this.setMode('idle');
      }
    }, 5000);
  }

  private applyModeParameters(): void {
    if (!this.ctx || !this.masterGain) return;
    const now = this.ctx.currentTime;

    let targetGain = 0.15;
    let targetCutoff = 3500;

    if (this.mode === 'playing') {
      targetGain = 0.05; // Duck to 0.05 during active key smashing
      targetCutoff = 3200;
    } else if (this.mode === 'ui') {
      targetGain = 0.10; // Warm lowpass ambient tone
      targetCutoff = 750;
    } else {
      targetGain = 0.15; // Idle ambient chime drops
      targetCutoff = 3500;
    }

    try {
      if (typeof this.masterGain.gain.setTargetAtTime === 'function') {
        this.masterGain.gain.setTargetAtTime(targetGain, now, 0.25);
      } else {
        this.masterGain.gain.setValueAtTime(targetGain, now);
      }

      if (this.filterNode) {
        if (typeof this.filterNode.frequency.setTargetAtTime === 'function') {
          this.filterNode.frequency.setTargetAtTime(targetCutoff, now, 0.25);
        } else {
          this.filterNode.frequency.setValueAtTime(targetCutoff, now);
        }
      }
    } catch (_) {}
  }

  private scheduleNextDrop(): void {
    if (!this.isRunning) return;

    const delay = 4000 + Math.random() * 2000; // 4.0 - 6.0s
    this.dropTimer = setTimeout(() => {
      if (!this.isRunning) return;
      this.triggerAmbientDrop();
      this.scheduleNextDrop();
    }, delay);
  }

  private triggerAmbientDrop(): void {
    if (!this.ctx || !this.filterNode) return;
    if (this.ctx.state === 'suspended') return;

    try {
      // Pick random pentatonic frequency from C4 to C6
      const freq = PENTATONIC_FREQUENCIES[Math.floor(Math.random() * PENTATONIC_FREQUENCIES.length)];
      const now = this.ctx.currentTime;

      const osc = this.ctx.createOscillator();
      const noteGain = this.ctx.createGain();

      osc.type = Math.random() > 0.4 ? 'sine' : 'triangle';
      osc.frequency.setValueAtTime(freq, now);

      noteGain.gain.setValueAtTime(0.0001, now);
      noteGain.gain.linearRampToValueAtTime(0.35, now + 0.04);
      noteGain.gain.exponentialRampToValueAtTime(0.0001, now + 2.2);

      osc.connect(noteGain);
      noteGain.connect(this.filterNode);

      osc.start(now);
      osc.stop(now + 2.3);
    } catch (_) {}
  }
}
