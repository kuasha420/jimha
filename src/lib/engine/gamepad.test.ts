import { describe, it, expect, vi } from 'vitest';
import { GamepadManager, type GamepadLike } from './gamepad';
import { RekkaBuffer, KONAMI_SEQUENCE } from './rekka';

describe('GamepadManager Unit & Contract Tests', () => {
  function createMockGamepad(
    index: number = 0,
    buttonsPressed: number[] = [],
    axes: number[] = [0, 0]
  ): GamepadLike {
    const buttons = Array.from({ length: 17 }, (_, idx) => ({
      pressed: buttonsPressed.includes(idx),
      value: buttonsPressed.includes(idx) ? 1.0 : 0.0,
    }));

    return {
      index,
      id: 'Steam Deck Controller (STANDARD GAMEPAD)',
      connected: true,
      mapping: 'standard',
      buttons,
      axes,
    };
  }

  it('triggers onConnected and detects button down edges', () => {
    const onConnected = vi.fn();
    const onButtonDown = vi.fn();
    const onButtonUp = vi.fn();

    const gm = new GamepadManager({
      onConnected,
      onButtonDown,
      onButtonUp,
    });

    // Frame 1: Gamepad appears with no buttons pressed
    gm.poll([createMockGamepad(0, [])]);
    expect(gm.isConnected(0)).toBe(true);
    expect(gm.getConnectedCount()).toBe(1);
    expect(gm.isButtonPressed(0, 'A')).toBe(false);
    expect(onConnected).toHaveBeenCalledWith(0, expect.stringContaining('Steam Deck'));
    expect(onButtonDown).not.toHaveBeenCalled();

    // Frame 2: Button A with index 0 is pressed
    gm.poll([createMockGamepad(0, [0])]);
    expect(gm.isButtonPressed(0, 'A')).toBe(true);
    expect(onButtonDown).toHaveBeenCalledTimes(1);
    const eventDown = onButtonDown.mock.calls[0][0];
    expect(eventDown.buttonId).toBe('A');
    expect(eventDown.pressed).toBe(true);
    expect(eventDown.value).toBe(1.0);
    expect(eventDown.meta.label).toBe('A Button');
    expect(eventDown.meta.emoji).toBe('🟢');

    // Frame 3: Button A still held down -> edge-triggered, no duplicate onButtonDown
    gm.poll([createMockGamepad(0, [0])]);
    expect(gm.isButtonPressed(0, 'A')).toBe(true);
    expect(onButtonDown).toHaveBeenCalledTimes(1);

    // Frame 4: Button A released -> onButtonUp
    gm.poll([createMockGamepad(0, [])]);
    expect(gm.isButtonPressed(0, 'A')).toBe(false);
    expect(onButtonUp).toHaveBeenCalledTimes(1);
    const eventUp = onButtonUp.mock.calls[0][0];
    expect(eventUp.buttonId).toBe('A');
    expect(eventUp.pressed).toBe(false);
    expect(eventUp.value).toBe(0.0);
  });

  it('binds RekkaBuffer and feeds D-pad and B/A presses for Konami code execution', () => {
    const rekka = new RekkaBuffer(1.0);
    const gm = new GamepadManager({ rekkaBuffer: rekka });

    // Standard Konami sequence button indices
    const buttonIndices = [12, 12, 13, 13, 14, 15, 14, 15, 1, 0];

    for (const btnIdx of buttonIndices) {
      // Press button
      gm.poll([createMockGamepad(0, [btnIdx])]);
      // Release button
      gm.poll([createMockGamepad(0, [])]);
    }

    expect(rekka.matches(KONAMI_SEQUENCE)).toBe(true);
  });

  it('translates analog stick deflection to virtual D-pad inputs', () => {
    const rekka = new RekkaBuffer(1.0);
    const onButtonDown = vi.fn();
    const gm = new GamepadManager({
      rekkaBuffer: rekka,
      onButtonDown,
    });

    // Neutral stick
    gm.poll([createMockGamepad(0, [], [0, 0])]);
    expect(onButtonDown).not.toHaveBeenCalled();

    // Deflect left stick upwards with axis 1 at -0.8
    gm.poll([createMockGamepad(0, [], [0, -0.8])]);
    expect(onButtonDown).toHaveBeenCalledWith(
      expect.objectContaining({
        buttonId: 'UP',
        pressed: true,
      })
    );
    expect(rekka.getTokens()).toEqual(['UP']);

    // Return to neutral
    gm.poll([createMockGamepad(0, [], [0, 0])]);

    // Deflect left stick rightwards with axis 0 at 0.9
    gm.poll([createMockGamepad(0, [], [0.9, 0])]);
    expect(onButtonDown).toHaveBeenCalledWith(
      expect.objectContaining({
        buttonId: 'RIGHT',
        pressed: true,
      })
    );
    expect(rekka.getTokens()).toEqual(['UP', 'RIGHT']);
  });

  it('filters analog stick drift within deadzone and applies hysteresis', () => {
    const onButtonDown = vi.fn();
    const onButtonUp = vi.fn();
    const gm = new GamepadManager({
      deadzone: 0.25,
      onButtonDown,
      onButtonUp,
    });

    // 1. Minor drift below deadzone: 0.15 is ignored
    gm.poll([createMockGamepad(0, [], [0.15, -0.18])]);
    expect(gm.isVirtualAxisEngaged(0, 'RIGHT')).toBe(false);
    expect(gm.isVirtualAxisEngaged(0, 'UP')).toBe(false);
    expect(onButtonDown).not.toHaveBeenCalled();

    // 2. Partial deflection below engagement threshold: 0.40 still not engaged
    gm.poll([createMockGamepad(0, [], [0.4, 0])]);
    expect(gm.isVirtualAxisEngaged(0, 'RIGHT')).toBe(false);
    expect(onButtonDown).not.toHaveBeenCalled();

    // 3. Deflection reaching engagement threshold: 0.60 engages
    gm.poll([createMockGamepad(0, [], [0.6, 0])]);
    expect(gm.isVirtualAxisEngaged(0, 'RIGHT')).toBe(true);
    expect(onButtonDown).toHaveBeenCalledTimes(1);
    const downEvent = onButtonDown.mock.calls[0][0];
    expect(downEvent.buttonId).toBe('RIGHT');
    expect(downEvent.pressed).toBe(true);
    expect(downEvent.value).toBe(0.6);

    // 4. Slight stick relaxation to 0.35: hysteresis holds engagement
    gm.poll([createMockGamepad(0, [], [0.35, 0])]);
    expect(gm.isVirtualAxisEngaged(0, 'RIGHT')).toBe(true);
    expect(onButtonUp).not.toHaveBeenCalled();

    // 5. Stick returned to neutral at 0.10: released
    gm.poll([createMockGamepad(0, [], [0.1, 0])]);
    expect(gm.isVirtualAxisEngaged(0, 'RIGHT')).toBe(false);
    expect(onButtonUp).toHaveBeenCalledTimes(1);
    const upEvent = onButtonUp.mock.calls[0][0];
    expect(upEvent.buttonId).toBe('RIGHT');
    expect(upEvent.pressed).toBe(false);
    expect(upEvent.value).toBe(0.0);
  });

  it('handles disconnection cleanly', () => {
    const onDisconnected = vi.fn();
    const gm = new GamepadManager({ onDisconnected });

    // Connect
    gm.poll([createMockGamepad(0, [])]);
    expect(gm.isConnected(0)).toBe(true);
    expect(gm.getConnectedCount()).toBe(1);

    // Disconnect when snapshot entry is null
    gm.poll([null]);
    expect(gm.isConnected(0)).toBe(false);
    expect(gm.getConnectedCount()).toBe(0);
    expect(onDisconnected).toHaveBeenCalledWith(0);
  });
});
