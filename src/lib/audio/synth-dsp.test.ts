import { describe, it, expect } from 'vitest';
import { synthesizeChimeSamples } from './synth-dsp';

describe('DSP Chime Synthesis Contract', () => {
  it('synthesizes non-empty stereo Float32Array buffers with 44100Hz and 0.85s duration', () => {
    const result = synthesizeChimeSamples(440.0, 44100, 0.85);
    const expectedLength = Math.floor(44100 * 0.85);

    expect(result.left.length).toBe(expectedLength);
    expect(result.right.length).toBe(expectedLength);
    expect(result.sampleRate).toBe(44100);
    expect(result.duration).toBe(0.85);
  });

  it('smooths attack envelope at start (sample 0 is 0.0)', () => {
    const result = synthesizeChimeSamples(440.0, 44100, 0.85);
    expect(result.left[0]).toBe(0.0);
    expect(result.right[0]).toBe(0.0);
  });

  it('normalizes output peaks safely within -1.0 to 1.0 (-0.7 dB scale)', () => {
    const result = synthesizeChimeSamples(523.25, 44100, 0.85);
    let maxAbs = 0;
    for (let i = 0; i < result.left.length; i++) {
      const absL = Math.abs(result.left[i]);
      const absR = Math.abs(result.right[i]);
      if (absL > maxAbs) maxAbs = absL;
      if (absR > maxAbs) maxAbs = absR;
    }
    expect(maxAbs).toBeLessThanOrEqual(0.92001);
    expect(maxAbs).toBeGreaterThan(0.5);
  });

  it('exhibits stereo phase spread between left and right channels', () => {
    const result = synthesizeChimeSamples(329.63, 44100, 0.85);
    let diffSum = 0;
    for (let i = 500; i < 1500; i++) {
      diffSum += Math.abs(result.left[i] - result.right[i]);
    }
    expect(diffSum).toBeGreaterThan(0);
  });
});
