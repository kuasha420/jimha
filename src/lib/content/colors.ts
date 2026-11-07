export interface ColorContent {
  name: string;
  hex: string;
  emoji: string;
  textColor: string;
  subtitle: string;
}

export const SENSORY_COLORS: ColorContent[] = [
  {
    name: 'Bubblegum Pink',
    hex: '#FF4081',
    emoji: '🌸',
    textColor: '#FFFFFF',
    subtitle: 'Sweet and cheerful Bubblegum Pink! 🌸'
  },
  {
    name: 'Electric Mint',
    hex: '#00E676',
    emoji: '🌿',
    textColor: '#0D0F18',
    subtitle: 'Fresh and lively Electric Mint! 🌿'
  },
  {
    name: 'Sunshine Yellow',
    hex: '#FFD600',
    emoji: '☀️',
    textColor: '#0D0F18',
    subtitle: 'Warm and glowing Sunshine Yellow! ☀️'
  },
  {
    name: 'Cyan Aqua',
    hex: '#00E5FF',
    emoji: '🌊',
    textColor: '#0D0F18',
    subtitle: 'Cool ocean waves of Cyan Aqua! 🌊'
  },
  {
    name: 'Bright Orange',
    hex: '#FF6D00',
    emoji: '🍊',
    textColor: '#FFFFFF',
    subtitle: 'Juicy and energetic Bright Orange! 🍊'
  },
  {
    name: 'Vibrant Lavender',
    hex: '#E040FB',
    emoji: '🔮',
    textColor: '#FFFFFF',
    subtitle: 'Magical and dreamy Vibrant Lavender! 🔮'
  },
  {
    name: 'Royal Violet',
    hex: '#7C4DFF',
    emoji: '🌌',
    textColor: '#FFFFFF',
    subtitle: 'Deep starry skies of Royal Violet! 🌌'
  },
  {
    name: 'Coral Red',
    hex: '#FF5252',
    emoji: '🍎',
    textColor: '#FFFFFF',
    subtitle: 'Bold and playful Coral Red! 🍎'
  },
  {
    name: 'Seafoam Teal',
    hex: '#1DE9B6',
    emoji: '🐬',
    textColor: '#0D0F18',
    subtitle: 'Soothing tropical Seafoam Teal! 🐬'
  }
];

export function getColorContent(query: string): ColorContent | undefined {
  const norm = query.trim().toLowerCase();
  return SENSORY_COLORS.find(
    (c) =>
      c.name.toLowerCase() === norm ||
      c.hex.toLowerCase() === norm ||
      c.emoji === query.trim()
  );
}
