import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  MelodySequencer,
  STARLIGHT_LULLABY,
  CELESTIAL_CAROUSEL,
  JIMHA_WONDER,
  ALL_THEMES,
  type MelodicTrack,
} from './melody-sequencer';
import { PENTATONIC_FREQUENCIES } from './frequencies';

describe('MelodySequencer Unit & Contract Suite', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('initializes with default track and allows switching tracks', () => {
    const sequencer = new MelodySequencer();
    expect(sequencer.getTrack().id).toBe(STARLIGHT_LULLABY.id);
    expect(sequencer.getCurrentStep()).toBe(0);

    sequencer.setTrack(CELESTIAL_CAROUSEL);
    expect(sequencer.getTrack().id).toBe(CELESTIAL_CAROUSEL.id);
    expect(sequencer.getCurrentStep()).toBe(0);

    sequencer.setTrack(JIMHA_WONDER);
    expect(sequencer.getTrack().id).toBe(JIMHA_WONDER.id);
    expect(ALL_THEMES).toHaveLength(3);
  });

  it('advances steps sequentially and loops at the track boundary', () => {
    const customTrack: MelodicTrack = {
      id: 'test_loop',
      name: 'Test Loop',
      timeSignature: '4/4',
      stepIntervalMs: 100,
      steps: [
        { lead: 0, bass: null },
        { lead: 1, bass: null },
        { lead: 2, bass: null },
      ],
    };

    const sequencer = new MelodySequencer();
    sequencer.setTrack(customTrack);

    expect(sequencer.getCurrentStep()).toBe(0);
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(1);
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(2);
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(0);
  });

  it('dispatches notes to audio sink and skips rest steps cleanly', () => {
    const playWebNote = vi.fn();
    const sequencer = new MelodySequencer({ playWebNote });

    const trackWithRests: MelodicTrack = {
      id: 'test_rests',
      name: 'Test Rests',
      timeSignature: '4/4',
      stepIntervalMs: 100,
      steps: [
        { lead: 5, bass: null }, // lead only
        { lead: null, bass: 0 }, // bass only
        { lead: null, bass: null }, // full rest
        { lead: 7, bass: 3 }, // both
      ],
    };

    sequencer.setTrack(trackWithRests);
    expect(sequencer.getCurrentStep()).toBe(0);
    expect(sequencer.getTrack().id).toBe('test_rests');

    // Step 0: lead only (index 5)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(1);
    expect(playWebNote).toHaveBeenCalledTimes(1);
    expect(playWebNote).toHaveBeenLastCalledWith(PENTATONIC_FREQUENCIES[5], 0.12);

    // Step 1: bass only (index 0)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(2);
    expect(playWebNote).toHaveBeenCalledTimes(2);
    expect(playWebNote).toHaveBeenLastCalledWith(PENTATONIC_FREQUENCIES[0], 0.08);

    // Step 2: full rest (nothing emitted)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(3);
    expect(playWebNote).toHaveBeenCalledTimes(2);

    // Step 3: both lead (7) and bass (3)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(0);
    expect(playWebNote).toHaveBeenCalledTimes(4);
    expect(playWebNote).toHaveBeenCalledWith(PENTATONIC_FREQUENCIES[7], 0.12);
    expect(playWebNote).toHaveBeenCalledWith(PENTATONIC_FREQUENCIES[3], 0.08);
  });

  it('calculates dynamic volume ducking on input and restores after timeout', () => {
    const sequencer = new MelodySequencer();

    // Default resting volume
    expect(sequencer.calculateVolume(false)).toBe(0.12);
    expect(sequencer.calculateVolume(true)).toBe(0.08);

    // Ducking triggered
    sequencer.notifyInput();
    expect(sequencer.calculateVolume(false)).toBe(0.03);
    expect(sequencer.calculateVolume(true)).toBe(0.05);

    // Fast-forward past ducking window (3500ms)
    vi.advanceTimersByTime(3600);
    expect(sequencer.calculateVolume(false)).toBe(0.12);
    expect(sequencer.calculateVolume(true)).toBe(0.08);
  });

  it('calculates attenuated volume in UI mode regardless of input', () => {
    const sequencer = new MelodySequencer();
    expect(sequencer.getMode()).toBe('idle');

    sequencer.setMode('ui');
    expect(sequencer.getMode()).toBe('ui');
    expect(sequencer.calculateVolume(false)).toBe(0.02);
    expect(sequencer.calculateVolume(true)).toBe(0.04);

    // Even if input is notified, UI mode maintains quiet attenuation
    sequencer.notifyInput();
    expect(sequencer.calculateVolume(false)).toBe(0.02);
    expect(sequencer.calculateVolume(true)).toBe(0.04);
  });

  it('schedules playback intervals and halts on stop', () => {
    const playWebNote = vi.fn();
    const sequencer = new MelodySequencer({ playWebNote });

    expect(sequencer.getCurrentStep()).toBe(0);
    expect(sequencer.getTrack().stepIntervalMs).toBe(260);

    sequencer.start();
    expect(playWebNote).not.toHaveBeenCalled();

    // Advance by track interval (260ms for STARLIGHT_LULLABY)
    vi.advanceTimersByTime(260);
    expect(playWebNote).toHaveBeenCalled();
    expect(sequencer.getCurrentStep()).toBe(1);

    const callCount = playWebNote.mock.calls.length;
    sequencer.stop();

    // Advancing timers further should NOT trigger additional notes or steps
    vi.advanceTimersByTime(1000);
    expect(playWebNote.mock.calls.length).toBe(callCount);
    expect(sequencer.getCurrentStep()).toBe(1);
  });
});
