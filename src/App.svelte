<script lang="ts">
  import { APP_NAME, APP_TAGLINE } from './lib/constants';

  let count = $state(0);
  let isPressed = $state(false);

  function handleInteraction() {
    count += 1;
    isPressed = true;
    setTimeout(() => {
      isPressed = false;
    }, 150);
  }
</script>

<main class="playground" onpointerdown={handleInteraction}>
  <div class="center-stage">
    <h1 class="brand-title" class:bounce={isPressed}>{APP_NAME}</h1>
    <p class="tagline">{APP_TAGLINE}</p>
    <div class="counter-badge">
      <span>Magical Touches: {count}</span>
    </div>
  </div>
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: #0d0f18;
    color: #ffffff;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    user-select: none;
    -webkit-user-select: none;
  }

  .playground {
    width: 100vw;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .center-stage {
    text-align: center;
  }

  .brand-title {
    font-size: 5rem;
    font-weight: 900;
    margin: 0;
    background: linear-gradient(135deg, #ff6b8b, #ffbe53, #4ecdc4);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    transition: transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }

  .brand-title.bounce {
    transform: scale(1.15) rotate(-2deg);
  }

  .tagline {
    font-size: 1.25rem;
    color: #a0aec0;
    margin: 0.5rem 0 1.5rem 0;
  }

  .counter-badge {
    display: inline-block;
    padding: 0.5rem 1.25rem;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(8px);
    font-weight: 600;
    color: #f7fafc;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }
</style>
