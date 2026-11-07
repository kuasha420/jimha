import { describe, it, expect } from 'vitest';
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
});
