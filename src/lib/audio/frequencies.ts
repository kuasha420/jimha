// Soothing celestial pentatonic frequencies (Hz) across octaves 4, 5, and 6
// Exact frequencies matching legacy JimHa sound synthesis
export const PENTATONIC_FREQUENCIES: readonly number[] = [
  261.63, // C4
  293.66, // D4
  329.63, // E4
  392.00, // G4
  440.00, // A4
  523.25, // C5
  587.33, // D5
  659.25, // E5
  783.99, // G5
  880.00, // A5
  1046.50, // C6
];

export interface FrequencySelection {
  frequency: number;
  index: number;
  noteName: string;
}

export const NOTE_NAMES: readonly string[] = [
  'C4', 'D4', 'E4', 'G4', 'A4',
  'C5', 'D5', 'E5', 'G5', 'A5',
  'C6'
];

/**
 * Maps a key or sequential index to a soothing pentatonic frequency.
 */
export function getFrequencyForKey(keyText: string = '', noteIndex: number = 0): FrequencySelection {
  const len = PENTATONIC_FREQUENCIES.length;
  let idx: number;

  if (keyText && keyText.length > 0) {
    idx = (keyText.charCodeAt(0) + noteIndex) % len;
  } else {
    idx = noteIndex % len;
  }

  // Ensure positive index
  idx = ((idx % len) + len) % len;

  return {
    frequency: PENTATONIC_FREQUENCIES[idx],
    index: idx,
    noteName: NOTE_NAMES[idx]
  };
}
