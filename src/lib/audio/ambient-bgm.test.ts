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
      gain: { setValueAtTime: vi.fn() },
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
    expect(mockFilter.frequency.setValueAtTime).toHaveBeenCalledWith(3000, 10);

    // Switch to playing mode -> 900 Hz with 0.3s transition
    engine.setMode('playing');
    expect(engine.getMode()).toBe('playing');
    expect(setTargetAtTime).toHaveBeenCalledWith(900, 10, 0.3);

    // Switch to ui mode -> 750 Hz with 0.3s transition
    engine.setMode('ui');
    expect(engine.getMode()).toBe('ui');
    expect(setTargetAtTime).toHaveBeenCalledWith(750, 10, 0.3);

    // Switch back to idle mode -> 3000 Hz with 0.3s transition
    engine.setMode('idle');
    expect(engine.getMode()).toBe('idle');
    expect(setTargetAtTime).toHaveBeenCalledWith(3000, 10, 0.3);
  });
});
