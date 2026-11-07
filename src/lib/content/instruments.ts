export type InstrumentId = 'celesta' | 'marimba' | 'kalimba' | 'music_box';

export interface InstrumentConfig {
  id: InstrumentId;
  name: string;
  emoji: string;
  description: string;
  harmonicMultipliers: number[];
  harmonicGains: number[];
  decayBodyRate: number;
  decayShimmerRate: number;
  attackSeconds: number;
}

export const INSTRUMENT_CELESTA: InstrumentConfig = {
  id: 'celesta',
  name: 'Celesta',
  emoji: '✨',
  description: 'Shimmering celestial chimes with rich harmonic overtones',
  harmonicMultipliers: [1.0, 2.0, 3.0, 4.2, 5.4],
  harmonicGains: [1.0, 0.35, 0.18, 0.1, 0.05],
  decayBodyRate: 2.5,
  decayShimmerRate: 5.5,
  attackSeconds: 0.004,
};

export const INSTRUMENT_MARIMBA: InstrumentConfig = {
  id: 'marimba',
  name: 'Wooden Marimba',
  emoji: '🪵',
  description: 'Warm organic wooden bars with quick resonant strike',
  harmonicMultipliers: [1.0, 3.0, 9.2, 12.0],
  harmonicGains: [1.0, 0.4, 0.08, 0.03],
  decayBodyRate: 4.5,
  decayShimmerRate: 9.0,
  attackSeconds: 0.002,
};

export const INSTRUMENT_KALIMBA: InstrumentConfig = {
  id: 'kalimba',
  name: 'Gentle Kalimba',
  emoji: '🔔',
  description: 'Gentle metallic thumb piano tines with soothing acoustic warmth',
  harmonicMultipliers: [1.0, 2.76, 5.4, 8.1],
  harmonicGains: [1.0, 0.25, 0.15, 0.06],
  decayBodyRate: 2.0,
  decayShimmerRate: 4.0,
  attackSeconds: 0.005,
};

export const INSTRUMENT_MUSIC_BOX: InstrumentConfig = {
  id: 'music_box',
  name: 'Music Box',
  emoji: '🎶',
  description: 'Crystalline music box cylinder with sparkling high-frequency ring',
  harmonicMultipliers: [1.0, 2.0, 3.0, 4.0, 6.0],
  harmonicGains: [1.0, 0.5, 0.3, 0.15, 0.08],
  decayBodyRate: 1.8,
  decayShimmerRate: 3.0,
  attackSeconds: 0.001,
};

export const INSTRUMENTS: Record<InstrumentId, InstrumentConfig> = {
  celesta: INSTRUMENT_CELESTA,
  marimba: INSTRUMENT_MARIMBA,
  kalimba: INSTRUMENT_KALIMBA,
  music_box: INSTRUMENT_MUSIC_BOX,
};

export const ALL_INSTRUMENTS: InstrumentConfig[] = [
  INSTRUMENT_CELESTA,
  INSTRUMENT_MARIMBA,
  INSTRUMENT_KALIMBA,
  INSTRUMENT_MUSIC_BOX,
];

export function getInstrumentConfig(id: InstrumentId | string): InstrumentConfig {
  if (id in INSTRUMENTS) {
    return INSTRUMENTS[id as InstrumentId];
  }
  return INSTRUMENT_CELESTA;
}
