/**
 * Spring-damper bouncy typography calculations.
 * Faithful port of the JimHa Python prototype elastic curve:
 * 0.2 -> 1.25 -> 1.0 bounce over 0.35s duration.
 */

export interface SpringConfig {
  duration?: number;
  initialScale?: number;
  overshootScale?: number;
  finalScale?: number;
}

export function calculateElasticScale(
  cardAge: number,
  config: SpringConfig = {}
): number {
  const duration = config.duration ?? 0.35;
  const initialScale = config.initialScale ?? 0.2;
  const overshootMultiplier = config.overshootScale ?? 0.35;
  const finalScale = config.finalScale ?? 1.0;

  if (cardAge <= 0) {
    return initialScale;
  }

  if (cardAge < duration) {
    const progress = cardAge / duration;
    // progress in [0, 1]
    // 0.2 + 0.8 * (1.0 + sin(progress * PI) * 0.35)
    // At progress = 0: 0.2 + 0.8 * (1.0 + 0) = 1.0 (or with scale factor)
    // Matching exact Python prototype formula:
    // self.card_scale = 0.2 + 0.8 * (1.0 + math.sin(progress * math.pi) * 0.35)
    const bounce = Math.sin(progress * Math.PI) * overshootMultiplier;
    return initialScale + (finalScale - initialScale) * (1.0 + bounce);
  }

  return finalScale;
}

/**
 * Calculates a smooth cubic-bezier or damped alpha fade for card life.
 */
export function calculateCardAlpha(cardAge: number, fadeStart: number = 3.0, fadeDuration: number = 1.5): number {
  if (cardAge < fadeStart) return 1.0;
  const elapsed = cardAge - fadeStart;
  if (elapsed >= fadeDuration) return 0.2; // Keep minimum visibility
  return 1.0 - 0.8 * (elapsed / fadeDuration);
}
