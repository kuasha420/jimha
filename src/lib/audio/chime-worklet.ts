/**
 * Dedicated AudioWorklet processor code for real-time DSP celestial chime synthesis.
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
        this.voices.push({
          frequency: data.frequency || 440.0,
          sampleRate: sampleRate,
          sampleIndex: 0,
          totalSamples: Math.floor(sampleRate * 0.85)
        });
      }
    };
  }

  process(inputs, outputs) {
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

      for (let i = 0; i < bufferSize; i++) {
        if (voice.sampleIndex >= total) break;
        const t = voice.sampleIndex / sr;
        const attack = Math.min(1.0, t / 0.004);
        const decayBody = Math.exp(-2.5 * t);
        const decayShimmer = Math.exp(-5.5 * t);

        const s1L = Math.sin(2.0 * Math.PI * f * t) * decayBody;
        const s2L = 0.35 * Math.sin(2.0 * Math.PI * (2.0 * f) * t) * decayBody;
        const s3L = 0.18 * Math.sin(2.0 * Math.PI * (3.0 * f) * t + phaseOffset) * decayShimmer;
        const s4L = 0.10 * Math.sin(2.0 * Math.PI * (4.2 * f) * t) * decayShimmer;
        const s5L = 0.05 * Math.sin(2.0 * Math.PI * (5.4 * f) * t) * decayShimmer;

        const s1R = Math.sin(2.0 * Math.PI * f * t + phaseOffset * 0.5) * decayBody;
        const s2R = 0.35 * Math.sin(2.0 * Math.PI * (2.0 * f) * t) * decayBody;
        const s3R = 0.18 * Math.sin(2.0 * Math.PI * (3.0 * f) * t) * decayShimmer;
        const s4R = 0.10 * Math.sin(2.0 * Math.PI * (4.2 * f) * t + phaseOffset) * decayShimmer;
        const s5R = 0.05 * Math.sin(2.0 * Math.PI * (5.4 * f) * t) * decayShimmer;

        const valL = attack * (s1L + s2L + s3L + s4L + s5L) * 0.45;
        const valR = attack * (s1R + s2R + s3R + s4R + s5R) * 0.45;

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
  }
}

registerProcessor('jimha-chime-processor', JimhaChimeProcessor);
`;
