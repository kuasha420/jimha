import { describe, it, expect, beforeEach } from 'vitest';
import {
  RekkaBuffer,
  KONAMI_SEQUENCE,
  QUICK_SWITCH_SEQUENCE,
  NAVIGATOR_SEQUENCE,
} from './rekka';

describe('RekkaBuffer Arcade Combo Engine', () => {
  let rekka: RekkaBuffer;

  beforeEach(() => {
    rekka = new RekkaBuffer(0.8);
  });

  it('initializes with empty buffer', () => {
    expect(rekka.length).toBe(0);
    expect(rekka.getTokens()).toEqual([]);
  });

  it('adds tokens and normalizes to uppercase', () => {
    rekka.add('up', 100.0);
    rekka.add('down', 100.2);
    expect(rekka.getTokens()).toEqual(['UP', 'DOWN']);
    expect(rekka.length).toBe(2);
  });

  it('caps buffer capacity at 30 items', () => {
    for (let i = 0; i < 40; i++) {
      rekka.add(`K_${i}`, 100.0 + i * 0.01);
    }
    expect(rekka.length).toBe(30);
    expect(rekka.getTokens()[0]).toBe('K_10');
    expect(rekka.getTokens()[29]).toBe('K_39');
  });

  it('decays automatically when elapsed time exceeds decayTimeout on add', () => {
    rekka.add('UP', 100.0);
    rekka.add('UP', 100.2);
    expect(rekka.getTokens()).toEqual(['UP', 'UP']);

    // Add after 0.9s (> 0.8s decay)
    rekka.add('DOWN', 101.1);
    expect(rekka.getTokens()).toEqual(['DOWN']);
  });

  it('checkDecay clears expired buffer', () => {
    rekka.add('UP', 100.0);
    expect(rekka.checkDecay(100.5)).toBe(false);
    expect(rekka.length).toBe(1);

    expect(rekka.checkDecay(100.85)).toBe(true);
    expect(rekka.length).toBe(0);
  });

  it('clear() empties the buffer', () => {
    rekka.add('UP', 100.0);
    rekka.add('DOWN', 100.2);
    rekka.clear();
    expect(rekka.length).toBe(0);
    expect(rekka.getTokens()).toEqual([]);
  });

  it('matches KONAMI sequence correctly', () => {
    const keys = ['UP', 'UP', 'DOWN', 'DOWN', 'LEFT', 'RIGHT', 'LEFT', 'RIGHT', 'B', 'A'];
    let t = 100.0;
    for (const k of keys) {
      rekka.add(k, t);
      t += 0.1;
    }
    expect(rekka.matches(KONAMI_SEQUENCE)).toBe(true);
    expect(rekka.endsWith(KONAMI_SEQUENCE)).toBe(true);
  });

  it('matches QUICK_SWITCH_SEQUENCE correctly', () => {
    rekka.add('UP', 100.0);
    rekka.add('UP', 100.1);
    rekka.add('DOWN', 100.2);
    rekka.add('DOWN', 100.3);
    expect(rekka.matches(QUICK_SWITCH_SEQUENCE)).toBe(true);
  });

  it('matches NAVIGATOR_SEQUENCE [UP, UP]', () => {
    rekka.add('UP', 100.0);
    expect(rekka.matches(NAVIGATOR_SEQUENCE)).toBe(false);
    rekka.add('UP', 100.1);
    expect(rekka.matches(NAVIGATOR_SEQUENCE)).toBe(true);
  });

  it('returns false when buffer is shorter than sequence', () => {
    rekka.add('UP', 100.0);
    expect(rekka.matches(QUICK_SWITCH_SEQUENCE)).toBe(false);
  });
});
