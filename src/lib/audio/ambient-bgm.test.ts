import { describe, it, expect, vi } from 'vitest';
import { AmbientBgmEngine } from './ambient-bgm';

describe('AmbientBgmEngine Contract', () => {
  it('initializes in idle mode and transitions correctly', () => {
    const engine = new AmbientBgmEngine();
    expect(engine.getMode()).toBe('idle');

    engine.setMode('playing');
    expect(engine.getMode()).toBe('playing');

    engine.setMode('ui');
    expect(engine.getMode()).toBe('ui');

    engine.setMode('idle');
    expect(engine.getMode()).toBe('idle');
  });

  it('notifies input and ducks into playing mode from idle', () => {
    const engine = new AmbientBgmEngine();
    engine.start();
    expect(engine.getMode()).toBe('idle');

    engine.notifyInput();
    expect(engine.getMode()).toBe('playing');

    engine.stop();
  });

  it('retains ui mode during input notification when modal is open', () => {
    const engine = new AmbientBgmEngine();
    engine.start();
    engine.setMode('ui');

    engine.notifyInput();
    expect(engine.getMode()).toBe('ui');

    engine.stop();
  });

  it('configures filter cutoff frequencies correctly for idle, playing, and ui modes', () => {
    const setTargetAtTime = vi.fn();
    const setValueAtTime = vi.fn();
    const mockFilter = {
      type: 'lowpass',
      frequency: {
        setTargetAtTime,
        setValueAtTime,
      },
      connect: vi.fn(),
    };
    const mockGain = {
      gain: {
        setValueAtTime: vi.fn(),
        setTargetAtTime: vi.fn(),
      },
      connect: vi.fn(),
    };
    const mockCtx = {
      currentTime: 10,
      createBiquadFilter: vi.fn().mockReturnValue(mockFilter),
      createGain: vi.fn().mockReturnValue(mockGain),
      destination: {},
    } as unknown as AudioContext;

    const engine = new AmbientBgmEngine(mockCtx);
    expect(engine.getMode()).toBe('idle');
    expect(mockFilter.frequency.setValueAtTime).toHaveBeenCalledWith(2500, 10);

    // Switch to playing mode -> 450 Hz with 0.2s transition
    engine.setMode('playing');
    expect(engine.getMode()).toBe('playing');
    expect(setTargetAtTime).toHaveBeenCalledWith(450, 10, 0.2);

    // Switch to ui mode -> 600 Hz with 1.5s transition
    engine.setMode('ui');
    expect(engine.getMode()).toBe('ui');
    expect(setTargetAtTime).toHaveBeenCalledWith(600, 10, 1.5);

    // Switch back to idle mode -> 2500 Hz with 1.5s transition
    engine.setMode('idle');
    expect(engine.getMode()).toBe('idle');
    expect(setTargetAtTime).toHaveBeenCalledWith(2500, 10, 1.5);
  });

  it('automatically recovers from playing to idle mode after 3.5s idle timeout', () => {
    vi.useFakeTimers();
    const engine = new AmbientBgmEngine();
    engine.start();
    expect(engine.getMode()).toBe('idle');

    engine.notifyInput();
    expect(engine.getMode()).toBe('playing');

    // Advance 2000ms -> should still be playing
    vi.advanceTimersByTime(2000);
    expect(engine.getMode()).toBe('playing');

    // Re-notify input before timer expires -> resets timer
    engine.notifyInput();
    vi.advanceTimersByTime(2000);
    expect(engine.getMode()).toBe('playing');

    // Advance remaining time past 3500ms
    vi.advanceTimersByTime(2000);
    expect(engine.getMode()).toBe('idle');

    engine.stop();
    vi.useRealTimers();
  });
});
