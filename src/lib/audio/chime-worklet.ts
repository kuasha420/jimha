/**
 * Dedicated AudioWorklet processor code for real-time DSP multi-instrument synthesis.
 * Running on high-priority audio rendering thread for 0ms latency.
 */

export const CHIME_WORKLET_PROCESSOR_CODE = `
class JimhaChimeProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.voices = [];
    this.port.onmessage = (event) => {
      const data = event.data;
      if (data && data.type === 'trigger') {
        const sr = data.sampleRate || (typeof sampleRate !== 'undefined' ? sampleRate : 44100);
        this.voices.push({
          frequency: data.frequency || 440.0,
          sampleRate: sr,
          sampleIndex: 0,
          totalSamples: Math.floor(sr * 0.85),
          multipliers: data.multipliers || [1.0, 2.0, 3.0, 4.2, 5.4],
          gains: data.gains || [1.0, 0.35, 0.18, 0.10, 0.05],
          decayBodyRate: data.decayBodyRate || 2.5,
          decayShimmerRate: data.decayShimmerRate || 5.5,
          attackSeconds: data.attackSeconds || 0.004
        });
      }
    };
  }

  process(inputs, outputs) {
    try {
      const output = outputs[0];
      if (!output || output.length === 0) return true;

      const left = output[0];
      const right = output[1] || output[0];
      const bufferSize = left.length;

      for (let i = 0; i < bufferSize; i++) {
        left[i] = 0;
        if (output[1]) right[i] = 0;
      }

      if (this.voices.length === 0) return true;

      const phaseOffset = Math.PI * 0.08;
      const activeVoices = [];

      for (let v = 0; v < this.voices.length; v++) {
        const voice = this.voices[v];
        const f = voice.frequency;
        const sr = voice.sampleRate;
        const total = voice.totalSamples;
        const mults = voice.multipliers;
        const gains = voice.gains;
        const decayBodyRate = voice.decayBodyRate;
        const decayShimmerRate = voice.decayShimmerRate;
        const attackSec = voice.attackSeconds;

        for (let i = 0; i < bufferSize; i++) {
          if (voice.sampleIndex >= total) break;
          const t = voice.sampleIndex / sr;
          const attack = Math.min(1.0, t / attackSec);
          const decayBody = Math.exp(-decayBodyRate * t);
          const decayShimmer = Math.exp(-decayShimmerRate * t);

          let sumL = 0;
          let sumR = 0;

          for (let h = 0; h < mults.length; h++) {
            const mult = mults[h];
            const gain = gains[h];
            const decay = mult <= 2.0 ? decayBody : decayShimmer;
            const phaseL = h === 2 ? phaseOffset : 0;
            const phaseR = h === 0 ? phaseOffset * 0.5 : h === 3 ? phaseOffset : 0;

            sumL += gain * Math.sin(2.0 * Math.PI * (mult * f) * t + phaseL) * decay;
            sumR += gain * Math.sin(2.0 * Math.PI * (mult * f) * t + phaseR) * decay;
          }

          const valL = attack * sumL * 0.45;
          const valR = attack * sumR * 0.45;

          left[i] += valL;
          if (output[1]) right[i] += valR;

          voice.sampleIndex++;
        }

        if (voice.sampleIndex < total) {
          activeVoices.push(voice);
        }
      }

      this.voices = activeVoices;
      return true;
    } catch (_) {
      return true;
    }
  }
}

registerProcessor('jimha-chime-processor', JimhaChimeProcessor);
`;
