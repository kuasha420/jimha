/**
 * Responsive Typography and Safe Handheld Viewport Bounds Engine
 *
 * Enforces strict width and height ceilings so titles, subtitles, and badges
 * remain completely on-screen with generous safety margins, even during peak
 * elastic spring scale overshoot (1.28x - 1.30x) on compact screens like the Steam Deck.
 */

export const MAX_SPRING_BOUNCE_SCALE = 1.3;

export interface ViewportDimensions {
  width: number;
  height: number;
}

export interface ResponsiveTextMetrics {
  fontSize: number;
  subFontSize: number;
  maxAllowedTitleWidth: number;
  maxAllowedSubWidth: number;
  maxAllowedBadgeWidth: number;
  badgeY: number;
}

/**
 * Computes baseline responsive font sizes scaled to viewport minimum dimension,
 * applying square-root damping for multi-character words.
 */
export function computeBaseFontSizes(
  viewport: ViewportDimensions,
  title: string
): { fontSize: number; subFontSize: number } {
  const minDim = Math.min(viewport.width, viewport.height);
  let fontSize = Math.max(48, Math.round(minDim * 0.26));
  const subFontSize = Math.max(16, Math.round(minDim * 0.045));

  if (title.length > 2) {
    const lenRatio = Math.max(1, title.length / 3);
    fontSize = Math.max(28, Math.round(fontSize / Math.sqrt(lenRatio)));
  }

  return { fontSize, subFontSize };
}

/**
 * Computes maximum allowed dimensions inside stageContainer such that
 * even at peak elastic overshoot (MAX_SPRING_BOUNCE_SCALE = 1.30),
 * title occupies <= 80% screen width and badge occupies <= 84% screen width.
 */
export function computeSafeViewportCeilings(
  viewport: ViewportDimensions,
  fontSize: number
): {
  maxAllowedTitleWidth: number;
  maxAllowedBadgeWidth: number;
  maxAllowedSubWidth: number;
  badgeY: number;
} {
  const maxAllowedTitleWidth = (viewport.width * 0.8) / MAX_SPRING_BOUNCE_SCALE;
  const maxAllowedBadgeWidth = (viewport.width * 0.84) / MAX_SPRING_BOUNCE_SCALE;
  const maxAllowedSubWidth = Math.max(80, maxAllowedBadgeWidth - 52);
  const badgeY = fontSize * 0.55 + 35;

  return {
    maxAllowedTitleWidth,
    maxAllowedBadgeWidth,
    maxAllowedSubWidth,
    badgeY,
  };
}

/**
 * Scales down font size proportionally if measured bounds exceed the safe ceiling.
 */
export function clampFontSizeToCeiling(
  currentFontSize: number,
  measuredWidth: number,
  maxAllowedWidth: number,
  minFontSize: number = 18
): number {
  if (measuredWidth > maxAllowedWidth && measuredWidth > 0) {
    const scaleDown = maxAllowedWidth / measuredWidth;
    return Math.max(minFontSize, Math.floor(currentFontSize * scaleDown));
  }
  return currentFontSize;
}
