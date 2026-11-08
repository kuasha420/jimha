import { describe, it, expect, vi } from 'vitest';
import { mount, unmount } from 'svelte';
import ExitHoldHud from './ExitHoldHud.svelte';
import UnlockCelebrationBanner from './UnlockCelebrationBanner.svelte';
import StickerBook from './StickerBook.svelte';
import type { JimhaAudioManager } from '../audio/audio-manager';

describe('UI Component Invariants', () => {
  it('renders ExitHoldHud with Shift + Esc and remaining seconds', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);

    const component = mount(ExitHoldHud, {
      target: container,
      props: {
        visible: true,
        holdProgress: 0.5,
        maxHoldSeconds: 2.5,
      },
    });

    const text = container.textContent || '';
    expect(text).toContain('Shift + Esc');
    expect(text).toContain('2.5s');

    unmount(component);
    container.remove();
  });

  it('renders ExitHoldHud with custom controller and touch prompts', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);

    const component = mount(ExitHoldHud, {
      target: container,
      props: {
        visible: true,
        progress: 0.75,
        remainingSec: 1.2,
        title: 'CONTROLLER EXIT HOLD...',
        hint: 'Hold SELECT + START to exit • Release to stay',
      },
    });

    const text = container.textContent || '';
    expect(text).toContain('CONTROLLER EXIT HOLD...');
    expect(text).toContain('Hold SELECT + START to exit');
    expect(text).toContain('1.2s');

    unmount(component);
    container.remove();
  });

  it('renders UnlockCelebrationBanner with First Spark and gesture prompt', () => {
    const container = document.createElement('div');
    document.body.appendChild(container);

    const component = mount(UnlockCelebrationBanner, {
      target: container,
      props: {
        unlockedStickerId: 'first_spark',
        visible: true,
        onDismiss: () => {},
      },
    });

    const text = container.textContent || '';
    expect(text).toContain('First Spark');
    expect(text.toUpperCase()).toContain('HOLD OR SWIPE UP TO OPEN STICKER BOOK');

    unmount(component);
    container.remove();
  });

  it('renders StickerBook and replays fanfare on unlocked badge and tap sound on locked badge', () => {
    const playStickerTapSound = vi.fn();
    const playCelebrationFanfare = vi.fn();
    const fakeAudioManager = {
      playStickerTapSound,
      playCelebrationFanfare,
    } as unknown as JimhaAudioManager;

    const container = document.createElement('div');
    document.body.appendChild(container);

    const component = mount(StickerBook, {
      target: container,
      props: {
        isOpen: true,
        unlockedStickers: ['first_spark'],
        audioManager: fakeAudioManager,
        onClose: () => {},
      },
    });

    const cards = container.querySelectorAll('.sticker-card');
    expect(cards.length).toBeGreaterThan(1);

    // Tapping unlocked badge replays celebration fanfare
    const unlockedCard = cards[0] as HTMLElement;
    expect(unlockedCard.classList.contains('unlocked')).toBe(true);
    unlockedCard.click();
    expect(playCelebrationFanfare).toHaveBeenCalled();

    // Tapping locked badge plays chime tap sound
    const lockedCard = cards[1] as HTMLElement;
    expect(lockedCard.classList.contains('locked')).toBe(true);
    lockedCard.click();
    expect(playStickerTapSound).toHaveBeenCalledWith(1);

    unmount(component);
    container.remove();
  });
});
