import { PENTATONIC_FREQUENCIES } from './frequencies';
import { invokeNativeAudioCommand } from './audio-manager';
import type { BgmMode } from './ambient-bgm';

export interface MelodicStep {
  lead: number | null; // index 0..10 or null for rest
  bass: number | null; // index 0..10 or null for rest
}

export interface MelodicTrack {
  id: string;
  name: string;
  timeSignature: string;
  stepIntervalMs: number;
  steps: MelodicStep[];
}

export const STARLIGHT_LULLABY: MelodicTrack = {
  id: 'starlight_lullaby',
  name: 'Starlight Lullaby ✨',
  timeSignature: '4/4',
  stepIntervalMs: 260,
  steps: [
    { lead: 5, bass: 0 },
    { lead: 7, bass: null },
    { lead: 8, bass: null },
    { lead: 7, bass: null },
    { lead: 10, bass: 3 },
    { lead: 8, bass: null },
    { lead: 7, bass: null },
    { lead: 5, bass: null },
    { lead: 6, bass: 0 },
    { lead: 7, bass: null },
    { lead: 5, bass: null },
    { lead: 3, bass: null },
    { lead: 4, bass: 3 },
    { lead: 5, bass: null },
    { lead: 2, bass: null },
    { lead: 0, bass: null },
  ],
};

export const CELESTIAL_CAROUSEL: MelodicTrack = {
  id: 'celestial_carousel',
  name: 'Celestial Carousel 🎠',
  timeSignature: '3/4',
  stepIntervalMs: 240,
  steps: [
    { lead: 5, bass: 0 },
    { lead: 7, bass: null },
    { lead: 8, bass: null },
    { lead: 10, bass: 3 },
    { lead: 8, bass: null },
    { lead: 7, bass: null },
    { lead: 9, bass: 4 },
    { lead: 8, bass: null },
    { lead: 5, bass: null },
    { lead: 7, bass: 0 },
    { lead: 6, bass: null },
    { lead: 5, bass: null },
  ],
};

export const JIMHA_WONDER: MelodicTrack = {
  id: 'jimha_wonder',
  name: "Jimha's Wonder 💖",
  timeSignature: '4/4',
  stepIntervalMs: 220,
  steps: [
    { lead: 5, bass: 0 },
    { lead: null, bass: null },
    { lead: 6, bass: null },
    { lead: 7, bass: null },
    { lead: 8, bass: 3 },
    { lead: 7, bass: null },
    { lead: 8, bass: null },
    { lead: 10, bass: null },
    { lead: 9, bass: 4 },
    { lead: 8, bass: null },
    { lead: 7, bass: null },
    { lead: 5, bass: null },
    { lead: 6, bass: 3 },
    { lead: 5, bass: null },
    { lead: 3, bass: null },
    { lead: 5, bass: 0 },
  ],
};

export const ALL_THEMES: MelodicTrack[] = [STARLIGHT_LULLABY, CELESTIAL_CAROUSEL, JIMHA_WONDER];

export interface SequencerAudioSink {
  playWebNote: (frequency: number, volume: number) => void;
}

export class MelodySequencer {
  private currentTrack: MelodicTrack = STARLIGHT_LULLABY;
  private currentStepIndex: number = 0;
  private isRunning: boolean = false;
  private stepTimer: ReturnType<typeof setTimeout> | null = null;
  private lastInputTimestamp: number = 0;
  private mode: BgmMode = 'idle';
  private sink: SequencerAudioSink | null = null;

  constructor(sink?: SequencerAudioSink) {
    if (sink) {
      this.sink = sink;
    }
  }

  public setSink(sink: SequencerAudioSink): void {
    this.sink = sink;
  }

  public setTrack(track: MelodicTrack): void {
    this.currentTrack = track;
    this.currentStepIndex = 0;
  }

  public getTrack(): MelodicTrack {
    return this.currentTrack;
  }

  public setMode(mode: BgmMode): void {
    this.mode = mode;
  }

  public getMode(): BgmMode {
    return this.mode;
  }

  public notifyInput(): void {
    this.lastInputTimestamp = Date.now();
  }

  public calculateVolume(isBass: boolean): number {
    const elapsed = Date.now() - this.lastInputTimestamp;
    const isDucked = elapsed < 3500;

    if (this.mode === 'ui') {
      return isBass ? 0.04 : 0.02;
    }

    if (isDucked) {
      return isBass ? 0.05 : 0.03;
    }

    return isBass ? 0.08 : 0.12;
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.scheduleNextStep();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.stepTimer) {
      clearTimeout(this.stepTimer);
      this.stepTimer = null;
    }
  }

  public getCurrentStep(): number {
    return this.currentStepIndex;
  }

  public advanceStep(): void {
    if (this.currentTrack.steps.length === 0) return;

    const step = this.currentTrack.steps[this.currentStepIndex];
    if (step) {
      this.dispatchStep(step);
    }

    this.currentStepIndex = (this.currentStepIndex + 1) % this.currentTrack.steps.length;
  }

  private dispatchStep(step: MelodicStep): void {
    if (step.lead !== null) {
      const leadVol = this.calculateVolume(false);
      this.emitNote(step.lead, leadVol);
    }

    if (step.bass !== null) {
      const bassVol = this.calculateVolume(true);
      this.emitNote(step.bass, bassVol);
    }
  }

  private emitNote(index: number, volume: number): void {
    // 1. Native PipeWire Audio Dispatch
    invokeNativeAudioCommand('audio_play_chime_index', { index, volume });

    // 2. Web Audio Fallback Dispatch
    if (this.sink) {
      const freq = PENTATONIC_FREQUENCIES[index % PENTATONIC_FREQUENCIES.length] ?? 261.63;
      this.sink.playWebNote(freq, volume);
    }
  }

  private scheduleNextStep(): void {
    if (!this.isRunning) return;

    const interval = this.currentTrack.stepIntervalMs;
    this.stepTimer = setTimeout(() => {
      if (!this.isRunning) return;
      this.advanceStep();
      this.scheduleNextStep();
    }, interval);
  }
}
