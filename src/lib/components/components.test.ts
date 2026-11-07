import { describe, it, expect } from 'vitest';
import { mount, unmount } from 'svelte';
import ExitHoldHud from './ExitHoldHud.svelte';
import UnlockCelebrationBanner from './UnlockCelebrationBanner.svelte';

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
});
