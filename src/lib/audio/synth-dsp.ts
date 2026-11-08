/**
 * Pure DSP synthesis for Jimha celestial music-box chimes.
 * Exact replication of harmonic spectrum, attack envelope, dual decay,
 * and stereo phase spread from legacy sound_synth.py.
 */

import {
  getInstrumentConfig,
  type InstrumentConfig,
  type InstrumentId,
} from '../content/instruments';

export interface SynthesizedChime {
  left: Float32Array;
  right: Float32Array;
  sampleRate: number;
  duration: number;
  peak: number;
}

function computeHarmonicSample(
  t: number,
  frequency: number,
  multipliers: readonly number[],
  gains: readonly number[],
  decayBody: number,
  decayShimmer: number,
  phaseOffset: number
): [number, number] {
  let sumL = 0;
  let sumR = 0;

  for (let h = 0; h < multipliers.length; h++) {
    const mult = multipliers[h] ?? 1.0;
    const gain = gains[h] ?? 0.0;
    const decay = mult <= 2.0 ? decayBody : decayShimmer;

    // Slight stereo spread on overtones
    const phaseL = h === 2 ? phaseOffset : 0;
    const phaseR = h === 0 ? phaseOffset * 0.5 : h === 3 ? phaseOffset : 0;

    sumL += gain * Math.sin(2.0 * Math.PI * (mult * frequency) * t + phaseL) * decay;
    sumR += gain * Math.sin(2.0 * Math.PI * (mult * frequency) * t + phaseR) * decay;
  }

  return [sumL, sumR];
}

function normalizeStereoBuffers(left: Float32Array, right: Float32Array, maxPeak: number): void {
  const scale = 0.92 / maxPeak;
  const nSamples = left.length;
  for (let i = 0; i < nSamples; i++) {
    const l = left[i];
    const r = right[i];
    if (l !== undefined) left[i] = Math.max(-1.0, Math.min(1.0, l * scale));
    if (r !== undefined) right[i] = Math.max(-1.0, Math.min(1.0, r * scale));
  }
}

export function synthesizeChimeSamples(
  frequency: number,
  sampleRate: number = 44100,
  duration: number = 0.85,
  instrumentOrId: InstrumentId | InstrumentConfig = 'celesta'
): SynthesizedChime {
  const config =
    typeof instrumentOrId === 'string' ? getInstrumentConfig(instrumentOrId) : instrumentOrId;

  const nSamples = Math.floor(sampleRate * duration);
  const left = new Float32Array(nSamples);
  const right = new Float32Array(nSamples);

  // Subtle stereo phase offset between left and right channels
  const phaseOffset = Math.PI * 0.08;

  let maxPeak = 1e-6;
  const attackSec = config.attackSeconds || 0.004;
  const decayBodyRate = config.decayBodyRate || 2.5;
  const decayShimmerRate = config.decayShimmerRate || 5.5;
  const multipliers = config.harmonicMultipliers;
  const gains = config.harmonicGains;

  for (let i = 0; i < nSamples; i++) {
    const t = i / sampleRate;

    // Attack envelope to prevent clicks
    const attack = Math.min(1.0, t / attackSec);

    // Dual decay: fast shimmer decay + body sustain
    const decayBody = Math.exp(-decayBodyRate * t);
    const decayShimmer = Math.exp(-decayShimmerRate * t);

    const [sumL, sumR] = computeHarmonicSample(
      t,
      frequency,
      multipliers,
      gains,
      decayBody,
      decayShimmer,
      phaseOffset
    );

    const valL = attack * sumL;
    const valR = attack * sumR;

    left[i] = valL;
    right[i] = valR;

    const absL = Math.abs(valL);
    const absR = Math.abs(valR);
    if (absL > maxPeak) maxPeak = absL;
    if (absR > maxPeak) maxPeak = absR;
  }

  // Normalize to 92% full scale (-0.7 dB) to prevent clipping while maximizing clarity
  normalizeStereoBuffers(left, right, maxPeak);

  return {
    left,
    right,
    sampleRate,
    duration,
    peak: maxPeak,
  };
}
