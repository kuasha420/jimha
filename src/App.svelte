<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import PixiCanvas from './lib/components/PixiCanvas.svelte';
  import ExitHoldHud from './lib/components/ExitHoldHud.svelte';
  import ParentGateHud from './lib/components/ParentGateHud.svelte';
  import VirtualSwitcher, { type WindowItem } from './lib/components/VirtualSwitcher.svelte';
  import StickerBook from './lib/components/StickerBook.svelte';
  import UnlockCelebrationBanner from './lib/components/UnlockCelebrationBanner.svelte';
  import { JimhaAudioManager } from './lib/audio/audio-manager';
  import { RekkaBuffer, KONAMI_SEQUENCE, QUICK_SWITCH_SEQUENCE } from './lib/engine/rekka';
  import { GamepadManager, type GamepadButtonEvent } from './lib/engine/gamepad';
  import { STICKERS } from './lib/content/stickers';
  import type { InstrumentId } from './lib/content/instruments';
  import { APP_NAME } from './lib/constants';

  interface ChildProfile {
    child_name: string;
    total_play_time_sec: number;
    total_key_presses: number;
    total_bubbles_popped: number;
    unlocked_stickers: string[];
    settings: {
      esc_hold_seconds: number;
      parent_gate_seconds: number;
      audio_volume: number;
      instrument: string;
    };
  }

  let pixiCanvas: PixiCanvas | null = $state(null);
  let switcherRef: VirtualSwitcher | null = $state(null);
  let audioManager: JimhaAudioManager | null = $state(null);
  let gamepadManager: GamepadManager | null = null;
  let touchCount = $state(0);
  let lastNoteName = $state('');

  // Child Progression state
  let profile = $state<ChildProfile>({
    child_name: 'Jimha',
    total_play_time_sec: 0,
    total_key_presses: 0,
    total_bubbles_popped: 0,
    unlocked_stickers: [],
    settings: {
      esc_hold_seconds: 3.0,
      parent_gate_seconds: 2.0,
      audio_volume: 1.0,
      instrument: 'celesta',
    },
  });
  let isStickerBookOpen = $state(false);
  let activeCelebrationStickerId = $state<string | null>(null);
  let showCelebrationBanner = $state(false);
  let showEscapeParentHint = $state(false);
  let escapeHintTimer: ReturnType<typeof setTimeout> | null = null;

  $effect(() => {
    if (isStickerBookOpen || virtualSwitcherActive) {
      audioManager?.setAudioMode('ui');
    } else {
      audioManager?.setAudioMode('idle');
    }
  });

  // ESC hold state (3.0s continuous hold)
  let isEscPressed = $state(false);
  let escStartTime = 0;
  let escHoldProgress = $state(0.0);
  let escRemainingSec = $state(3.0);

  // Alt+Tab Parent Gate hold state (2.0s continuous hold)
  let isAltTabPressed = $state(false);
  let altPressed = false;
  let tabPressed = false;
  let altTabStartTime = 0;
  let altTabHoldProgress = $state(0.0);
  let altTabRemainingSec = $state(2.0);

  // Rekka combo engine & Virtual Switcher
  const rekka = new RekkaBuffer(0.8);
  let virtualSwitcherActive = $state(false);
  let virtualWindows = $state<WindowItem[]>([]);
  let virtualIndex = $state(0);
  let switcherLastActionTime = 0;
  let lastInputTime = performance.now();
  let lullabyTriggeredInIdleCycle = false;

  let animFrameId: number | null = null;

  async function callTauri<T>(cmd: string, args?: Record<string, unknown>): Promise<T | null> {
    try {
      if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
        const { invoke } = await import('@tauri-apps/api/core');
        return await invoke<T>(cmd, args);
      }
    } catch (err) {
      console.warn(`Tauri command ${cmd} invocation:`, err);
    }
    return null;
  }

  async function triggerDesktopHandover(targetId?: string) {
    if (audioManager) {
      audioManager.playKey('ENTER');
    }
    await callTauri('kiosk_handover', { targetId: targetId ?? null });
    await callTauri('kiosk_minimize');
  }

  async function recordProgressionEvent(eventType: string, key?: string | null) {
    if (eventType === 'key_press') {
      profile.total_key_presses += 1;
    } else if (eventType === 'bubble_pop') {
      profile.total_bubbles_popped += 1;
    }

    const unlocked = await callTauri<string | null>('profile_record_event', {
      eventType,
      key: key ?? null,
    });
    if (unlocked) {
      if (!profile.unlocked_stickers.includes(unlocked)) {
        profile.unlocked_stickers = [...profile.unlocked_stickers, unlocked];
      }
      activeCelebrationStickerId = unlocked;
      showCelebrationBanner = true;
      if (audioManager) {
        audioManager.playCelebrationFanfare();
      }
      if (pixiCanvas) {
        pixiCanvas.triggerKey('✨', { color: '#FFD600', subtitle: '🌟 NEW BADGE UNLOCKED! 🌟' });
      }
    }
  }

  function triggerKonamiHandover() {
    void recordProgressionEvent('konami', 'KONAMI');
    if (pixiCanvas) {
      pixiCanvas.triggerKey('👑 30 LIVES GRANTED! 🚀💖✨', { color: '#FF4081' });
    }
    if (audioManager) {
      audioManager.playKey('ENTER');
    }
    if (!import.meta.env.DEV) {
      setTimeout(() => {
        void triggerDesktopHandover();
      }, 600);
    }
  }

  async function triggerQuickSwitchHandover() {
    const wins = await callTauri<WindowItem[]>('kiosk_query_windows');
    const target = wins && wins.length > 0 ? wins[0]?.id : undefined;
    await triggerDesktopHandover(target);
  }

  async function openVirtualSwitcher() {
    const wins = await callTauri<WindowItem[]>('kiosk_query_windows');
    virtualWindows =
      wins && wins.length > 0
        ? wins
        : [{ id: 'desktop', title: 'Desktop / Workspace', icon: 'user-desktop' }];
    virtualIndex = 0;
    virtualSwitcherActive = true;
    switcherLastActionTime = performance.now();
    if (audioManager) {
      audioManager.playKey('ALT_TAB');
    }
  }

  function handleKeyTriggered(_title: string, _subtitle: string) {
    touchCount += 1;
  }

  function handleBubblePop() {
    touchCount += 1;
    lastInputTime = performance.now();
    lullabyTriggeredInIdleCycle = false;
    void recordProgressionEvent('bubble_pop');
    if (audioManager) {
      audioManager.setAudioMode('playing');
      const selection = audioManager.playKey('POP');
      lastNoteName = selection.noteName;
    }
  }

  const pressedKeys = new Set<string>();

  const SWALLOWED_KEY_CODES = new Set([
    'Space',
    'ArrowUp',
    'ArrowDown',
    'ArrowLeft',
    'ArrowRight',
    'Tab',
    'Backspace',
    'Escape',
    'F5',
    'F11',
  ]);

  const BROWSER_SHORTCUT_KEYS = new Set(['w', 'W', 'q', 'Q', 'r', 'R']);

  const ARROW_KEY_MAP: Record<string, string> = {
    ArrowUp: 'UP',
    ArrowDown: 'DOWN',
    ArrowLeft: 'LEFT',
    ArrowRight: 'RIGHT',
  };

  function normalizeKeyToken(key: string): string {
    return ARROW_KEY_MAP[key] ?? key.toUpperCase();
  }

  function preventToddlerDefaults(event: KeyboardEvent): void {
    if (
      SWALLOWED_KEY_CODES.has(event.code) ||
      (event.altKey && (event.key === 'F4' || event.key === 'Tab')) ||
      (event.ctrlKey && BROWSER_SHORTCUT_KEYS.has(event.key))
    ) {
      event.preventDefault();
    }
  }

  function handleAdultAltTabGate(event: KeyboardEvent): boolean {
    const isAlt = event.key === 'Alt';
    const isTab = event.key === 'Tab';

    if (isAlt) altPressed = true;
    if (isTab) tabPressed = true;

    const isAltTab = (isTab && (event.altKey || altPressed)) || (isAlt && tabPressed);

    // 1. Alt+Tab Continuous Hold Adult Gate
    if (isAltTab) {
      isEscPressed = false;
      escHoldProgress = 0;
      virtualSwitcherActive = false;
      rekka.clear();

      if (!isAltTabPressed) {
        isAltTabPressed = true;
        altTabStartTime = performance.now();
        altTabHoldProgress = 0;
        altTabRemainingSec = 2.0;
        if (audioManager) {
          audioManager.playKey('ALT_TAB');
        }
      }
      return true;
    }

    // Any non-Alt/Tab key interrupts Alt+Tab hold
    if (!isAlt && !isTab) {
      isAltTabPressed = false;
      altTabHoldProgress = 0;
      altPressed = false;
      tabPressed = false;
    }

    return false;
  }

  function handleSwitcherNavigation(key: string): boolean {
    if (key === 'ArrowRight' || key === 'ArrowDown') {
      switcherRef?.cycleNext();
      rekka.add(key === 'ArrowRight' ? 'RIGHT' : 'DOWN');
      if (rekka.matches(QUICK_SWITCH_SEQUENCE)) {
        virtualSwitcherActive = false;
        void triggerQuickSwitchHandover();
      }
      return true;
    }

    if (key === 'ArrowLeft' || key === 'ArrowUp') {
      switcherRef?.cyclePrev();
      rekka.add(key === 'ArrowLeft' ? 'LEFT' : 'UP');
      return true;
    }

    return false;
  }

  function handleVirtualSwitcherKey(event: KeyboardEvent): boolean {
    if (!virtualSwitcherActive) {
      return false;
    }

    switcherLastActionTime = performance.now();

    if (event.key === 'Escape') {
      virtualSwitcherActive = false;
      rekka.clear();
      return true;
    }

    if (event.key === 'Enter') {
      virtualSwitcherActive = false;
      switcherRef?.commitSelection();
      return true;
    }

    if (handleSwitcherNavigation(event.key)) {
      return true;
    }

    const upper = event.key.toUpperCase();
    if (upper === 'B' || upper === 'A') {
      rekka.add(upper);
      if (rekka.matches(KONAMI_SEQUENCE)) {
        virtualSwitcherActive = false;
        void triggerKonamiHandover();
      }
      return true;
    }

    // Any other key closes virtual switcher
    virtualSwitcherActive = false;
    rekka.clear();
    return false;
  }

  function handleCompoundExitGate(event: KeyboardEvent): boolean {
    // 3. Shift+Escape Compound Adult Exit Gate (2.5s continuous hold)
    const isShiftEsc = event.key === 'Escape' && (event.shiftKey || pressedKeys.has('Shift'));
    const isElbowMashing = pressedKeys.size > 2;

    if (isElbowMashing) {
      // Multiple keys pressed simultaneously (e.g. toddler elbow resting across top row) cancels exit
      isEscPressed = false;
      escHoldProgress = 0;
    } else if (isShiftEsc) {
      showEscapeParentHint = false;
      if (!isEscPressed) {
        isEscPressed = true;
        escStartTime = performance.now();
        escHoldProgress = 0;
        escRemainingSec = 2.5;
      }
      return true;
    } else {
      isEscPressed = false;
      escHoldProgress = 0;
    }

    // Lone Escape pressed: show discrete parent exit hint while retaining rocket companion card
    if (event.key === 'Escape' && !isShiftEsc) {
      showEscapeParentHint = true;
      if (escapeHintTimer) {
        clearTimeout(escapeHintTimer);
      }
      escapeHintTimer = setTimeout(() => {
        showEscapeParentHint = false;
      }, 4000);
    }

    return false;
  }

  function checkArcadeCombos(): boolean {
    if (rekka.matches(KONAMI_SEQUENCE)) {
      void triggerKonamiHandover();
      return true;
    }
    if (rekka.matches(QUICK_SWITCH_SEQUENCE)) {
      void openVirtualSwitcher();
      return true;
    }
    return false;
  }

  function handleGamepadVirtualSwitcher(event: GamepadButtonEvent): boolean {
    if (!virtualSwitcherActive) {
      return false;
    }

    switcherLastActionTime = performance.now();
    if (event.buttonId === 'B') {
      virtualSwitcherActive = false;
      rekka.clear();
      return true;
    }
    if (event.buttonId === 'A' || event.buttonId === 'START') {
      virtualSwitcherActive = false;
      switcherRef?.commitSelection();
      return true;
    }
    if (['RIGHT', 'DOWN', 'RB', 'RT'].includes(event.buttonId)) {
      switcherRef?.cycleNext();
      if (rekka.matches(QUICK_SWITCH_SEQUENCE)) {
        virtualSwitcherActive = false;
        void triggerQuickSwitchHandover();
      }
      return true;
    }
    if (['LEFT', 'UP', 'LB', 'LT'].includes(event.buttonId)) {
      switcherRef?.cyclePrev();
      return true;
    }
    return true;
  }

  function handleKeyDown(event: KeyboardEvent) {
    pressedKeys.add(event.key);

    if (isStickerBookOpen) {
      event.preventDefault();
      isStickerBookOpen = false;
      return;
    }

    if (event.key === 'F2' || (event.altKey && (event.key === 'b' || event.key === 'B'))) {
      event.preventDefault();
      isStickerBookOpen = true;
      return;
    }

    preventToddlerDefaults(event);

    if (handleAdultAltTabGate(event)) {
      return;
    }

    if (handleVirtualSwitcherKey(event)) {
      return;
    }

    if (handleCompoundExitGate(event)) {
      return;
    }

    // 4. Rekka Arcade Combo Buffer Processing
    const token = normalizeKeyToken(event.key);
    rekka.add(token);

    if (checkArcadeCombos()) {
      return;
    }

    // 5. Normal Game Audio, Pixi Canvas and Child Progression Dispatch
    lastInputTime = performance.now();
    lullabyTriggeredInIdleCycle = false;
    const keyName = event.key === ' ' ? 'SPACE' : event.key;
    void recordProgressionEvent('key_press', keyName);

    if (audioManager) {
      const selection = audioManager.playKey(event.key);
      lastNoteName = selection.noteName;
    }

    if (pixiCanvas) {
      pixiCanvas.triggerKey(event.key);
    }
  }

  function handleKeyUp(event: KeyboardEvent) {
    pressedKeys.delete(event.key);

    if (event.key === 'Escape' || event.key === 'Shift') {
      isEscPressed = false;
      escHoldProgress = 0;
    }

    if (event.key === 'Alt') {
      altPressed = false;
      isAltTabPressed = false;
      altTabHoldProgress = 0;
    }

    if (event.key === 'Tab') {
      tabPressed = false;
      isAltTabPressed = false;
      altTabHoldProgress = 0;
    }
  }

  function handleGamepadButtonDown(event: GamepadButtonEvent) {
    if (isStickerBookOpen) {
      if (['B', 'START', 'SELECT'].includes(event.buttonId)) {
        isStickerBookOpen = false;
      }
      return;
    }

    if (handleGamepadVirtualSwitcher(event)) {
      return;
    }

    // Check combos from gamepad RekkaBuffer feeds
    if (checkArcadeCombos()) {
      return;
    }

    // Gamepad button audio, visual and progression dispatch
    lastInputTime = performance.now();
    lullabyTriggeredInIdleCycle = false;
    void recordProgressionEvent('key_press', event.buttonId);

    if (audioManager) {
      const selection = audioManager.playKey(event.buttonId);
      lastNoteName = selection.noteName;
    }

    if (pixiCanvas) {
      pixiCanvas.triggerKey(event.meta.label, {
        emoji: event.meta.emoji,
        color: event.meta.color,
      });
    }
  }

  function tick() {
    const now = performance.now();

    // Check Shift+ESC compound hold
    if (isEscPressed) {
      if (pressedKeys.size > 2) {
        isEscPressed = false;
        escHoldProgress = 0;
      } else {
        const elapsed = (now - escStartTime) / 1000;
        const targetSec = profile.settings?.esc_hold_seconds || 2.5;
        escHoldProgress = Math.min(1.0, elapsed / targetSec);
        escRemainingSec = Math.max(0.0, targetSec - elapsed);
        if (escHoldProgress >= 1.0) {
          isEscPressed = false;
          void callTauri('kiosk_close');
        }
      }
    }

    // Check Alt+Tab hold
    if (isAltTabPressed) {
      const elapsed = (now - altTabStartTime) / 1000;
      altTabHoldProgress = Math.min(1.0, elapsed / 2.0);
      altTabRemainingSec = Math.max(0.0, 2.0 - elapsed);
      if (altTabHoldProgress >= 1.0) {
        isAltTabPressed = false;
        void triggerDesktopHandover();
      }
    }

    // Virtual Switcher idle timeout (15s)
    if (virtualSwitcherActive && now - switcherLastActionTime > 15000) {
      virtualSwitcherActive = false;
    }

    // Check lullaby listener achievement (20s uninterrupted idle with BGM)
    if (!lullabyTriggeredInIdleCycle && now - lastInputTime >= 20000) {
      lullabyTriggeredInIdleCycle = true;
      void recordProgressionEvent('lullaby', 'LULLABY');
    }

    rekka.checkDecay(Date.now() / 1000);

    animFrameId = requestAnimationFrame(tick);
  }

  function handleContextMenu(e: MouseEvent): void {
    e.preventDefault();
  }

  function handleBlur(): void {
    pressedKeys.clear();
    isEscPressed = false;
    escHoldProgress = 0;
    isAltTabPressed = false;
    altTabHoldProgress = 0;
  }

  onMount(() => {
    audioManager = new JimhaAudioManager();
    audioManager
      .unlock()
      .then(() => {
        audioManager?.playStartupChime();
        audioManager?.setAudioMode('idle');
      })
      .catch((err) => {
        console.warn('[App] Audio unlock error on mount:', err);
      });

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    gamepadManager = new GamepadManager({
      rekkaBuffer: rekka,
      onButtonDown: handleGamepadButtonDown,
    });
    gamepadManager.attach();

    void callTauri('kiosk_inhibit_shortcuts');

    void callTauri<ChildProfile>('profile_get').then((loadedProfile) => {
      if (loadedProfile) {
        profile = loadedProfile;
        touchCount = loadedProfile.total_key_presses + loadedProfile.total_bubbles_popped;
        if (loadedProfile.settings?.instrument && audioManager) {
          audioManager.setInstrument(loadedProfile.settings.instrument as InstrumentId);
        }
      }
    });

    animFrameId = requestAnimationFrame(tick);

    window.addEventListener('blur', handleBlur);
    window.addEventListener('contextmenu', handleContextMenu, { capture: true });

    // Initial warm-up on first user interaction
    const unlockAudio = () => {
      audioManager
        ?.unlock()
        .then(() => {
          audioManager?.playStartupChime();
          audioManager?.setAudioMode('idle');
        })
        .catch((err) => {
          console.warn('[App] Audio unlock error on user interaction:', err);
        });
      window.removeEventListener('pointerdown', unlockAudio);
      window.removeEventListener('keydown', unlockAudio);
    };
    window.addEventListener('pointerdown', unlockAudio, { once: true });
    window.addEventListener('keydown', unlockAudio, { once: true });
  });

  onDestroy(() => {
    if (escapeHintTimer) {
      clearTimeout(escapeHintTimer);
      escapeHintTimer = null;
    }
    window.removeEventListener('keydown', handleKeyDown);
    window.removeEventListener('keyup', handleKeyUp);
    window.removeEventListener('blur', handleBlur);
    window.removeEventListener('contextmenu', handleContextMenu, {
      capture: true,
    });
    if (gamepadManager) {
      gamepadManager.detach();
      gamepadManager = null;
    }
    if (animFrameId !== null) {
      cancelAnimationFrame(animFrameId);
    }
    if (audioManager) {
      audioManager.close();
      audioManager = null;
    }
  });
</script>

<main class="jimha-app" aria-label={APP_NAME} oncontextmenu={(e) => e.preventDefault()}>
  <PixiCanvas
    bind:this={pixiCanvas}
    onBubblePop={handleBubblePop}
    onKeyTriggered={handleKeyTriggered}
  />

  {#if isEscPressed || escHoldProgress > 0}
    <ExitHoldHud progress={escHoldProgress} remainingSec={escRemainingSec} />
  {/if}

  {#if isAltTabPressed || altTabHoldProgress > 0}
    <ParentGateHud progress={altTabHoldProgress} remainingSec={altTabRemainingSec} />
  {/if}

  {#if virtualSwitcherActive}
    <VirtualSwitcher
      bind:this={switcherRef}
      windows={virtualWindows}
      bind:selectedIndex={virtualIndex}
      onSelect={(id) => {
        virtualSwitcherActive = false;
        void triggerDesktopHandover(id);
      }}
      onClose={() => {
        virtualSwitcherActive = false;
      }}
    />
  {/if}

  <StickerBook
    isOpen={isStickerBookOpen}
    unlockedStickers={profile.unlocked_stickers}
    childName={profile.child_name}
    totalKeyPresses={profile.total_key_presses}
    totalBubblesPopped={profile.total_bubbles_popped}
    {audioManager}
    onClose={() => {
      isStickerBookOpen = false;
    }}
  />

  <UnlockCelebrationBanner
    stickerId={activeCelebrationStickerId}
    visible={showCelebrationBanner}
    onDismiss={() => {
      showCelebrationBanner = false;
    }}
    onOpenStickerBook={() => {
      showCelebrationBanner = false;
      isStickerBookOpen = true;
    }}
  />

  {#if showEscapeParentHint}
    <div class="escape-parent-hint" role="note">(Parents: Hold Shift + Esc for 2.5s to exit)</div>
  {/if}

  <header class="hud-header">
    <div class="hud-pill brand-pill">
      <span class="sparkle">✨</span>
      <span class="brand-text">{APP_NAME}</span>
    </div>

    <button
      type="button"
      class="hud-pill sticker-pill"
      onclick={() => {
        isStickerBookOpen = true;
      }}
      aria-label="Open Sticker Book"
    >
      <span>🏆 Badges ({profile.unlocked_stickers.length}/{STICKERS.length})</span>
    </button>

    {#if lastNoteName}
      <div class="hud-pill tone-pill">
        <span>🎵 {lastNoteName}</span>
      </div>
    {/if}

    <div class="hud-pill counter-pill">
      <span>Magical Touches: {touchCount}</span>
    </div>
  </header>
</main>

<style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    background: #0d0f18;
    color: #ffffff;
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      Roboto,
      sans-serif;
    user-select: none;
    -webkit-user-select: none;
  }

  .jimha-app {
    position: relative;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  .hud-header {
    position: absolute;
    top: 1.25rem;
    left: 1.5rem;
    right: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    pointer-events: none;
    z-index: 10;
  }

  .hud-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 9999px;
    background: rgba(13, 15, 24, 0.65);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    font-size: 0.95rem;
    font-weight: 600;
    color: #f7fafc;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  }

  .brand-pill {
    background: linear-gradient(135deg, rgba(255, 64, 129, 0.3), rgba(0, 229, 255, 0.2));
    border-color: rgba(255, 64, 129, 0.4);
  }

  .brand-text {
    font-weight: 800;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #ff4081, #ffd600, #00e5ff);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .tone-pill {
    color: #ffd600;
    border-color: rgba(255, 214, 0, 0.3);
  }

  .sticker-pill {
    pointer-events: auto;
    cursor: pointer;
    background: linear-gradient(135deg, rgba(255, 214, 0, 0.2), rgba(124, 77, 255, 0.2));
    border-color: rgba(255, 214, 0, 0.4);
    color: #ffd600;
    transition:
      transform 0.2s ease,
      border-color 0.2s ease,
      box-shadow 0.2s ease;
  }

  .sticker-pill:hover {
    transform: scale(1.05);
    border-color: rgba(255, 214, 0, 0.8);
    box-shadow: 0 4px 16px rgba(255, 214, 0, 0.3);
  }

  .escape-parent-hint {
    position: absolute;
    bottom: 2.5rem;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(13, 15, 24, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 0.6rem 1.4rem;
    border-radius: 9999px;
    font-size: 0.95rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.85);
    pointer-events: none;
    z-index: 50;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    animation: fade-in 0.3s ease-out;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translate(-50%, 10px);
    }
    to {
      opacity: 1;
      transform: translate(-50%, 0);
    }
  }
</style>
