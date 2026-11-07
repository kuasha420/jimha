<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import PixiCanvas from './lib/components/PixiCanvas.svelte';
  import { JimhaAudioManager } from './lib/audio/audio-manager';
  import { APP_NAME } from './lib/constants';

  let pixiCanvas: PixiCanvas | null = $state(null);
  let audioManager: JimhaAudioManager | null = null;
  let touchCount = $state(0);
  let lastNoteName = $state('');

  function handleKeyTriggered(_title: string, _subtitle: string) {
    touchCount += 1;
  }

  function handleBubblePop() {
    touchCount += 1;
    if (audioManager) {
      const selection = audioManager.playKey('POP');
      lastNoteName = selection.noteName;
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    // Intercept default actions for game keys to prevent unwanted scroll or reload
    if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab', 'Backspace'].includes(event.code)) {
      event.preventDefault();
    }

    if (audioManager) {
      const selection = audioManager.playKey(event.key);
      lastNoteName = selection.noteName;
    }

    if (pixiCanvas) {
      pixiCanvas.triggerKey(event.key);
    }
  }

  onMount(() => {
    audioManager = new JimhaAudioManager();
    window.addEventListener('keydown', handleKeyDown);

    // Initial warm-up on first user interaction
    const unlockAudio = () => {
      audioManager?.unlock();
      window.removeEventListener('pointerdown', unlockAudio);
      window.removeEventListener('keydown', unlockAudio);
    };
    window.addEventListener('pointerdown', unlockAudio, { once: true });
    window.addEventListener('keydown', unlockAudio, { once: true });
  });

  onDestroy(() => {
    window.removeEventListener('keydown', handleKeyDown);
    if (audioManager) {
      audioManager.close();
      audioManager = null;
    }
  });
</script>

<main class="jimha-app" aria-label={APP_NAME}>
  <PixiCanvas
    bind:this={pixiCanvas}
    onBubblePop={handleBubblePop}
    onKeyTriggered={handleKeyTriggered}
  />

  <header class="hud-header">
    <div class="hud-pill brand-pill">
      <span class="sparkle">✨</span>
      <span class="brand-text">{APP_NAME}</span>
    </div>

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
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
</style>
