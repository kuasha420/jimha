/**
 * Pure DSP synthesis for Jimha celestial music-box chimes.
 * Exact replication of harmonic spectrum, attack envelope, dual decay,
 * and stereo phase spread from legacy sound_synth.py.
 */

export interface SynthesizedChime {
  left: Float32Array;
  right: Float32Array;
  sampleRate: number;
  duration: number;
  peak: number;
}

export function synthesizeChimeSamples(
  frequency: number,
  sampleRate: number = 44100,
  duration: number = 0.85
): SynthesizedChime {
  const nSamples = Math.floor(sampleRate * duration);
  const left = new Float32Array(nSamples);
  const right = new Float32Array(nSamples);

  // Subtle stereo phase offset between left and right channels
  const phaseOffset = Math.PI * 0.08;

  let maxPeak = 1e-6;

  for (let i = 0; i < nSamples; i++) {
    const t = i / sampleRate;

    // 4ms attack envelope to prevent clicks
    const attack = Math.min(1.0, t / 0.004);

    // Dual decay: fast shimmer decay + long fundamental sustain
    const decayBody = Math.exp(-2.5 * t);
    const decayShimmer = Math.exp(-5.5 * t);

    // Left channel harmonic spectrum
    const s1L = Math.sin(2.0 * Math.PI * frequency * t) * decayBody;
    const s2L = 0.35 * Math.sin(2.0 * Math.PI * (2.0 * frequency) * t) * decayBody;
    const s3L = 0.18 * Math.sin(2.0 * Math.PI * (3.0 * frequency) * t + phaseOffset) * decayShimmer;
    const s4L = 0.10 * Math.sin(2.0 * Math.PI * (4.2 * frequency) * t) * decayShimmer;
    const s5L = 0.05 * Math.sin(2.0 * Math.PI * (5.4 * frequency) * t) * decayShimmer;

    // Right channel (subtle harmonic stereo spread)
    const s1R = Math.sin(2.0 * Math.PI * frequency * t + phaseOffset * 0.5) * decayBody;
    const s2R = 0.35 * Math.sin(2.0 * Math.PI * (2.0 * frequency) * t) * decayBody;
    const s3R = 0.18 * Math.sin(2.0 * Math.PI * (3.0 * frequency) * t) * decayShimmer;
    const s4R = 0.10 * Math.sin(2.0 * Math.PI * (4.2 * frequency) * t + phaseOffset) * decayShimmer;
    const s5R = 0.05 * Math.sin(2.0 * Math.PI * (5.4 * frequency) * t) * decayShimmer;

    const valL = attack * (s1L + s2L + s3L + s4L + s5L);
    const valR = attack * (s1R + s2R + s3R + s4R + s5R);

    left[i] = valL;
    right[i] = valR;

    const absL = Math.abs(valL);
    const absR = Math.abs(valR);
    if (absL > maxPeak) maxPeak = absL;
    if (absR > maxPeak) maxPeak = absR;
  }

  // Normalize to 92% full scale (-0.7 dB) to prevent clipping while maximizing clarity
  const scale = 0.92 / maxPeak;
  for (let i = 0; i < nSamples; i++) {
    left[i] = Math.max(-1.0, Math.min(1.0, left[i] * scale));
    right[i] = Math.max(-1.0, Math.min(1.0, right[i] * scale));
  }

  return {
    left,
    right,
    sampleRate,
    duration,
    peak: maxPeak
  };
}
