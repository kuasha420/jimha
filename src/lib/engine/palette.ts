import { getNumberContent } from '../content/numbers';

export const PALETTE = [
  '#FF4081', // Bubblegum Pink
  '#00E676', // Electric Mint
  '#FFD600', // Sunshine Yellow
  '#00E5FF', // Cyan Aqua
  '#FF6D00', // Bright Orange
  '#E040FB', // Vibrant Lavender
  '#7C4DFF', // Royal Violet
  '#FF5252', // Coral Red
  '#1DE9B6', // Seafoam Teal
] as const;

export interface CompanionInfo {
  emoji: string;
  word: string;
  subtitle: string;
}

export interface KeyDisplayResult {
  title: string;
  subtitle: string;
  emoji: string;
  color?: string;
}

export const ALPHABET_COMPANIONS: Record<string, [string, string]> = {
  A: ['🍎', 'Apple'],
  B: ['🦋', 'Butterfly'],
  C: ['🐱', 'Cat'],
  D: ['🐶', 'Dog'],
  E: ['🐘', 'Elephant'],
  F: ['🌸', 'Flower'],
  G: ['🎸', 'Guitar'],
  H: ['❤️', 'Heart'],
  I: ['🍦', 'Ice Cream'],
  J: ['👑', 'Jimha! ✨'], // The queen herself!
  K: ['🪁', 'Kite'],
  L: ['🦁', 'Lion'],
  M: ['🌙', 'Moon'],
  N: ['🌈', 'Nature'],
  O: ['🦉', 'Owl'],
  P: ['🐼', 'Panda'],
  Q: ['👑', 'Queen'],
  R: ['🚀', 'Rocket'],
  S: ['⭐', 'Star'],
  T: ['🐯', 'Tiger'],
  U: ['🦄', 'Unicorn'],
  V: ['🎻', 'Violin'],
  W: ['🌊', 'Wave'],
  X: ['🎁', 'Xylophone'],
  Y: ['⛵', 'Yacht'],
  Z: ['🦓', 'Zebra'],
};

export function getRandomColor(palette: readonly string[] = PALETTE): string {
  const idx = Math.floor(Math.random() * palette.length);
  return palette[idx] ?? '#FF4081';
}

const SPECIAL_KEYS: Record<string, KeyDisplayResult> = {
  ESCAPE: {
    title: 'ESCAPE',
    subtitle: '🚀 BLAST OFF TO SPACE! 🚀',
    emoji: '🚀',
    color: '#7C4DFF',
  },
  ESC: {
    title: 'ESCAPE',
    subtitle: '🚀 BLAST OFF TO SPACE! 🚀',
    emoji: '🚀',
    color: '#7C4DFF',
  },
  ' ': {
    title: 'SPACE',
    subtitle: '🌟 COSMIC SUPERNOVA! 🌟',
    emoji: '✨',
  },
  SPACE: {
    title: 'SPACE',
    subtitle: '🌟 COSMIC SUPERNOVA! 🌟',
    emoji: '✨',
  },
  ENTER: {
    title: 'ENTER',
    subtitle: '🎉 PARTY TIME CELEBRATION! 🎉',
    emoji: '🎈',
  },
  BACKSPACE: {
    title: 'POP!',
    subtitle: '🫧 BUBBLE POP! 🫧',
    emoji: '🫧',
  },
  ARROWUP: {
    title: 'UP ⬆️',
    subtitle: '🚀 ROCKETING TO THE STARS!',
    emoji: '🌌',
  },
  UP: {
    title: 'UP ⬆️',
    subtitle: '🚀 ROCKETING TO THE STARS!',
    emoji: '🌌',
  },
  ARROWDOWN: {
    title: 'DOWN ⬇️',
    subtitle: '🌊 DIVING DEEP INTO THE OCEAN!',
    emoji: '🐬',
  },
  DOWN: {
    title: 'DOWN ⬇️',
    subtitle: '🌊 DIVING DEEP INTO THE OCEAN!',
    emoji: '🐬',
  },
  ARROWLEFT: {
    title: 'LEFT ⬅️',
    subtitle: '🌪️ SWISHING TO THE LEFT!',
    emoji: '💫',
  },
  LEFT: {
    title: 'LEFT ⬅️',
    subtitle: '🌪️ SWISHING TO THE LEFT!',
    emoji: '💫',
  },
  ARROWRIGHT: {
    title: 'RIGHT ➡️',
    subtitle: '⚡ DASHING TO THE RIGHT!',
    emoji: '⚡',
  },
  RIGHT: {
    title: 'RIGHT ➡️',
    subtitle: '⚡ DASHING TO THE RIGHT!',
    emoji: '⚡',
  },
};

export function resolveKeyDisplay(rawKey: string): KeyDisplayResult {
  const text = rawKey.trim().toUpperCase();

  if (rawKey === ' ' || text === 'SPACEBAR' || text === 'SPACE') {
    return {
      title: 'SPACE',
      subtitle: '🌟 COSMIC SUPERNOVA! 🌟',
      emoji: '✨',
      color: '#00E5FF',
    };
  }

  const companion = ALPHABET_COMPANIONS[text];
  if (companion) {
    const [emoji, word] = companion;
    return {
      title: text,
      subtitle: `${text} is for ${word} ${emoji}`,
      emoji,
    };
  }

  if (/^\d+$/.test(text)) {
    const numContent = getNumberContent(parseInt(text, 10));
    if (numContent) {
      return {
        title: numContent.title,
        subtitle: numContent.subtitle,
        emoji: numContent.emoji,
        color: numContent.color,
      };
    }
  }

  const special = SPECIAL_KEYS[text];
  if (special) {
    return special;
  }

  return {
    title: text || 'KEY',
    subtitle: '💖 YOU ARE AWESOME JIMHA! 💖',
    emoji: '🌟',
  };
}
