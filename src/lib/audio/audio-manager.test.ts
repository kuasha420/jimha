import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { JimhaAudioManager, isTauriEnvironment } from './audio-manager';

describe('JimhaAudioManager Single-Sink Dispatch Contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    delete (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
  });

  afterEach(() => {
    delete (window as unknown as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
  });

  it('detects Tauri environment accurately', () => {
    expect(isTauriEnvironment()).toBe(false);
    (window as unknown as { __TAURI_INTERNALS__: unknown }).__TAURI_INTERNALS__ = {};
    expect(isTauriEnvironment()).toBe(true);
  });

  it('in browser environment, dispatches playKey and playChord to Web Audio without Tauri IPC', () => {
    const manager = new JimhaAudioManager();
    const playFrequencySpy = vi.spyOn(manager, 'playFrequency').mockImplementation(() => {});

    const selection = manager.playKey('A');
    expect(selection).toBeDefined();
    expect(selection.frequency).toBeGreaterThan(0);
    expect(playFrequencySpy).toHaveBeenCalledWith(selection.frequency);

    manager.playChord([0, 2, 4]);
    expect(playFrequencySpy).toHaveBeenCalled();
  });

  it('in Tauri environment, dispatches playKey to native IPC and suppresses Web Audio', async () => {
    (window as unknown as { __TAURI_INTERNALS__: unknown }).__TAURI_INTERNALS__ = {};

    const manager = new JimhaAudioManager();
    const playFrequencySpy = vi.spyOn(manager, 'playFrequency').mockImplementation(() => {});

    const selection = manager.playKey('B');
    expect(selection).toBeDefined();
    // In Tauri, Web Audio buffer playback is suppressed
    expect(playFrequencySpy).not.toHaveBeenCalled();
  });

  it('in Tauri environment, suppresses Web Audio for chords, fanfare, startup, and sticker taps', () => {
    (window as unknown as { __TAURI_INTERNALS__: unknown }).__TAURI_INTERNALS__ = {};

    const manager = new JimhaAudioManager();
    const playFrequencySpy = vi.spyOn(manager, 'playFrequency').mockImplementation(() => {});

    manager.playChord([0, 3, 5]);
    manager.playStartupChime();
    manager.playCelebrationFanfare();
    manager.playStickerTapSound(2);

    expect(playFrequencySpy).not.toHaveBeenCalled();
  });
});
