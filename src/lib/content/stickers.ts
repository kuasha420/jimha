export interface StickerBadge {
  id: string;
  title: string;
  emoji: string;
  description: string;
  hint: string;
  accentColor: string;
}

export const STICKERS: StickerBadge[] = [
  {
    id: 'first_spark',
    title: 'First Spark ✨',
    emoji: '✨',
    description: 'Pressed a magical key or popped your first bubble!',
    hint: 'Press any key or pop a bubble',
    accentColor: '#FF4081'
  },
  {
    id: 'bubble_popper',
    title: 'Bubble Master 🫧',
    emoji: '🫧',
    description: 'Popped 10 or more liquid bubbles!',
    hint: 'Pop 10 floating bubbles',
    accentColor: '#00E5FF'
  },
  {
    id: 'jimha_crown',
    title: 'Queen Jimha 👑',
    emoji: '👑',
    description: 'Honored Queen Jimha by pressing J!',
    hint: 'Press the letter J',
    accentColor: '#FFD600'
  },
  {
    id: 'jim_heart',
    title: 'Jim Heart ❤️',
    emoji: '❤️',
    description: 'Born from a whisper across the Knot mesh: a serendipitous voice-dictation spark that started Jimha\'s magical playground.',
    hint: 'Listen closely to the heartbeat of the game...',
    accentColor: '#E040FB'
  },
  {
    id: 'star_counter',
    title: 'Star Counter ⭐',
    emoji: '⭐',
    description: 'Counted the twinkling stars!',
    hint: 'Press numbers to count',
    accentColor: '#FFD600'
  },
  {
    id: 'rainbow_explorer',
    title: 'Rainbow Explorer 🌈',
    emoji: '🌈',
    description: 'Discovered the vibrant rainbow colors!',
    hint: 'Press the letter R',
    accentColor: '#00E676'
  },
  {
    id: 'konami_champion',
    title: 'Konami Champion 🎮',
    emoji: '🎮',
    description: 'Executed the legendary arcade cheat code!',
    hint: '↑ ↑ ↓ ↓ ← → ← → B A',
    accentColor: '#7C4DFF'
  }
];

export function getStickerById(id: string): StickerBadge | undefined {
  return STICKERS.find((s) => s.id === id);
}
