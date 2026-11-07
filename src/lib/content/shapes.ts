export type ShapeType = 'circle' | 'square' | 'triangle' | 'star' | 'heart' | 'diamond' | 'hexagon';

export interface ShapeContent {
  id: ShapeType;
  name: string;
  emoji: string;
  particleShape: 'circle' | 'square' | 'triangle' | 'star' | 'heart' | 'confetti';
  color: string;
  subtitle: string;
}

export const SENSORY_SHAPES: ShapeContent[] = [
  {
    id: 'circle',
    name: 'Circle',
    emoji: '🔴',
    particleShape: 'circle',
    color: '#00E5FF',
    subtitle: 'Round and smooth like a bubble! 🫧',
  },
  {
    id: 'square',
    name: 'Square',
    emoji: '🟧',
    particleShape: 'square',
    color: '#FF6D00',
    subtitle: 'Four equal sides and four corners! 📦',
  },
  {
    id: 'triangle',
    name: 'Triangle',
    emoji: '🔺',
    particleShape: 'triangle',
    color: '#FFD600',
    subtitle: 'Three sharp points reaching high! 📐',
  },
  {
    id: 'star',
    name: 'Star',
    emoji: '⭐',
    particleShape: 'star',
    color: '#FF4081',
    subtitle: 'Five twinkling points shining bright! ✨',
  },
  {
    id: 'heart',
    name: 'Heart',
    emoji: '💖',
    particleShape: 'heart',
    color: '#E040FB',
    subtitle: 'Full of warm love and joy! 💖',
  },
  {
    id: 'diamond',
    name: 'Diamond',
    emoji: '💎',
    particleShape: 'confetti',
    color: '#00E676',
    subtitle: 'Glittering crystal gem! 💎',
  },
  {
    id: 'hexagon',
    name: 'Hexagon',
    emoji: '⬡',
    particleShape: 'circle',
    color: '#7C4DFF',
    subtitle: 'Six sweet sides like a honeycomb! 🐝',
  },
];

export function getShapeContent(idOrName: string): ShapeContent | undefined {
  const norm = idOrName.trim().toLowerCase();
  return SENSORY_SHAPES.find((shape) => shape.id === norm || shape.name.toLowerCase() === norm);
}
