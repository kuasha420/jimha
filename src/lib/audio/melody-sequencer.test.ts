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
    expect(playWebNote).toHaveBeenLastCalledWith(PENTATONIC_FREQUENCIES[5], 0.06);

    // Step 1: bass only (index 0)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(2);
    expect(playWebNote).toHaveBeenCalledTimes(2);
    expect(playWebNote).toHaveBeenLastCalledWith(PENTATONIC_FREQUENCIES[0], 0.04);

    // Step 2: full rest (nothing emitted)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(3);
    expect(playWebNote).toHaveBeenCalledTimes(2);

    // Step 3: both lead (7) and bass (3)
    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(0);
    expect(playWebNote).toHaveBeenCalledTimes(4);
    expect(playWebNote).toHaveBeenCalledWith(PENTATONIC_FREQUENCIES[7], 0.06);
    expect(playWebNote).toHaveBeenCalledWith(PENTATONIC_FREQUENCIES[3], 0.04);
  });

  it('calculates dynamic volume ducking on input and restores after timeout', () => {
    const sequencer = new MelodySequencer();

    // Default resting volume
    expect(sequencer.calculateVolume(false)).toBe(0.06);
    expect(sequencer.calculateVolume(true)).toBe(0.04);

    // Ducking triggered (< 3000ms): lead muted (0.0), bass reduced to 0.02
    sequencer.notifyInput();
    expect(sequencer.calculateVolume(false)).toBe(0.0);
    expect(sequencer.calculateVolume(true)).toBe(0.02);

    // Active key input at 2000ms still muted
    vi.advanceTimersByTime(2000);
    expect(sequencer.calculateVolume(false)).toBe(0.0);
    expect(sequencer.calculateVolume(true)).toBe(0.02);

    // Quadratic recovery ramp between 3000ms and 6000ms
    // At elapsed = 4500ms (advance 2500ms: 2000 + 2500 = 4500ms)
    // progress = (4500 - 3000) / 3000 = 0.5
    // ramp = 0.5 * 0.5 = 0.25
    // lead = 0.06 * 0.25 = 0.015
    // bass = 0.02 + 0.02 * 0.5 = 0.03
    vi.advanceTimersByTime(2500);
    expect(sequencer.calculateVolume(false)).toBeCloseTo(0.015);
    expect(sequencer.calculateVolume(true)).toBeCloseTo(0.03);

    // Fully restored after 6000ms (advance 2000ms more: 4500 + 2000 = 6500ms >= 6000ms)
    vi.advanceTimersByTime(2000);
    expect(sequencer.calculateVolume(false)).toBe(0.06);
    expect(sequencer.calculateVolume(true)).toBe(0.04);
  });

  it('calculates attenuated volume in UI mode regardless of input', () => {
    const sequencer = new MelodySequencer();
    expect(sequencer.getMode()).toBe('idle');

    sequencer.setMode('ui');
    expect(sequencer.getMode()).toBe('ui');
    expect(sequencer.calculateVolume(false)).toBe(0.015);
    expect(sequencer.calculateVolume(true)).toBe(0.03);

    // Even if input is notified, UI mode maintains quiet attenuation
    sequencer.notifyInput();
    expect(sequencer.calculateVolume(false)).toBe(0.015);
    expect(sequencer.calculateVolume(true)).toBe(0.03);
  });

  it('skips dispatching lead note during active ducking when volume is 0', () => {
    const playWebNote = vi.fn();
    const sequencer = new MelodySequencer({ playWebNote });

    const track: MelodicTrack = {
      id: 'test_duck_skip',
      name: 'Test Duck Skip',
      timeSignature: '4/4',
      stepIntervalMs: 100,
      steps: [{ lead: 5, bass: 0 }],
    };

    sequencer.setTrack(track);
    expect(sequencer.getCurrentStep()).toBe(0);
    expect(sequencer.getTrack().id).toBe('test_duck_skip');

    sequencer.notifyInput(); // Trigger active ducking: lead is 0.0 (<= 0.001), bass is 0.02
    expect(sequencer.calculateVolume(false)).toBe(0.0);
    expect(sequencer.calculateVolume(true)).toBe(0.02);

    sequencer.advanceStep();
    expect(sequencer.getCurrentStep()).toBe(0);
    // Lead note is skipped because volume <= 0.001
    // Bass note is played with volume 0.02
    expect(playWebNote).toHaveBeenCalledTimes(1);
    expect(playWebNote).toHaveBeenCalledWith(PENTATONIC_FREQUENCIES[0], 0.02);
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
