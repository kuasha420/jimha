/**
 * Multi-Touch Multiplexer for Jimha
 *
 * Tracks multiple simultaneous pointer/touch contacts (touchId, x, y),
 * facilitates multi-finger drumming, palm tap detection, and multi-bubble hit-testing.
 */

import type { FloatingBubble } from './particles';

export interface TouchPoint {
  id: number;
  x: number;
  y: number;
  startX: number;
  startY: number;
  startTime: number;
  lastTime: number;
  pointerType: string;
}

export interface HitTestResult {
  hitBubble: FloatingBubble | null;
  remainingBubbles: FloatingBubble[];
}

export interface MultiHitTestResult {
  poppedBubbles: FloatingBubble[];
  remainingBubbles: FloatingBubble[];
}

export interface PointerEventLike {
  pointerId: number;
  clientX: number;
  clientY: number;
  pointerType?: string;
  target?: EventTarget | null;
  preventDefault?: () => void;
  stopPropagation?: () => void;
}

export interface InputMultiplexerOptions {
  hitMarginFactor?: number;
  drumThresholdMs?: number;
  palmTapMinContacts?: number;
  palmTapWindowMs?: number;
  onPointerDown?: (point: TouchPoint, totalActive: number) => void;
  onPointerMove?: (point: TouchPoint, totalActive: number) => void;
  onPointerUp?: (point: TouchPoint, totalActive: number) => void;
  onPalmTap?: (points: TouchPoint[]) => void;
  onDrumBeat?: (point: TouchPoint, cadenceMs: number) => void;
}

/**
 * Tests if a coordinate hits a floating bubble within a generous toddler margin.
 */
export function hitTestBubble(
  point: { x: number; y: number },
  bubble: FloatingBubble,
  marginFactor: number = 1.25
): boolean {
  const dx = point.x - bubble.x;
  const dy = point.y - bubble.y;
  const threshold = bubble.radius * marginFactor;
  return dx * dx + dy * dy <= threshold * threshold;
}

/**
 * Hit tests a single coordinate against a collection of bubbles.
 * Pops the first bubble hit and returns the result.
 */
export function hitTestAndPop(
  point: { x: number; y: number },
  bubbles: FloatingBubble[],
  marginFactor: number = 1.25
): HitTestResult {
  for (let i = 0; i < bubbles.length; i++) {
    const bubble = bubbles[i];
    if (bubble && hitTestBubble(point, bubble, marginFactor)) {
      const remainingBubbles = bubbles.filter((_, idx) => idx !== i);
      return { hitBubble: bubble, remainingBubbles };
    }
  }
  return { hitBubble: null, remainingBubbles: bubbles };
}

/**
 * Hit tests multiple coordinates simultaneously against bubbles (e.g. multi-finger slap).
 * Returns all popped bubbles and remaining unpopped bubbles.
 */
export function multiHitTestAndPop(
  points: Array<{ x: number; y: number }>,
  bubbles: FloatingBubble[],
  marginFactor: number = 1.25
): MultiHitTestResult {
  const poppedBubbles: FloatingBubble[] = [];
  const remainingBubbles: FloatingBubble[] = [];

  for (const bubble of bubbles) {
    const hit = points.some((pt) => hitTestBubble(pt, bubble, marginFactor));
    if (hit) {
      poppedBubbles.push(bubble);
    } else {
      remainingBubbles.push(bubble);
    }
  }

  return { poppedBubbles, remainingBubbles };
}

export class InputMultiplexer {
  private activeTouches: Map<number, TouchPoint> = new Map();
  private recentDowns: Array<{ point: TouchPoint; time: number }> = [];
  private lastDownTime: number = 0;
  private attachedElement: HTMLElement | Window | null = null;
  private boundPointerDown: ((e: PointerEvent) => void) | null = null;
  private boundPointerMove: ((e: PointerEvent) => void) | null = null;
  private boundPointerUp: ((e: PointerEvent) => void) | null = null;
  private boundPointerCancel: ((e: PointerEvent) => void) | null = null;

  public options: Required<InputMultiplexerOptions>;

  constructor(options: InputMultiplexerOptions = {}) {
    this.options = {
      hitMarginFactor: options.hitMarginFactor ?? 1.25,
      drumThresholdMs: options.drumThresholdMs ?? 150,
      palmTapMinContacts: options.palmTapMinContacts ?? 3,
      palmTapWindowMs: options.palmTapWindowMs ?? 100,
      onPointerDown: options.onPointerDown ?? (() => {}),
      onPointerMove: options.onPointerMove ?? (() => {}),
      onPointerUp: options.onPointerUp ?? (() => {}),
      onPalmTap: options.onPalmTap ?? (() => {}),
      onDrumBeat: options.onDrumBeat ?? (() => {}),
    };
  }

  private getRelativeCoords(e: PointerEventLike): { x: number; y: number } {
    if (
      this.attachedElement &&
      'getBoundingClientRect' in this.attachedElement &&
      typeof this.attachedElement.getBoundingClientRect === 'function'
    ) {
      const rect = this.attachedElement.getBoundingClientRect();
      return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    }
    return { x: e.clientX, y: e.clientY };
  }

  public handlePointerDown(e: PointerEventLike, now = performance.now()): TouchPoint {
    const { x, y } = this.getRelativeCoords(e);
    const point: TouchPoint = {
      id: e.pointerId,
      x,
      y,
      startX: x,
      startY: y,
      startTime: now,
      lastTime: now,
      pointerType: e.pointerType || 'touch',
    };

    this.activeTouches.set(e.pointerId, point);

    // Track for palm tap detection (rolling window)
    this.recentDowns.push({ point, time: now });
    const cutoff = now - this.options.palmTapWindowMs;
    this.recentDowns = this.recentDowns.filter((entry) => entry.time >= cutoff);

    if (this.recentDowns.length >= this.options.palmTapMinContacts) {
      const palmTouches = this.recentDowns.map((d) => d.point);
      this.options.onPalmTap(palmTouches);
      this.recentDowns = [];
    }

    // Drumming cadence detection
    if (this.lastDownTime > 0) {
      const cadence = now - this.lastDownTime;
      if (cadence > 0 && cadence <= this.options.drumThresholdMs) {
        this.options.onDrumBeat(point, cadence);
      }
    }
    this.lastDownTime = now;

    this.options.onPointerDown(point, this.activeTouches.size);
    return point;
  }

  public handlePointerMove(e: PointerEventLike, now = performance.now()): TouchPoint | null {
    const existing = this.activeTouches.get(e.pointerId);
    if (!existing) {
      return null;
    }

    const { x, y } = this.getRelativeCoords(e);
    existing.x = x;
    existing.y = y;
    existing.lastTime = now;

    this.options.onPointerMove(existing, this.activeTouches.size);
    return existing;
  }

  public handlePointerUp(e: PointerEventLike, now = performance.now()): TouchPoint | null {
    const existing = this.activeTouches.get(e.pointerId);
    if (existing) {
      const { x, y } = this.getRelativeCoords(e);
      existing.x = x;
      existing.y = y;
      existing.lastTime = now;
      this.activeTouches.delete(e.pointerId);
      this.options.onPointerUp(existing, this.activeTouches.size);
      return existing;
    }
    return null;
  }

  public handlePointerCancel(e: PointerEventLike, now = performance.now()): TouchPoint | null {
    return this.handlePointerUp(e, now);
  }

  public getActiveTouches(): TouchPoint[] {
    return Array.from(this.activeTouches.values());
  }

  public getActiveCount(): number {
    return this.activeTouches.size;
  }

  public clear(): void {
    this.activeTouches.clear();
    this.recentDowns = [];
    this.lastDownTime = 0;
  }

  public attach(element: HTMLElement | Window): void {
    this.detach();
    this.attachedElement = element;

    this.boundPointerDown = (e: PointerEvent) => this.handlePointerDown(e);
    this.boundPointerMove = (e: PointerEvent) => this.handlePointerMove(e);
    this.boundPointerUp = (e: PointerEvent) => this.handlePointerUp(e);
    this.boundPointerCancel = (e: PointerEvent) => this.handlePointerCancel(e);

    element.addEventListener('pointerdown', this.boundPointerDown as EventListener);
    element.addEventListener('pointermove', this.boundPointerMove as EventListener);
    element.addEventListener('pointerup', this.boundPointerUp as EventListener);
    element.addEventListener('pointercancel', this.boundPointerCancel as EventListener);
  }

  public detach(): void {
    if (this.attachedElement) {
      if (this.boundPointerDown) {
        this.attachedElement.removeEventListener(
          'pointerdown',
          this.boundPointerDown as EventListener
        );
      }
      if (this.boundPointerMove) {
        this.attachedElement.removeEventListener(
          'pointermove',
          this.boundPointerMove as EventListener
        );
      }
      if (this.boundPointerUp) {
        this.attachedElement.removeEventListener('pointerup', this.boundPointerUp as EventListener);
      }
      if (this.boundPointerCancel) {
        this.attachedElement.removeEventListener(
          'pointercancel',
          this.boundPointerCancel as EventListener
        );
      }
      this.attachedElement = null;
    }
    this.clear();
  }
}
