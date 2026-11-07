/**
 * Steam Deck & Gamepad Controller Engine for Jimha
 *
 * Implements standard W3C Gamepad API polling, connection listeners,
 * button state edge detection (A/B/X/Y, D-Pad, bumpers, triggers),
 * and feeds D-pad / BA inputs directly into RekkaBuffer for Konami code execution.
 */

import type { RekkaBuffer } from './rekka';

export type GamepadButtonId =
  | 'A'
  | 'B'
  | 'X'
  | 'Y'
  | 'LB'
  | 'RB'
  | 'LT'
  | 'RT'
  | 'SELECT'
  | 'START'
  | 'L3'
  | 'R3'
  | 'UP'
  | 'DOWN'
  | 'LEFT'
  | 'RIGHT'
  | 'GUIDE';

export interface GamepadButtonInfo {
  id: GamepadButtonId;
  label: string;
  emoji: string;
  color: string;
  isRekkaToken: boolean;
  rekkaToken?: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT' | 'B' | 'A';
}

export const STANDARD_BUTTON_MAP: Record<number, GamepadButtonId> = {
  0: 'A',
  1: 'B',
  2: 'X',
  3: 'Y',
  4: 'LB',
  5: 'RB',
  6: 'LT',
  7: 'RT',
  8: 'SELECT',
  9: 'START',
  10: 'L3',
  11: 'R3',
  12: 'UP',
  13: 'DOWN',
  14: 'LEFT',
  15: 'RIGHT',
  16: 'GUIDE',
};

export const GAMEPAD_BUTTON_META: Record<GamepadButtonId, GamepadButtonInfo> = {
  A: { id: 'A', label: 'A Button', emoji: '🟢', color: '#00E676', isRekkaToken: true, rekkaToken: 'A' },
  B: { id: 'B', label: 'B Button', emoji: '🔴', color: '#FF1744', isRekkaToken: true, rekkaToken: 'B' },
  X: { id: 'X', label: 'X Button', emoji: '🔵', color: '#2979FF', isRekkaToken: false },
  Y: { id: 'Y', label: 'Y Button', emoji: '🟡', color: '#FFEA00', isRekkaToken: false },
  LB: { id: 'LB', label: 'Left Bumper', emoji: '🛡️', color: '#E040FB', isRekkaToken: false },
  RB: { id: 'RB', label: 'Right Bumper', emoji: '⚔️', color: '#7C4DFF', isRekkaToken: false },
  LT: { id: 'LT', label: 'Left Trigger', emoji: '⚡', color: '#00E5FF', isRekkaToken: false },
  RT: { id: 'RT', label: 'Right Trigger', emoji: '🔥', color: '#FF3D00', isRekkaToken: false },
  SELECT: { id: 'SELECT', label: 'Select / View', emoji: '✨', color: '#B388FF', isRekkaToken: false },
  START: { id: 'START', label: 'Start / Menu', emoji: '🌟', color: '#FFD600', isRekkaToken: false },
  L3: { id: 'L3', label: 'Left Stick Click', emoji: '🕹️', color: '#76FF03', isRekkaToken: false },
  R3: { id: 'R3', label: 'Right Stick Click', emoji: '🎯', color: '#FF6D00', isRekkaToken: false },
  UP: { id: 'UP', label: 'D-Pad Up', emoji: '⬆️', color: '#FF4081', isRekkaToken: true, rekkaToken: 'UP' },
  DOWN: { id: 'DOWN', label: 'D-Pad Down', emoji: '⬇️', color: '#00E5FF', isRekkaToken: true, rekkaToken: 'DOWN' },
  LEFT: { id: 'LEFT', label: 'D-Pad Left', emoji: '⬅️', color: '#FFD600', isRekkaToken: true, rekkaToken: 'LEFT' },
  RIGHT: { id: 'RIGHT', label: 'D-Pad Right', emoji: '➡️', color: '#76FF03', isRekkaToken: true, rekkaToken: 'RIGHT' },
  GUIDE: { id: 'GUIDE', label: 'Steam / Home', emoji: '👑', color: '#E040FB', isRekkaToken: false },
};

export interface GamepadButtonEvent {
  gamepadIndex: number;
  gamepadId: string;
  buttonId: GamepadButtonId;
  rawIndex: number;
  value: number;
  pressed: boolean;
  meta: GamepadButtonInfo;
}

export interface GamepadButtonLike {
  pressed: boolean;
  value: number;
}

export interface GamepadLike {
  index: number;
  id: string;
  connected: boolean;
  mapping: string;
  buttons: readonly GamepadButtonLike[] | GamepadButtonLike[];
  axes?: readonly number[] | number[];
}

export interface GamepadManagerOptions {
  onButtonDown?: (event: GamepadButtonEvent) => void;
  onButtonUp?: (event: GamepadButtonEvent) => void;
  onConnected?: (index: number, id: string) => void;
  onDisconnected?: (index: number) => void;
  rekkaBuffer?: RekkaBuffer;
  deadzone?: number;
}

export class GamepadManager {
  private options: GamepadManagerOptions;
  private previousButtonStates: Map<number, boolean[]> = new Map();
  private previousAxisStates: Map<number, { up: boolean; down: boolean; left: boolean; right: boolean }> = new Map();
  private rekkaBuffer: RekkaBuffer | null = null;
  private isPolling: boolean = false;
  private animFrameId: number | null = null;
  private attachedWindow: Window | null = null;
  private boundConnected: ((e: Event) => void) | null = null;
  private boundDisconnected: ((e: Event) => void) | null = null;

  constructor(options: GamepadManagerOptions = {}) {
    this.options = options;
    if (options.rekkaBuffer) {
      this.rekkaBuffer = options.rekkaBuffer;
    }
  }

  public bindRekka(rekka: RekkaBuffer): void {
    this.rekkaBuffer = rekka;
  }

  public poll(gamepadsSnapshot?: (GamepadLike | null)[]): void {
    let gamepads: (GamepadLike | null)[] = [];
    if (gamepadsSnapshot) {
      gamepads = gamepadsSnapshot;
    } else if (typeof navigator !== 'undefined' && typeof navigator.getGamepads === 'function') {
      gamepads = Array.from(navigator.getGamepads());
    }

    for (let i = 0; i < gamepads.length; i++) {
      const pad = gamepads[i];
      if (!pad || !pad.connected) {
        if (this.previousButtonStates.has(i)) {
          this.previousButtonStates.delete(i);
          this.previousAxisStates.delete(i);
          this.options.onDisconnected?.(i);
        }
        continue;
      }

      // Check Buttons
      let prevButtons = this.previousButtonStates.get(pad.index);
      if (!prevButtons) {
        prevButtons = new Array(pad.buttons.length).fill(false);
        this.previousButtonStates.set(pad.index, prevButtons);
        this.options.onConnected?.(pad.index, pad.id);
      }

      for (let btnIdx = 0; btnIdx < pad.buttons.length; btnIdx++) {
        const btn = pad.buttons[btnIdx];
        const isPressed = btn.pressed || btn.value > 0.5;
        const wasPressed = prevButtons[btnIdx] || false;

        const buttonId = STANDARD_BUTTON_MAP[btnIdx];
        if (buttonId) {
          const meta = GAMEPAD_BUTTON_META[buttonId];

          if (isPressed && !wasPressed) {
            // Button Down Edge
            prevButtons[btnIdx] = true;

            // Feed Rekka if eligible
            if (meta.isRekkaToken && meta.rekkaToken && this.rekkaBuffer) {
              this.rekkaBuffer.add(meta.rekkaToken);
            }

            this.options.onButtonDown?.({
              gamepadIndex: pad.index,
              gamepadId: pad.id,
              buttonId,
              rawIndex: btnIdx,
              value: btn.value,
              pressed: true,
              meta,
            });
          } else if (!isPressed && wasPressed) {
            // Button Up Edge
            prevButtons[btnIdx] = false;
            this.options.onButtonUp?.({
              gamepadIndex: pad.index,
              gamepadId: pad.id,
              buttonId,
              rawIndex: btnIdx,
              value: btn.value,
              pressed: false,
              meta,
            });
          }
        }
      }

      // Check Axes (Analog Sticks to virtual D-pad mapping with deadzone & hysteresis)
      if (pad.axes && pad.axes.length >= 2) {
        let prevAxis = this.previousAxisStates.get(pad.index);
        if (!prevAxis) {
          prevAxis = { up: false, down: false, left: false, right: false };
          this.previousAxisStates.set(pad.index, prevAxis);
        }

        const deadzone = this.options.deadzone ?? 0.25;
        const rawX = pad.axes[0];
        const rawY = pad.axes[1];
        const axisX = Math.abs(rawX) > deadzone ? rawX : 0;
        const axisY = Math.abs(rawY) > deadzone ? rawY : 0;

        this.checkVirtualAxis(pad, 'LEFT', axisX, false, prevAxis.left, deadzone, (val) => (prevAxis!.left = val));
        this.checkVirtualAxis(pad, 'RIGHT', axisX, true, prevAxis.right, deadzone, (val) => (prevAxis!.right = val));
        this.checkVirtualAxis(pad, 'UP', axisY, false, prevAxis.up, deadzone, (val) => (prevAxis!.up = val));
        this.checkVirtualAxis(pad, 'DOWN', axisY, true, prevAxis.down, deadzone, (val) => (prevAxis!.down = val));
      }
    }
  }

  private checkVirtualAxis(
    pad: GamepadLike,
    buttonId: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT',
    axisValue: number,
    isPositiveDirection: boolean,
    wasEngaged: boolean,
    deadzone: number,
    setEngaged: (val: boolean) => void
  ): void {
    const meta = GAMEPAD_BUTTON_META[buttonId];
    const engagementThreshold = 0.50;

    let shouldEngage = false;
    let shouldRelease = false;

    if (isPositiveDirection) {
      if (!wasEngaged && axisValue >= engagementThreshold) {
        shouldEngage = true;
      } else if (wasEngaged && axisValue < deadzone) {
        shouldRelease = true;
      }
    } else {
      if (!wasEngaged && axisValue <= -engagementThreshold) {
        shouldEngage = true;
      } else if (wasEngaged && axisValue > -deadzone) {
        shouldRelease = true;
      }
    }

    if (shouldEngage) {
      setEngaged(true);
      if (meta.isRekkaToken && meta.rekkaToken && this.rekkaBuffer) {
        this.rekkaBuffer.add(meta.rekkaToken);
      }
      this.options.onButtonDown?.({
        gamepadIndex: pad.index,
        gamepadId: pad.id,
        buttonId,
        rawIndex: -1,
        value: Math.abs(axisValue),
        pressed: true,
        meta,
      });
    } else if (shouldRelease) {
      setEngaged(false);
      this.options.onButtonUp?.({
        gamepadIndex: pad.index,
        gamepadId: pad.id,
        buttonId,
        rawIndex: -1,
        value: 0.0,
        pressed: false,
        meta,
      });
    }
  }

  public start(): void {
    if (this.isPolling) return;
    this.isPolling = true;

    const loop = () => {
      if (!this.isPolling) return;
      this.poll();
      this.animFrameId = requestAnimationFrame(loop);
    };

    this.animFrameId = requestAnimationFrame(loop);
  }

  public stop(): void {
    this.isPolling = false;
    if (this.animFrameId !== null) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
  }

  public attach(win: Window = window): void {
    this.detach();
    this.attachedWindow = win;

    this.boundConnected = (e: Event) => {
      const gpEvent = e as unknown as { gamepad: GamepadLike };
      if (gpEvent && gpEvent.gamepad) {
        this.options.onConnected?.(gpEvent.gamepad.index, gpEvent.gamepad.id);
      }
    };

    this.boundDisconnected = (e: Event) => {
      const gpEvent = e as unknown as { gamepad: GamepadLike };
      if (gpEvent && gpEvent.gamepad) {
        this.previousButtonStates.delete(gpEvent.gamepad.index);
        this.previousAxisStates.delete(gpEvent.gamepad.index);
        this.options.onDisconnected?.(gpEvent.gamepad.index);
      }
    };

    win.addEventListener('gamepadconnected', this.boundConnected);
    win.addEventListener('gamepaddisconnected', this.boundDisconnected);

    this.start();
  }

  public detach(): void {
    this.stop();
    if (this.attachedWindow) {
      if (this.boundConnected) {
        this.attachedWindow.removeEventListener('gamepadconnected', this.boundConnected);
      }
      if (this.boundDisconnected) {
        this.attachedWindow.removeEventListener('gamepaddisconnected', this.boundDisconnected);
      }
      this.attachedWindow = null;
    }
    this.previousButtonStates.clear();
    this.previousAxisStates.clear();
  }

  public isConnected(gamepadIndex: number = 0): boolean {
    return this.previousButtonStates.has(gamepadIndex);
  }

  public getConnectedCount(): number {
    return this.previousButtonStates.size;
  }

  public isButtonPressed(gamepadIndex: number, buttonId: GamepadButtonId): boolean {
    const states = this.previousButtonStates.get(gamepadIndex);
    if (!states) return false;
    for (let idx = 0; idx < states.length; idx++) {
      if (STANDARD_BUTTON_MAP[idx] === buttonId && states[idx]) {
        return true;
      }
    }
    return false;
  }

  public isVirtualAxisEngaged(gamepadIndex: number, direction: 'UP' | 'DOWN' | 'LEFT' | 'RIGHT'): boolean {
    const axis = this.previousAxisStates.get(gamepadIndex);
    if (!axis) return false;
    if (direction === 'UP') return axis.up;
    if (direction === 'DOWN') return axis.down;
    if (direction === 'LEFT') return axis.left;
    if (direction === 'RIGHT') return axis.right;
    return false;
  }
}
