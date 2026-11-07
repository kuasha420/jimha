import { describe, it, expect, vi } from 'vitest';
import {
  InputMultiplexer,
  hitTestBubble,
  hitTestAndPop,
  multiHitTestAndPop,
  type PointerEventLike,
} from './input-multiplexer';
import type { FloatingBubble } from './particles';

describe('InputMultiplexer Unit & Contract Tests', () => {
  it('tracks single pointer down, move, and up lifecycles', () => {
    const onDown = vi.fn();
    const onMove = vi.fn();
    const onUp = vi.fn();

    const mux = new InputMultiplexer({
      onPointerDown: onDown,
      onPointerMove: onMove,
      onPointerUp: onUp,
    });

    const event1: PointerEventLike = {
      pointerId: 1,
      clientX: 100,
      clientY: 150,
      pointerType: 'touch',
    };

    const pt1 = mux.handlePointerDown(event1, 1000);
    expect(pt1.id).toBe(1);
    expect(pt1.x).toBe(100);
    expect(pt1.y).toBe(150);
    expect(mux.getActiveCount()).toBe(1);
    expect(onDown).toHaveBeenCalledWith(pt1, 1);

    // Pointer move
    const event1Move: PointerEventLike = {
      pointerId: 1,
      clientX: 120,
      clientY: 160,
    };
    const moveRes = mux.handlePointerMove(event1Move, 1016);
    expect(moveRes?.x).toBe(120);
    expect(moveRes?.y).toBe(160);
    expect(onMove).toHaveBeenCalledWith(moveRes, 1);

    // Pointer up
    const upRes = mux.handlePointerUp(event1Move, 1050);
    expect(upRes?.id).toBe(1);
    expect(mux.getActiveCount()).toBe(0);
    expect(onUp).toHaveBeenCalledWith(upRes, 0);
  });

  it('tracks multiple simultaneous touches (multi-finger drumming)', () => {
    const mux = new InputMultiplexer();

    mux.handlePointerDown({ pointerId: 10, clientX: 50, clientY: 50 }, 1000);
    mux.handlePointerDown({ pointerId: 20, clientX: 100, clientY: 100 }, 1020);
    mux.handlePointerDown({ pointerId: 30, clientX: 150, clientY: 150 }, 1040);

    expect(mux.getActiveCount()).toBe(3);
    const active = mux.getActiveTouches();
    expect(active.map((t) => t.id)).toEqual([10, 20, 30]);

    // Release middle pointer
    mux.handlePointerUp({ pointerId: 20, clientX: 100, clientY: 100 }, 1100);
    expect(mux.getActiveCount()).toBe(2);
    expect(mux.getActiveTouches().map((t) => t.id)).toEqual([10, 30]);
  });

  it('detects palm tap when >= 3 contacts land within window', () => {
    const onPalm = vi.fn();
    const mux = new InputMultiplexer({
      palmTapMinContacts: 3,
      palmTapWindowMs: 80,
      onPalmTap: onPalm,
    });

    // 3 contacts within 40ms -> Palm tap!
    mux.handlePointerDown({ pointerId: 1, clientX: 200, clientY: 200 }, 1000);
    mux.handlePointerDown({ pointerId: 2, clientX: 220, clientY: 210 }, 1020);
    expect(mux.getActiveCount()).toBe(2);
    expect(onPalm).not.toHaveBeenCalled();

    mux.handlePointerDown({ pointerId: 3, clientX: 240, clientY: 230 }, 1040);
    expect(mux.getActiveCount()).toBe(3);
    expect(onPalm).toHaveBeenCalledTimes(1);
    const touchesPassed = onPalm.mock.calls[0][0];
    expect(touchesPassed.length).toBe(3);
    expect(touchesPassed[0].id).toBe(1);
    expect(touchesPassed[1].id).toBe(2);
    expect(touchesPassed[2].id).toBe(3);
  });

  it('does not trigger palm tap when contacts are too far apart in time', () => {
    const onPalm = vi.fn();
    const mux = new InputMultiplexer({
      palmTapMinContacts: 3,
      palmTapWindowMs: 80,
      onPalmTap: onPalm,
    });

    mux.handlePointerDown({ pointerId: 1, clientX: 200, clientY: 200 }, 1000);
    mux.handlePointerDown({ pointerId: 2, clientX: 220, clientY: 210 }, 1150);
    mux.handlePointerDown({ pointerId: 3, clientX: 240, clientY: 230 }, 1300);

    expect(mux.getActiveCount()).toBe(3);
    expect(mux.getActiveTouches().map((t) => t.id)).toEqual([1, 2, 3]);
    expect(onPalm).not.toHaveBeenCalled();
  });

  it('detects drumming cadence on rapid sequential taps', () => {
    const onDrum = vi.fn();
    const mux = new InputMultiplexer({
      drumThresholdMs: 120,
      onDrumBeat: onDrum,
    });

    mux.handlePointerDown({ pointerId: 1, clientX: 100, clientY: 100 }, 1000);
    expect(mux.getActiveCount()).toBe(1);
    expect(onDrum).not.toHaveBeenCalled();

    // Second tap 80ms later -> drum beat!
    mux.handlePointerDown({ pointerId: 2, clientX: 150, clientY: 100 }, 1080);
    expect(mux.getActiveCount()).toBe(2);
    expect(onDrum).toHaveBeenCalledTimes(1);
    const drumCalls = onDrum.mock.calls;
    expect(drumCalls[0][0].id).toBe(2);
    expect(drumCalls[0][1]).toBe(80);

    // Third tap 90ms later -> drum beat!
    mux.handlePointerDown({ pointerId: 3, clientX: 200, clientY: 100 }, 1170);
    expect(mux.getActiveCount()).toBe(3);
    expect(onDrum).toHaveBeenCalledTimes(2);
    expect(drumCalls[1][0].id).toBe(3);
    expect(drumCalls[1][1]).toBe(90);
  });

  describe('Bubble Hit-Testing & Multi-Pop', () => {
    const mockBubbles: FloatingBubble[] = [
      { x: 100, y: 100, vx: 0, vy: 0, radius: 20, color: '#FF4081', life: 1.0 },
      { x: 300, y: 300, vx: 0, vy: 0, radius: 25, color: '#00E5FF', life: 1.0 },
      { x: 500, y: 500, vx: 0, vy: 0, radius: 30, color: '#FFD600', life: 1.0 },
    ];

    it('accurately tests single bubble collision with margin factor', () => {
      const bubble = mockBubbles[0];
      // Direct center hit
      expect(hitTestBubble({ x: 100, y: 100 }, bubble)).toBe(true);
      // Within radius (20px) + margin (1.25 -> 25px)
      expect(hitTestBubble({ x: 122, y: 100 }, bubble)).toBe(true);
      // Outside margin
      expect(hitTestBubble({ x: 140, y: 100 }, bubble)).toBe(false);
    });

    it('pops single bubble on touch and retains remaining bubbles', () => {
      const result = hitTestAndPop({ x: 305, y: 305 }, mockBubbles);
      expect(result.hitBubble).toBeDefined();
      expect(result.hitBubble?.color).toBe('#00E5FF');
      expect(result.remainingBubbles.length).toBe(2);
      expect(result.remainingBubbles.map((b) => b.color)).toEqual(['#FF4081', '#FFD600']);
    });

    it('returns null and keeps all bubbles when hit misses', () => {
      const result = hitTestAndPop({ x: 999, y: 999 }, mockBubbles);
      expect(result.hitBubble).toBeNull();
      expect(result.remainingBubbles.length).toBe(3);
    });

    it('supports simultaneous multi-finger bubble pop', () => {
      const points = [
        { x: 102, y: 98 }, // Hits bubble 0 (#FF4081)
        { x: 501, y: 502 }, // Hits bubble 2 (#FFD600)
      ];

      const result = multiHitTestAndPop(points, mockBubbles);
      expect(result.poppedBubbles.length).toBe(2);
      expect(result.poppedBubbles.map((b) => b.color)).toEqual(['#FF4081', '#FFD600']);
      expect(result.remainingBubbles.length).toBe(1);
      expect(result.remainingBubbles[0].color).toBe('#00E5FF');
    });
  });

  it('attaches and detaches cleanly to DOM target without leaks', () => {
    const mux = new InputMultiplexer();
    const div = document.createElement('div');
    const addSpy = vi.spyOn(div, 'addEventListener');
    const removeSpy = vi.spyOn(div, 'removeEventListener');

    expect(mux.getActiveCount()).toBe(0);
    mux.attach(div);
    expect(addSpy).toHaveBeenCalledWith('pointerdown', expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith('pointermove', expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith('pointerup', expect.any(Function));
    expect(addSpy).toHaveBeenCalledWith('pointercancel', expect.any(Function));

    mux.detach();
    expect(mux.getActiveCount()).toBe(0);
    expect(mux.getActiveTouches()).toEqual([]);
    expect(removeSpy).toHaveBeenCalledWith('pointerdown', expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith('pointermove', expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith('pointerup', expect.any(Function));
    expect(removeSpy).toHaveBeenCalledWith('pointercancel', expect.any(Function));
  });
});
