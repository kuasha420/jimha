import { describe, it, expect } from 'vitest';
import { calculateElasticScale, calculateCardAlpha } from './spring';

describe('Spring Math & Elastic Scale Contract', () => {
  it('returns initial scale when cardAge is 0 or negative', () => {
    expect(calculateElasticScale(0)).toBe(0.2);
    expect(calculateElasticScale(-0.1)).toBe(0.2);
  });

  it('peaks at overshoot scale around halfway through duration (0.175s)', () => {
    const midpointScale = calculateElasticScale(0.175);
    // At halfway (progress = 0.5): sin(0.5 * PI) = 1.0
    // scale = 0.2 + 0.8 * (1.0 + 0.35) = 0.2 + 0.8 * 1.35 = 0.2 + 1.08 = 1.28
    expect(midpointScale).toBeCloseTo(1.28, 2);
    expect(midpointScale).toBeGreaterThan(1.0);
  });

  it('settles to exactly 1.0 when cardAge reaches or exceeds duration (0.35s)', () => {
    expect(calculateElasticScale(0.35)).toBe(1.0);
    expect(calculateElasticScale(0.5)).toBe(1.0);
    expect(calculateElasticScale(2.0)).toBe(1.0);
  });

  it('computes smooth alpha decay over time', () => {
    expect(calculateCardAlpha(1.0)).toBe(1.0);
    expect(calculateCardAlpha(3.0)).toBe(1.0);
    expect(calculateCardAlpha(3.75)).toBeCloseTo(0.6, 2);
    expect(calculateCardAlpha(5.0)).toBe(0.2);
  });
});
