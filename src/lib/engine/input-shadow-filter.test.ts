import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { InputShadowFilter } from './input-shadow-filter';

describe('InputShadowFilter (Steam Desktop Input Deduplication)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('identifies synthetic Enter as shadow when Gamepad A is pressed', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });
    const t0 = 1000;

    filter.recordButtonDown('A', t0);

    // Enter arriving 20ms later is recognized as shadow
    expect(filter.isSyntheticKeyboardShadow('Enter', ['A'], t0 + 20)).toBe(true);
    expect(filter.isSyntheticKeyboardShadow('Return', ['A'], t0 + 20)).toBe(true);

    // Literal 'a' or 'A' is also recognized as shadow
    expect(filter.isSyntheticKeyboardShadow('a', ['A'], t0 + 20)).toBe(true);
    expect(filter.isSyntheticKeyboardShadow('A', ['A'], t0 + 20)).toBe(true);
  });

  it('identifies synthetic Escape as shadow when Gamepad B is pressed', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });
    const t0 = 1000;

    filter.recordButtonDown('B', t0);

    expect(filter.isSyntheticKeyboardShadow('Escape', ['B'], t0 + 15)).toBe(true);
    expect(filter.isSyntheticKeyboardShadow('Esc', ['B'], t0 + 15)).toBe(true);
    expect(filter.isSyntheticKeyboardShadow('b', ['B'], t0 + 15)).toBe(true);
  });

  it('identifies D-Pad arrows as shadows when D-Pad is pressed', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });
    const t0 = 1000;

    filter.recordButtonDown('UP', t0);
    expect(filter.isSyntheticKeyboardShadow('ArrowUp', ['UP'], t0 + 10)).toBe(true);
    expect(filter.isSyntheticKeyboardShadow('ArrowDown', ['UP'], t0 + 10)).toBe(false);

    filter.recordButtonDown('DOWN', t0 + 50);
    expect(filter.isSyntheticKeyboardShadow('ArrowDown', ['DOWN'], t0 + 60)).toBe(true);
  });

  it('identifies SELECT and START shadows (Tab, Escape, Enter)', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });
    const t0 = 1000;

    filter.recordButtonDown('SELECT', t0);
    expect(filter.isSyntheticKeyboardShadow('Tab', ['SELECT'], t0 + 10)).toBe(true);
    expect(filter.isSyntheticKeyboardShadow('Escape', ['SELECT'], t0 + 10)).toBe(true);

    filter.recordButtonDown('START', t0);
    expect(filter.isSyntheticKeyboardShadow('Enter', ['START'], t0 + 10)).toBe(true);
  });

  it('allows real physical keyboard inputs through when no gamepad button is active', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });

    // No gamepad button pressed
    expect(filter.isSyntheticKeyboardShadow('Enter', [], 2000)).toBe(false);
    expect(filter.isSyntheticKeyboardShadow('Escape', [], 2000)).toBe(false);
    expect(filter.isSyntheticKeyboardShadow('c', [], 2000)).toBe(false);
    expect(filter.isSyntheticKeyboardShadow('d', [], 2000)).toBe(false);
    expect(filter.isSyntheticKeyboardShadow('ArrowUp', [], 2000)).toBe(false);
  });

  it('allows keyboard inputs after button release and window expiration', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });
    const t0 = 1000;

    filter.recordButtonDown('A', t0);
    filter.recordButtonUp('A');

    // Within window: still filtered as shadow
    expect(filter.isSyntheticKeyboardShadow('Enter', [], t0 + 50)).toBe(true);

    // After window expiration (160ms > 150ms): allowed through
    expect(filter.isSyntheticKeyboardShadow('Enter', [], t0 + 160)).toBe(false);
  });

  it('resets cleanly with clear()', () => {
    const filter = new InputShadowFilter({ windowMs: 150 });
    filter.recordButtonDown('A', 1000);
    filter.clear();

    expect(filter.isSyntheticKeyboardShadow('Enter', [], 1010)).toBe(false);
  });

  describe('Pending Shadow Buffer (Race Condition Prevention)', () => {
    it('drops synthetic Enter when controller button A lands within 55ms', () => {
      const filter = new InputShadowFilter({ windowMs: 350, pendingDelayMs: 55 });
      const dispatchSpy = vi.fn();

      // 1. Enter arrives first from Steam Desktop profile
      const handled = filter.filterOrBufferKey('Enter', {
        hasGamepad: true,
        onDispatch: dispatchSpy,
        now: 1000,
      });

      expect(handled).toBe(true);
      expect(dispatchSpy).not.toHaveBeenCalled();

      // 2. 10ms later, Gamepad API detects button A
      filter.recordButtonDown('A', 1010);

      // 3. Time advances past the 55ms buffer window
      vi.advanceTimersByTime(100);

      // 4. Dispatch MUST NOT have been called (synthetic Enter cancelled!)
      expect(dispatchSpy).not.toHaveBeenCalled();
    });

    it('drops synthetic Escape when controller button B lands within 55ms', () => {
      const filter = new InputShadowFilter({ windowMs: 350, pendingDelayMs: 55 });
      const dispatchSpy = vi.fn();

      const handled = filter.filterOrBufferKey('Escape', {
        hasGamepad: true,
        onDispatch: dispatchSpy,
        now: 1000,
      });

      expect(handled).toBe(true);
      filter.recordButtonDown('B', 1015);
      vi.advanceTimersByTime(100);

      expect(dispatchSpy).not.toHaveBeenCalled();
    });

    it('dispatches non-shadow keys immediately with 0ms delay even when gamepad is connected', () => {
      const filter = new InputShadowFilter();
      const dispatchSpy = vi.fn();

      const handled = filter.filterOrBufferKey('k', {
        hasGamepad: true,
        onDispatch: dispatchSpy,
      });

      expect(handled).toBe(false);
      // Caller dispatches immediately when handled === false
    });

    it('dispatches shadow keys after delay if no controller button is pressed', () => {
      const filter = new InputShadowFilter({ pendingDelayMs: 55 });
      const dispatchSpy = vi.fn();

      const handled = filter.filterOrBufferKey('Enter', {
        hasGamepad: true,
        onDispatch: dispatchSpy,
      });

      expect(handled).toBe(true);
      expect(dispatchSpy).not.toHaveBeenCalled();

      // After buffer expires with no controller button, dispatch is executed
      vi.advanceTimersByTime(60);
      expect(dispatchSpy).toHaveBeenCalledTimes(1);
    });

    it('dispatches shadow keys immediately if no gamepad is connected at all', () => {
      const filter = new InputShadowFilter();
      const dispatchSpy = vi.fn();

      const handled = filter.filterOrBufferKey('Enter', {
        hasGamepad: false,
        onDispatch: dispatchSpy,
      });

      expect(handled).toBe(false);
      expect(dispatchSpy).not.toHaveBeenCalled(); // Handled false -> caller executes immediately
    });
  });
});
