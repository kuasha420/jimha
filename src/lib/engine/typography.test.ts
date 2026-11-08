import { describe, it, expect } from 'vitest';
import {
  computeBaseFontSizes,
  computeSafeViewportCeilings,
  clampFontSizeToCeiling,
  MAX_SPRING_BOUNCE_SCALE,
} from './typography';

describe('Responsive Typography & Safe Handheld Viewport Bounds', () => {
  const STEAM_DECK_VIEWPORT = { width: 1280, height: 800 };
  const FULL_HD_VIEWPORT = { width: 1920, height: 1080 };

  it('calculates baseline font sizes with length damping on Steam Deck (1280x800)', () => {
    // Single letter "A"
    const singleLetter = computeBaseFontSizes(STEAM_DECK_VIEWPORT, 'A');
    expect(singleLetter.fontSize).toBe(208); // 800 * 0.26
    expect(singleLetter.subFontSize).toBe(36); // 800 * 0.045

    // Word "SPACE" (5 chars)
    const spaceKey = computeBaseFontSizes(STEAM_DECK_VIEWPORT, 'SPACE');
    expect(spaceKey.fontSize).toBeLessThan(singleLetter.fontSize);
    expect(spaceKey.fontSize).toBeGreaterThanOrEqual(150);

    // Long phrase "👑 30 LIVES GRANTED! 🚀💖✨" (27 chars)
    const longTitle = computeBaseFontSizes(STEAM_DECK_VIEWPORT, '👑 30 LIVES GRANTED! 🚀💖✨');
    expect(longTitle.fontSize).toBeLessThan(100);
    expect(longTitle.fontSize).toBeGreaterThanOrEqual(28);
  });

  it('guarantees safe viewport ceilings that never clip at peak spring overshoot on Steam Deck', () => {
    const { maxAllowedTitleWidth, maxAllowedBadgeWidth, maxAllowedSubWidth, badgeY } =
      computeSafeViewportCeilings(STEAM_DECK_VIEWPORT, 120);

    // Title at peak spring bounce (1.28 - 1.30x) must not exceed 80% screen width
    const peakTitleWidth = maxAllowedTitleWidth * MAX_SPRING_BOUNCE_SCALE;
    expect(peakTitleWidth).toBeCloseTo(STEAM_DECK_VIEWPORT.width * 0.8, 1);
    expect(peakTitleWidth).toBeLessThan(STEAM_DECK_VIEWPORT.width);

    // Badge at peak spring bounce must not exceed 84% screen width
    const peakBadgeWidth = maxAllowedBadgeWidth * MAX_SPRING_BOUNCE_SCALE;
    expect(peakBadgeWidth).toBeCloseTo(STEAM_DECK_VIEWPORT.width * 0.84, 1);
    expect(peakBadgeWidth).toBeLessThan(STEAM_DECK_VIEWPORT.width);

    // Subtitle text fits inside badge with padding
    expect(maxAllowedSubWidth + 52).toBeCloseTo(maxAllowedBadgeWidth, 1);

    // Badge vertical offset is below title
    expect(badgeY).toBeGreaterThan(0);
    // At centerStageY = 400, badge bottom at peak scale is well above bottom of screen (800)
    const peakBadgeBottom = 400 + (badgeY + 25) * 1.28;
    expect(peakBadgeBottom).toBeLessThan(STEAM_DECK_VIEWPORT.height - 50);
  });

  it('scales down font size when measured bounds exceed safe width ceiling', () => {
    const currentSize = 120;
    const maxAllowedWidth = 750;

    // Under ceiling: keeps size
    expect(clampFontSizeToCeiling(currentSize, 600, maxAllowedWidth, 18)).toBe(120);

    // Over ceiling: scales down proportionally
    const scaledSize = clampFontSizeToCeiling(currentSize, 1000, maxAllowedWidth, 18);
    expect(scaledSize).toBe(90); // 120 * (750 / 1000)

    // Severe overflow: respects minimum font size
    const clampedMin = clampFontSizeToCeiling(currentSize, 8000, maxAllowedWidth, 18);
    expect(clampedMin).toBe(18);
  });

  it('guarantees safe margins on 1080p desktop display', () => {
    const ceilings = computeSafeViewportCeilings(FULL_HD_VIEWPORT, 200);
    const peakBadgeWidth = ceilings.maxAllowedBadgeWidth * MAX_SPRING_BOUNCE_SCALE;
    expect(peakBadgeWidth).toBeLessThan(FULL_HD_VIEWPORT.width);
    expect(FULL_HD_VIEWPORT.width - peakBadgeWidth).toBeGreaterThan(300); // at least 150px per side
  });
});
