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

export const ALPHABET_COMPANIONS: Record<string, [string, string]> = {
  A: ['🍎', 'Apple'],
  B: ['🦋', 'Butterfly'],
  C: ['🐱', 'Cat'],
  D: ['🐶', 'Dog'],
  E: ['🐘', 'Elephant'],
  F: ['🌸', 'Flower'],
  G: ['🎸', 'Guitar'],
  H: ['💖', 'Jim Heart (Easter Egg! 💖)'], // The legendary voice-dictation spark!
  I: ['🍦', 'Ice Cream'],
  J: ['👑', 'JimHa! ✨'], // The queen herself!
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
  return palette[idx];
}

export function resolveKeyDisplay(rawKey: string): { title: string; subtitle: string; emoji: string } {
  const text = rawKey.trim().toUpperCase();

  if (text && ALPHABET_COMPANIONS[text]) {
    const [emoji, word] = ALPHABET_COMPANIONS[text];
    return {
      title: text,
      subtitle: `${text} is for ${word} ${emoji}`,
      emoji
    };
  }

  if (text && /^\d$/.test(text)) {
    const val = parseInt(text, 10);
    const stars = '⭐'.repeat(Math.max(1, Math.min(val, 10)));
    return {
      title: text,
      subtitle: `Number ${val}! ${stars}`,
      emoji: '🔢'
    };
  }

  switch (text) {
    case ' ':
    case 'SPACE':
      return {
        title: 'SPACE',
        subtitle: '🌟 COSMIC SUPERNOVA! 🌟',
        emoji: '✨'
      };
    case 'ENTER':
      return {
        title: 'ENTER',
        subtitle: '🎉 PARTY TIME CELEBRATION! 🎉',
        emoji: '🎈'
      };
    case 'BACKSPACE':
      return {
        title: 'POP!',
        subtitle: '🫧 BUBBLE POP! 🫧',
        emoji: '🫧'
      };
    case 'ARROWUP':
    case 'UP':
      return {
        title: 'UP ⬆️',
        subtitle: '🚀 ROCKETING TO THE STARS!',
        emoji: '🌌'
      };
    case 'ARROWDOWN':
    case 'DOWN':
      return {
        title: 'DOWN ⬇️',
        subtitle: '🌊 DIVING DEEP INTO THE OCEAN!',
        emoji: '🐬'
      };
    case 'ARROWLEFT':
    case 'LEFT':
      return {
        title: 'LEFT ⬅️',
        subtitle: '🌪️ SWISHING TO THE LEFT!',
        emoji: '💫'
      };
    case 'ARROWRIGHT':
    case 'RIGHT':
      return {
        title: 'RIGHT ➡️',
        subtitle: '⚡ DASHING TO THE RIGHT!',
        emoji: '⚡'
      };
    default:
      return {
        title: text || 'KEY',
        subtitle: '💖 YOU ARE AWESOME JIMHA! 💖',
        emoji: '🌟'
      };
  }
}
