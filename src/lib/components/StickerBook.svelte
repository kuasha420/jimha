<script lang="ts">
  import { STICKERS, type StickerBadge } from '../content/stickers';
  import type { JimhaAudioManager } from '../audio/audio-manager';

  interface Props {
    isOpen: boolean;
    unlockedStickers: string[];
    childName?: string;
    totalKeyPresses?: number;
    totalBubblesPopped?: number;
    audioManager?: JimhaAudioManager | null;
    onClose: () => void;
  }

  const {
    isOpen,
    unlockedStickers = [],
    childName = 'Jimha',
    totalKeyPresses = 0,
    totalBubblesPopped = 0,
    audioManager = null,
    onClose,
  }: Props = $props();

  const unlockedCount = $derived(STICKERS.filter((s) => unlockedStickers.includes(s.id)).length);

  function isUnlocked(id: string): boolean {
    return unlockedStickers.includes(id);
  }

  let tappedCardId = $state<string | null>(null);

  function playStickerSound(sticker: StickerBadge, idx: number) {
    tappedCardId = sticker.id;
    setTimeout(() => {
      if (tappedCardId === sticker.id) {
        tappedCardId = null;
      }
    }, 450);

    if (audioManager) {
      audioManager.playStickerTapSound(idx);
    }
  }

  function handleBackdrop(event: MouseEvent | PointerEvent) {
    if (event.target === event.currentTarget) {
      onClose();
    }
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <div
    class="sticker-modal-overlay"
    role="dialog"
    aria-modal="true"
    aria-label="Jimha Magical Sticker Book"
    tabindex="-1"
    onclick={handleBackdrop}
    onpointerdown={handleBackdrop}
  >
    <div class="sticker-book-panel">
      <!-- Header -->
      <header class="panel-header">
        <div class="header-titles">
          <h1 class="album-title">
            <span class="sparkle-icon">📖</span>
            {childName}'s Magical Sticker Book
            <span class="sparkle-icon">✨</span>
          </h1>
          <p class="album-subtitle">
            Collect sparkling achievement badges through wonder and play!
          </p>
        </div>

        <button class="close-button" aria-label="Close Sticker Book" onclick={onClose}> ✕ </button>
      </header>

      <!-- Stats ribbon -->
      <div class="stats-ribbon">
        <div class="stat-chip">
          <span class="stat-icon">🏆</span>
          <span class="stat-label">Badges:</span>
          <strong class="stat-value">{unlockedCount} / {STICKERS.length}</strong>
        </div>
        <div class="stat-chip">
          <span class="stat-icon">🎹</span>
          <span class="stat-label">Magical Keys:</span>
          <strong class="stat-value">{totalKeyPresses}</strong>
        </div>
        <div class="stat-chip">
          <span class="stat-icon">🫧</span>
          <span class="stat-label">Bubbles Popped:</span>
          <strong class="stat-value">{totalBubblesPopped}</strong>
        </div>
      </div>

      <!-- Sticker grid -->
      <div class="stickers-grid" role="list">
        {#each STICKERS as sticker, idx (sticker.id)}
          {@const unlocked = isUnlocked(sticker.id)}
          <!-- svelte-ignore a11y_click_events_have_key_events -->
          <div
            class="sticker-card"
            class:unlocked
            class:locked={!unlocked}
            class:tapped={tappedCardId === sticker.id}
            role="button"
            tabindex="0"
            style="--accent-color: {sticker.accentColor}"
            onclick={() => playStickerSound(sticker, idx)}
          >
            <div class="card-glow"></div>
            <div class="badge-emblem">
              {#if unlocked}
                <span class="emblem-emoji">{sticker.emoji}</span>
              {:else}
                <span class="emblem-lock">🔒</span>
              {/if}
            </div>

            <div class="badge-details">
              <h3 class="badge-name">{sticker.title}</h3>
              {#if unlocked}
                <p class="badge-description">{sticker.description}</p>
                <span class="unlocked-badge">✨ UNLOCKED ✨</span>
              {:else}
                <p class="badge-hint"><em>Hint: {sticker.hint}</em></p>
                <span class="locked-badge">LOCKED</span>
              {/if}
            </div>
          </div>
        {/each}
      </div>

      <!-- Footer action -->
      <footer class="panel-footer">
        <button class="resume-button" onclick={onClose}> 💖 Return to Play (ESC) 🚀 </button>
      </footer>
    </div>
  </div>
{/if}

<style>
  .sticker-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(10, 12, 20, 0.88);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 2rem;
    box-sizing: border-box;
    animation: fade-in 0.25s ease-out;
  }

  .sticker-book-panel {
    width: 100%;
    max-width: 960px;
    max-height: 90vh;
    background: rgba(22, 27, 46, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 28px;
    box-shadow:
      0 24px 64px rgba(0, 0, 0, 0.7),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.75rem 2.25rem 1rem 2.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .album-title {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 800;
    background: linear-gradient(135deg, #ff4081, #ffd600, #00e5ff);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .sparkle-icon {
    -webkit-text-fill-color: initial;
    font-size: 1.6rem;
  }

  .album-subtitle {
    margin: 0.35rem 0 0 0;
    font-size: 0.95rem;
    color: rgba(255, 255, 255, 0.75);
  }

  .close-button {
    width: 2.75rem;
    height: 2.75rem;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    font-size: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .close-button:hover {
    background: rgba(255, 64, 129, 0.3);
    border-color: rgba(255, 64, 129, 0.6);
    transform: scale(1.05);
  }

  .stats-ribbon {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    padding: 1rem 2.25rem;
    background: rgba(13, 16, 28, 0.5);
  }

  .stat-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 1rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 0.9rem;
    color: #e2e8f0;
  }

  .stat-icon {
    font-size: 1.1rem;
  }

  .stat-value {
    color: #ffd600;
    font-weight: 700;
  }

  .stickers-grid {
    padding: 1.5rem 2.25rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1.25rem;
    overflow-y: auto;
    max-height: 55vh;
  }

  .sticker-card {
    position: relative;
    padding: 1.25rem;
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.03);
    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease;
    overflow: hidden;
    cursor: pointer;
  }

  .sticker-card.tapped {
    animation: badge-spring 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  @keyframes badge-spring {
    0% {
      transform: scale(1);
    }
    35% {
      transform: scale(1.14);
    }
    65% {
      transform: scale(0.95);
    }
    100% {
      transform: scale(1);
    }
  }

  .sticker-card.unlocked {
    border-color: var(--accent-color, #ffd600);
    background: radial-gradient(circle at top, rgba(255, 255, 255, 0.08), rgba(22, 27, 46, 0.7));
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  }

  .sticker-card.unlocked:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(255, 214, 0, 0.25);
  }

  .sticker-card.locked {
    opacity: 0.55;
    background: rgba(10, 12, 20, 0.4);
    border-style: dashed;
  }

  .badge-emblem {
    width: 4.5rem;
    height: 4.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.75rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  .unlocked .badge-emblem {
    background: radial-gradient(circle, var(--accent-color, #ffd600), transparent 70%);
    border-color: var(--accent-color, #ffd600);
    box-shadow: 0 0 16px var(--accent-color, #ffd600);
  }

  .emblem-emoji {
    font-size: 2.5rem;
  }

  .emblem-lock {
    font-size: 2rem;
    color: rgba(255, 255, 255, 0.4);
  }

  .badge-name {
    margin: 0 0 0.35rem 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #ffffff;
  }

  .badge-description {
    margin: 0 0 0.75rem 0;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.3;
  }

  .badge-hint {
    margin: 0 0 0.75rem 0;
    font-size: 0.82rem;
    color: rgba(255, 255, 255, 0.5);
  }

  .unlocked-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    background: rgba(255, 214, 0, 0.2);
    border: 1px solid rgba(255, 214, 0, 0.5);
    color: #ffd600;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.5px;
  }

  .locked-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.75rem;
    font-weight: 700;
  }

  .panel-footer {
    display: flex;
    justify-content: center;
    padding: 1.25rem 2.25rem 1.75rem 2.25rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .resume-button {
    padding: 0.85rem 2.5rem;
    border-radius: 9999px;
    background: linear-gradient(135deg, #ff4081, #7c4dff);
    border: none;
    color: #ffffff;
    font-size: 1.05rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(255, 64, 129, 0.4);
    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease;
  }

  .resume-button:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 28px rgba(255, 64, 129, 0.6);
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
</style>
