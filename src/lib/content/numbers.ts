export interface NumberContent {
  number: number;
  title: string;
  word: string;
  emoji: string;
  starCount: number;
  subtitle: string;
  color: string;
}

export const NUMBER_WORDS = [
  'Zero',
  'One',
  'Two',
  'Three',
  'Four',
  'Five',
  'Six',
  'Seven',
  'Eight',
  'Nine',
  'Ten',
  'Eleven',
  'Twelve',
  'Thirteen',
  'Fourteen',
  'Fifteen',
  'Sixteen',
  'Seventeen',
  'Eighteen',
  'Nineteen',
  'Twenty',
] as const;

export const NUMBER_COLORS = [
  '#00E5FF', // 0 - Cyan Aqua
  '#FF4081', // 1 - Bubblegum Pink
  '#00E676', // 2 - Electric Mint
  '#FFD600', // 3 - Sunshine Yellow
  '#FF6D00', // 4 - Bright Orange
  '#E040FB', // 5 - Vibrant Lavender
  '#7C4DFF', // 6 - Royal Violet
  '#FF5252', // 7 - Coral Red
  '#1DE9B6', // 8 - Seafoam Teal
  '#FF4081', // 9 - Pink
  '#FFD600', // 10 - Golden Sun
  '#00E5FF', // 11 - Aqua
  '#00E676', // 12 - Mint
  '#FF6D00', // 13 - Orange
  '#E040FB', // 14 - Lavender
  '#7C4DFF', // 15 - Violet
  '#FF5252', // 16 - Coral
  '#1DE9B6', // 17 - Teal
  '#FFD600', // 18 - Gold
  '#FF4081', // 19 - Rose
  '#00E5FF', // 20 - Diamond Blue
] as const;

export function getStarString(count: number): string {
  if (count <= 0) return '✨';
  return '⭐'.repeat(Math.min(count, 20));
}

export const NUMBERS_0_20: NumberContent[] = Array.from({ length: 21 }, (_, i) => {
  const word = NUMBER_WORDS[i];
  const color = NUMBER_COLORS[i % NUMBER_COLORS.length];
  const starCount = i;
  const stars = getStarString(i);
  const subtitle =
    i === 0
      ? 'Zero sparkle stars! ✨'
      : i === 1
        ? '1 Shining Star! ⭐'
        : `${i} Sparkling Stars! ${stars}`;

  return {
    number: i,
    title: String(i),
    word,
    emoji: i === 0 ? '✨' : '⭐',
    starCount,
    subtitle,
    color,
  };
});

export function getNumberContent(n: number): NumberContent | undefined {
  if (n >= 0 && n <= 20) {
    return NUMBERS_0_20[n];
  }
  return undefined;
}
