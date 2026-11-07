<script lang="ts">
  export interface WindowItem {
    id: string;
    title: string;
    icon: string;
  }

  interface Props {
    windows: WindowItem[];
    selectedIndex?: number;
    onSelect: (targetId: string) => void;
    onClose: () => void;
  }

  let { windows = [], selectedIndex = $bindable(0), onSelect, onClose }: Props = $props();

  let total = $derived(windows.length);
  let safeIndex = $derived(total > 0 ? ((selectedIndex % total) + total) % total : 0);
  let currentWindow = $derived(
    total > 0
      ? (windows[safeIndex] ?? {
          id: 'desktop',
          title: 'Desktop / Workspace',
          icon: 'user-desktop',
        })
      : { id: 'desktop', title: 'Desktop / Workspace', icon: 'user-desktop' }
  );

  let prevWindow = $derived(
    total > 1 ? (windows[(((safeIndex - 1) % total) + total) % total] ?? null) : null
  );
  let nextWindow = $derived(
    total > 1 ? (windows[(((safeIndex + 1) % total) + total) % total] ?? null) : null
  );

  export function cycleNext() {
    if (total > 0) {
      selectedIndex = (((selectedIndex + 1) % total) + total) % total;
    }
  }

  export function cyclePrev() {
    if (total > 0) {
      selectedIndex = (((selectedIndex - 1) % total) + total) % total;
    }
  }

  export function commitSelection() {
    onSelect(currentWindow.id);
  }

  function handleBackdropClick(e: MouseEvent) {
    if ((e.target as HTMLElement).classList.contains('switcher-backdrop')) {
      onClose();
    }
  }

  function getFallbackEmoji(title: string, icon: string): string {
    const t = (title + ' ' + icon).toLowerCase();
    if (
      t.includes('terminal') ||
      t.includes('konsole') ||
      t.includes('kitty') ||
      t.includes('alacritty') ||
      t.includes('zsh')
    ) {
      return '📟';
    }
    if (
      t.includes('firefox') ||
      t.includes('chrome') ||
      t.includes('browser') ||
      t.includes('edge') ||
      t.includes('brave')
    ) {
      return '🌐';
    }
    if (
      t.includes('discord') ||
      t.includes('vesktop') ||
      t.includes('slack') ||
      t.includes('telegram')
    ) {
      return '💬';
    }
    if (
      t.includes('code') ||
      t.includes('antigravity') ||
      t.includes('cursor') ||
      t.includes('editor')
    ) {
      return '✨';
    }
    if (t.includes('steam') || t.includes('game') || t.includes('lutris') || t.includes('heroic')) {
      return '🎮';
    }
    if (
      t.includes('music') ||
      t.includes('spotify') ||
      t.includes('audio') ||
      t.includes('vlc') ||
      t.includes('media')
    ) {
      return '🎵';
    }
    if (
      t.includes('dolphin') ||
      t.includes('file') ||
      t.includes('nautilus') ||
      t.includes('folder')
    ) {
      return '📁';
    }
    if (t.includes('setting') || t.includes('config') || t.includes('control')) {
      return '⚙️';
    }
    return '🖥️';
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="switcher-backdrop"
  onclick={handleBackdropClick}
  role="dialog"
  aria-modal="true"
  tabindex="-1"
>
  <div class="switcher-container">
    <h2 class="switcher-title">🕹️ REKKA VIRTUAL WINDOW SWITCHER 🕹️</h2>

    <div class="carousel-deck">
      {#if prevWindow}
        <button
          type="button"
          class="flank-card prev-card"
          onclick={() => cyclePrev()}
          aria-label={`Previous window: ${prevWindow.title}`}
        >
          {#if prevWindow.icon && prevWindow.icon.startsWith('data:image')}
            <img class="card-icon-img" src={prevWindow.icon} alt={prevWindow.title} />
          {:else}
            <div class="card-icon">{getFallbackEmoji(prevWindow.title, prevWindow.icon)}</div>
          {/if}
          <div class="card-title">{prevWindow.title}</div>
        </button>
      {/if}

      <button
        type="button"
        class="active-card"
        onclick={() => commitSelection()}
        aria-label={`Active window: ${currentWindow.title}. Click to switch.`}
      >
        {#if currentWindow.icon && currentWindow.icon.startsWith('data:image')}
          <img class="active-icon-img" src={currentWindow.icon} alt={currentWindow.title} />
        {:else}
          <div class="active-icon">{getFallbackEmoji(currentWindow.title, currentWindow.icon)}</div>
        {/if}
        <div class="active-title">{currentWindow.title}</div>
        <div class="active-pos">
          Window [ {safeIndex + 1} of {Math.max(1, total)} ]
        </div>
      </button>

      {#if nextWindow}
        <button
          type="button"
          class="flank-card next-card"
          onclick={() => cycleNext()}
          aria-label={`Next window: ${nextWindow.title}`}
        >
          {#if nextWindow.icon && nextWindow.icon.startsWith('data:image')}
            <img class="card-icon-img" src={nextWindow.icon} alt={nextWindow.title} />
          {:else}
            <div class="card-icon">{getFallbackEmoji(nextWindow.title, nextWindow.icon)}</div>
          {/if}
          <div class="card-title">{nextWindow.title}</div>
        </button>
      {/if}
    </div>

    <footer class="instruction-pill">
      <span>[← / ↑ Prev]</span>
      <span class="sep">•</span>
      <span>[→ / ↓ Next]</span>
      <span class="sep">•</span>
      <span class="enter-hint">[ENTER: Switch to App]</span>
      <span class="sep">•</span>
      <span>[ESC: Stay in Jimha]</span>
    </footer>
  </div>
</div>

<style>
  .switcher-backdrop {
    position: absolute;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 200;
  }

  .switcher-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2.5rem;
    max-width: 90vw;
  }

  .switcher-title {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: 1px;
    color: #00e5ff;
    text-shadow: 0 0 16px rgba(0, 229, 255, 0.4);
  }

  .carousel-deck {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
  }

  .flank-card {
    width: 220px;
    height: 160px;
    border-radius: 18px;
    background: rgba(15, 25, 45, 0.45);
    border: 2px solid rgba(0, 229, 255, 0.35);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 1rem;
    cursor: pointer;
    transition:
      transform 0.2s ease,
      border-color 0.2s ease;
    color: rgba(255, 255, 255, 0.65);
  }

  .flank-card:hover {
    transform: scale(1.05);
    border-color: rgba(0, 229, 255, 0.8);
    color: #ffffff;
  }

  .active-card {
    width: 480px;
    height: 280px;
    border-radius: 24px;
    background: rgba(15, 25, 45, 0.95);
    border: 3px solid #ffd600;
    box-shadow: 0 8px 32px rgba(255, 214, 0, 0.35);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.25rem;
    padding: 1.5rem 2rem;
    text-align: center;
    cursor: pointer;
    font-family: inherit;
    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease;
  }

  .active-card:hover {
    transform: scale(1.02);
    box-shadow: 0 12px 40px rgba(255, 214, 0, 0.5);
  }

  .card-icon {
    font-size: 2.2rem;
  }

  .card-icon-img {
    width: 48px;
    height: 48px;
    object-fit: contain;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.4));
  }

  .active-icon {
    font-size: 3.8rem;
  }

  .active-icon-img {
    width: 80px;
    height: 80px;
    object-fit: contain;
    filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.5));
    animation: icon-float 2.5s ease-in-out infinite;
  }

  @keyframes icon-float {
    0%,
    100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-5px);
    }
  }

  .card-title {
    font-size: 0.95rem;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }

  .active-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #ffffff;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }

  .active-pos {
    font-size: 1rem;
    font-weight: 700;
    color: #00e5ff;
    letter-spacing: 0.5px;
  }

  .instruction-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 1.6rem;
    border-radius: 9999px;
    background: rgba(15, 15, 30, 0.88);
    border: 1.5px solid rgba(0, 229, 255, 0.6);
    font-size: 0.95rem;
    font-weight: 700;
    color: #ffffff;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  }

  .sep {
    color: #00e5ff;
  }

  .enter-hint {
    color: #ffd600;
  }
</style>
