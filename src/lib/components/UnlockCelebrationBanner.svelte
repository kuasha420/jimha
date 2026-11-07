<script lang="ts">
  import { onDestroy } from 'svelte';
  import { getStickerById } from '../content/stickers';

  interface Props {
    stickerId?: string | null;
    unlockedStickerId?: string | null;
    visible: boolean;
    onDismiss: () => void;
    onOpenStickerBook?: () => void;
  }

  const {
    stickerId,
    unlockedStickerId,
    visible,
    onDismiss,
    onOpenStickerBook
  }: Props = $props();

  const effectiveId = $derived(stickerId || unlockedStickerId || null);
  const sticker = $derived(effectiveId ? getStickerById(effectiveId) : null);
  let timerId: ReturnType<typeof setTimeout> | null = null;
  let holdTimer: ReturnType<typeof setTimeout> | null = null;

  let pointerDownTime = 0;
  let pointerStartY = 0;
  let didTriggerHold = false;

  function handlePointerDown(e: PointerEvent) {
    pointerDownTime = performance.now();
    pointerStartY = e.clientY;
    didTriggerHold = false;

    if (holdTimer) clearTimeout(holdTimer);
    holdTimer = setTimeout(() => {
      didTriggerHold = true;
      if (onOpenStickerBook) {
        onOpenStickerBook();
      }
    }, 450);
  }

  function handlePointerUp(e: PointerEvent) {
    if (holdTimer) clearTimeout(holdTimer);
    const duration = performance.now() - pointerDownTime;
    const deltaY = pointerStartY - e.clientY; // upward swipe

    if (didTriggerHold || duration >= 450 || deltaY > 30) {
      if (onOpenStickerBook) {
        onOpenStickerBook();
        return;
      }
    }

    // Brief normal tap simply dismisses banner
    onDismiss();
  }

  function handlePointerCancel() {
    if (holdTimer) clearTimeout(holdTimer);
    didTriggerHold = false;
  }

  $effect(() => {
    if (visible) {
      if (timerId) clearTimeout(timerId);
      timerId = setTimeout(() => {
        onDismiss();
      }, 5000);
    }
  });

  onDestroy(() => {
    if (timerId) clearTimeout(timerId);
    if (holdTimer) clearTimeout(holdTimer);
  });
</script>

{#if visible && sticker}
  <aside class="celebration-container" role="status" aria-live="polite">
    <div
      class="celebration-card"
      onpointerdown={handlePointerDown}
      onpointerup={handlePointerUp}
      onpointercancel={handlePointerCancel}
      role="button"
      tabindex="0"
      aria-label="New badge unlocked: {sticker.title}. Hold or swipe up to view album."
    >
      <div class="sparkle-orbit left-orbit">✨</div>
      <div class="badge-icon-wrap" style="--accent: {sticker.accentColor}">
        <span class="badge-emoji">{sticker.emoji}</span>
      </div>
      <div class="text-content">
        <div class="banner-tag">🌟 NEW BADGE UNLOCKED! 🌟</div>
        <h2 class="badge-title">{sticker.title}</h2>
        <p class="badge-desc">{sticker.description}</p>
        <div class="gesture-cue">
          <span class="gesture-icon">👆</span> Hold or swipe up to open Sticker Book 📖
        </div>
      </div>
      <div class="sparkle-orbit right-orbit">🎉</div>
    </div>
  </aside>
{/if}

<style>
  .celebration-container {
    position: fixed;
    top: 2rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999;
    cursor: pointer;
    animation: slide-bounce-in 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    filter: drop-shadow(0 12px 32px rgba(0, 0, 0, 0.5));
  }

  .celebration-card {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 1rem 1.75rem;
    background: rgba(18, 22, 34, 0.88);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 2px solid rgba(255, 214, 0, 0.6);
    border-radius: 9999px;
    color: #ffffff;
    font-family: inherit;
    cursor: pointer;
    text-align: left;
    box-shadow:
      0 0 30px rgba(255, 214, 0, 0.35),
      inset 0 0 15px rgba(255, 255, 255, 0.1);
  }

  .badge-icon-wrap {
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, var(--accent, #ffd600), transparent 70%);
    box-shadow: 0 0 20px var(--accent, #ffd600);
    animation: pulse-glow 1.5s infinite ease-in-out;
  }

  .badge-emoji {
    font-size: 2.2rem;
    line-height: 1;
  }

  .text-content {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    text-align: left;
  }

  .banner-tag {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 1px;
    color: #ffd600;
    text-transform: uppercase;
  }

  .badge-title {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 900;
    background: linear-gradient(135deg, #ffffff, #ffd600, #ff4081);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .badge-desc {
    margin: 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.8);
  }

  .gesture-cue {
    margin-top: 0.25rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: #00e5ff;
    display: flex;
    align-items: center;
    gap: 0.35rem;
    animation: cue-pulse 2s ease-in-out infinite;
  }

  .gesture-icon {
    font-size: 0.9rem;
  }

  @keyframes cue-pulse {
    0%, 100% {
      opacity: 0.75;
      transform: translateY(0);
    }
    50% {
      opacity: 1;
      transform: translateY(-2px);
    }
  }

  .sparkle-orbit {
    font-size: 1.8rem;
    animation: spin-sparkle 3s linear infinite;
  }

  @keyframes slide-bounce-in {
    0% {
      opacity: 0;
      transform: translate(-50%, -100%) scale(0.85);
    }
    100% {
      opacity: 1;
      transform: translate(-50%, 0) scale(1);
    }
  }

  @keyframes pulse-glow {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.1);
    }
  }

  @keyframes spin-sparkle {
    0% {
      transform: rotate(0deg) scale(1);
    }
    50% {
      transform: rotate(180deg) scale(1.2);
    }
    100% {
      transform: rotate(360deg) scale(1);
    }
  }
</style>
