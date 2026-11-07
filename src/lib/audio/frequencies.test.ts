import { describe, it, expect } from 'vitest';
import { PENTATONIC_FREQUENCIES, NOTE_NAMES, getFrequencyForKey } from './frequencies';

describe('Pentatonic Frequencies & Audio Mapping Contract', () => {
  it('defines exactly 11 celestial pentatonic tones from C4 to C6', () => {
    expect(PENTATONIC_FREQUENCIES.length).toBe(11);
    expect(NOTE_NAMES.length).toBe(11);

    expect(PENTATONIC_FREQUENCIES[0]).toBe(261.63); // C4
    expect(PENTATONIC_FREQUENCIES[4]).toBe(440.00); // A4
    expect(PENTATONIC_FREQUENCIES[5]).toBe(523.25); // C5
    expect(PENTATONIC_FREQUENCIES[10]).toBe(1046.50); // C6
  });

  it('correctly maps sequential note indexes within pentatonic bounds', () => {
    for (let i = 0; i < 22; i++) {
      const selection = getFrequencyForKey('', i);
      expect(selection.index).toBe(i % 11);
      expect(selection.frequency).toBe(PENTATONIC_FREQUENCIES[i % 11]);
      expect(selection.noteName).toBe(NOTE_NAMES[i % 11]);
    }
  });

  it('determines deterministic harmonic pitch based on key characters', () => {
    const keyA = getFrequencyForKey('A', 0);
    const keyB = getFrequencyForKey('B', 0);
    expect(keyA.index).toBe(10);
    expect(keyA.frequency).toBe(1046.50);
    expect(keyA.noteName).toBe('C6');

    expect(keyB.index).toBe(0);
    expect(keyB.frequency).toBe(261.63);
    expect(keyB.noteName).toBe('C4');
  });

  it('wraps around negative noteIndex correctly to valid pentatonic frequency', () => {
    const selection = getFrequencyForKey('', -1);
    expect(selection.index).toBe(10);
    expect(selection.frequency).toBe(1046.50);
    expect(selection.noteName).toBe('C6');
  });
});
