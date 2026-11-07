<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Application, Container, Graphics, Text, TextStyle } from 'pixi.js';
  import { PALETTE, getRandomColor, resolveKeyDisplay } from '../engine/palette';
  import { calculateElasticScale, calculateCardAlpha } from '../engine/spring';
  import {
    spawnParticleBurst,
    spawnBubble,
    updateParticles,
    updateBubbles,
    type Particle,
    type FloatingBubble
  } from '../engine/particles';

  interface Props {
    onBubblePop?: (bubble: FloatingBubble) => void;
    onKeyTriggered?: (title: string, subtitle: string) => void;
  }

  const { onBubblePop, onKeyTriggered }: Props = $props();

  let containerEl: HTMLDivElement | null = $state(null);
  let app: Application | null = null;
  let isDestroyed = false;

  // Active state
  let currentTitle = $state('JIMHA');
  let currentSubtitle = $state('💖 Smash any button to play! 💖');
  let currentEmoji = $state('✨');
  let currentColor = $state('#FF4081');
  let cardAge = $state(0.0);
  let backgroundHue = $state(260.0);

  // Entities
  let particles: Particle[] = [];
  let bubbles: FloatingBubble[] = [];
  let bgStars: { relX: number; relY: number; size: number; phase: number }[] = [];

  // Containers
  let bgGraphics: Graphics | null = null;
  let particleGraphics: Graphics | null = null;
  let bubbleGraphics: Graphics | null = null;
  let stageContainer: Container | null = null;
  let haloGraphics: Graphics | null = null;
  let keyTitleText: Text | null = null;
  let keyShadowText: Text | null = null;
  let subtitleContainer: Container | null = null;
  let subtitleBg: Graphics | null = null;
  let subtitleText: Text | null = null;

  // Star initialization for background
  for (let i = 0; i < 70; i++) {
    bgStars.push({
      relX: Math.random(),
      relY: Math.random(),
      size: 2.0 + Math.random() * 3.0,
      phase: Math.random() * Math.PI * 2
    });
  }

  export function triggerKey(
    keyInput: string,
    customSubtitle?: string,
    customEmoji?: string,
    customColor?: string
  ): void {
    const resolved = resolveKeyDisplay(keyInput);
    currentTitle = resolved.title;
    currentSubtitle = customSubtitle ?? resolved.subtitle;
    currentEmoji = customEmoji ?? resolved.emoji;
    currentColor = customColor ?? resolved.color ?? getRandomColor();
    cardAge = 0.0;

    if (app && app.screen) {
      const cx = app.screen.width / 2;
      const cy = app.screen.height / 2;
      const newParticles = spawnParticleBurst(cx, cy, 45);
      particles.push(...newParticles);
    }

    if (onKeyTriggered) {
      onKeyTriggered(currentTitle, currentSubtitle);
    }

    updateStageText();
  }

  export function spawnInteractiveBubble(x: number, y: number): void {
    const bubble = spawnBubble(x, y);
    bubbles.push(bubble);
    const burst = spawnParticleBurst(x, y, 16);
    particles.push(...burst);

    if (onBubblePop) {
      onBubblePop(bubble);
    }
  }

  function updateStageText(): void {
    if (!keyTitleText || !keyShadowText || !subtitleText || !app) return;

    const width = app.screen.width;
    const height = app.screen.height;
    const minDim = Math.min(width, height);
    const fontSize = Math.max(48, Math.round(minDim * 0.26));
    const subFontSize = Math.max(16, Math.round(minDim * 0.045));

    // Update title text and shadow
    keyTitleText.text = currentTitle;
    keyShadowText.text = currentTitle;

    keyTitleText.style = new TextStyle({
      fontFamily: 'Cantarell, system-ui, -apple-system, sans-serif',
      fontSize,
      fontWeight: '900',
      fill: currentColor
    });

    keyShadowText.style = new TextStyle({
      fontFamily: 'Cantarell, system-ui, -apple-system, sans-serif',
      fontSize,
      fontWeight: '900',
      fill: '#000000'
    });

    keyTitleText.anchor.set(0.5, 0.5);
    keyShadowText.anchor.set(0.5, 0.5);
    keyShadowText.position.set(6, 6);

    // Update subtitle text & background badge
    subtitleText.text = currentSubtitle;
    subtitleText.style = new TextStyle({
      fontFamily: 'Cantarell, system-ui, -apple-system, sans-serif',
      fontSize: subFontSize,
      fontWeight: '700',
      fill: '#FFFFFF'
    });
    subtitleText.anchor.set(0.5, 0.5);

    const subBounds = subtitleText.getLocalBounds();
    const badgeW = subBounds.width + 48;
    const badgeH = subBounds.height + 20;
    const badgeY = fontSize * 0.55 + 35;

    if (subtitleContainer && subtitleBg) {
      subtitleContainer.position.set(0, badgeY);
      subtitleBg.clear();
      subtitleBg
        .roundRect(-badgeW / 2, -badgeH / 2, badgeW, badgeH, 20)
        .fill({ color: 0x000000, alpha: 0.65 })
        .stroke({ color: 0xffffff, alpha: 0.7, width: 2 });
    }
  }

  function drawStar(g: Graphics, cx: number, cy: number, r: number, color: string, alpha: number, points: number = 5): void {
    const step = Math.PI / points;
    const innerR = r * 0.45;
    const poly: number[] = [];
    for (let i = 0; i < 2 * points; i++) {
      const radius = i % 2 === 0 ? r : innerR;
      const angle = i * step - Math.PI / 2;
      poly.push(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
    }
    g.poly(poly).fill({ color, alpha });
  }

  function drawHeart(g: Graphics, cx: number, cy: number, size: number, color: string, alpha: number): void {
    const s = size * 0.6;
    g.moveTo(cx, cy + s * 0.3)
      .bezierCurveTo(cx - s, cy - s * 0.7, cx - s * 1.2, cy + s * 0.2, cx, cy + s)
      .bezierCurveTo(cx + s * 1.2, cy + s * 0.2, cx + s, cy - s * 0.7, cx, cy + s * 0.3)
      .fill({ color, alpha });
  }

  onMount(async () => {
    if (!containerEl) return;

    app = new Application();
    await app.init({
      resizeTo: containerEl,
      antialias: true,
      resolution: window.devicePixelRatio || 1,
      autoDensity: true,
      backgroundColor: 0x0d0f18
    });

    if (isDestroyed) {
      app.destroy(true, { children: true, texture: true });
      return;
    }

    containerEl.appendChild(app.canvas);

    // 1. Background layer
    bgGraphics = new Graphics();
    app.stage.addChild(bgGraphics);

    // 2. Liquid bubble layer
    bubbleGraphics = new Graphics();
    app.stage.addChild(bubbleGraphics);

    // 3. Particle fireworks layer
    particleGraphics = new Graphics();
    app.stage.addChild(particleGraphics);

    // 4. Center-stage typography and glowing halo container
    stageContainer = new Container();
    app.stage.addChild(stageContainer);

    haloGraphics = new Graphics();
    stageContainer.addChild(haloGraphics);

    keyShadowText = new Text();
    keyTitleText = new Text();
    stageContainer.addChild(keyShadowText);
    stageContainer.addChild(keyTitleText);

    subtitleContainer = new Container();
    subtitleBg = new Graphics();
    subtitleText = new Text();
    subtitleContainer.addChild(subtitleBg);
    subtitleContainer.addChild(subtitleText);
    stageContainer.addChild(subtitleContainer);

    updateStageText();

    // Responsive resize listener
    window.addEventListener('resize', handleResize);

    // Frame Ticker Loop (Dynamic Framerate: 120/60 FPS active, 30 FPS idle)
    app.ticker.add((ticker) => {
      const dt = Math.max(0.001, Math.min(0.1, ticker.deltaMS / 1000.0));
      const width = app!.screen.width;
      const height = app!.screen.height;
      const centerStageX = width / 2;
      const centerStageY = height / 2;

      // Update card age & spring scale
      cardAge += dt;
      const scale = calculateElasticScale(cardAge);
      const alpha = calculateCardAlpha(cardAge);

      // Framerate scaling check
      const hasActiveFx = particles.length > 0 || bubbles.length > 0 || cardAge < 1.2;
      app!.ticker.maxFPS = hasActiveFx ? 120 : 30;

      // Slowly shift background hue
      backgroundHue = (backgroundHue + dt * 3.0) % 360.0;

      // 1. Render dynamic background with twilight glow & twinkling stars
      if (bgGraphics) {
        bgGraphics.clear();

        // Subtle gradient simulation via background box and radial glow
        const nowSec = performance.now() / 1000.0;
        for (let i = 0; i < bgStars.length; i++) {
          const star = bgStars[i];
          const twinkle = 0.5 + 0.5 * Math.sin(nowSec * 2.5 + star.phase);
          bgGraphics.circle(star.relX * width, star.relY * height, star.size)
            .fill({ color: 0xffffff, alpha: 0.25 + 0.55 * twinkle });
        }
      }

      // 2. Render floating liquid bubbles with specular highlights
      bubbles = updateBubbles(bubbles, dt);
      if (bubbleGraphics) {
        bubbleGraphics.clear();
        for (let i = 0; i < bubbles.length; i++) {
          const b = bubbles[i];
          // Main bubble body
          bubbleGraphics
            .circle(b.x, b.y, b.radius)
            .fill({ color: b.color, alpha: 0.35 * b.life })
            .stroke({ color: 0xffffff, alpha: 0.65 * b.life, width: 2.5 });

          // Specular light reflection
          bubbleGraphics
            .circle(b.x - b.radius * 0.35, b.y - b.radius * 0.35, b.radius * 0.24)
            .fill({ color: 0xffffff, alpha: 0.75 * b.life });
        }
      }

      // 3. Render multi-shaped particle fireworks
      particles = updateParticles(particles, dt, height);
      if (particleGraphics) {
        particleGraphics.clear();
        for (let i = 0; i < particles.length; i++) {
          const p = particles[i];
          const pLife = Math.max(0, Math.min(1, p.life));

          if (p.shape === 'circle') {
            particleGraphics.circle(p.x, p.y, p.size / 2).fill({ color: p.color, alpha: pLife });
          } else if (p.shape === 'confetti') {
            particleGraphics.rect(p.x - p.size / 2, p.y - p.size / 4, p.size, p.size / 2).fill({ color: p.color, alpha: pLife });
          } else if (p.shape === 'star') {
            drawStar(particleGraphics, p.x, p.y, p.size / 2, p.color, pLife);
          } else if (p.shape === 'heart') {
            drawHeart(particleGraphics, p.x, p.y, p.size, p.color, pLife);
          }
        }
      }

      // 4. Update center-stage scale and radial glowing halo
      if (stageContainer) {
        stageContainer.position.set(centerStageX, centerStageY);
        stageContainer.scale.set(scale, scale);
        stageContainer.alpha = alpha;
      }

      if (haloGraphics) {
        haloGraphics.clear();
        const minDim = Math.min(width, height);
        const haloRadius = minDim * 0.38;

        for (let r = 0; r < 4; r++) {
          const stepR = haloRadius * (1.0 - r * 0.22);
          const haloAlpha = (0.05 + (4 - r) * 0.04) * alpha;
          haloGraphics.circle(0, 0, stepR).fill({ color: currentColor, alpha: haloAlpha });
        }
      }
    });
  });

  function handleResize(): void {
    if (!app || !containerEl) return;
    app.resize();
    updateStageText();
  }

  function handlePointerDown(e: PointerEvent): void {
    if (!containerEl) return;
    const rect = containerEl.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    spawnInteractiveBubble(x, y);
  }

  onDestroy(() => {
    isDestroyed = true;
    window.removeEventListener('resize', handleResize);
    if (app) {
      app.destroy(true, { children: true, texture: true });
      app = null;
    }
  });
</script>

<div
  class="pixi-canvas-wrapper"
  bind:this={containerEl}
  onpointerdown={handlePointerDown}
  role="presentation"
></div>

<style>
  .pixi-canvas-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    touch-action: none;
    user-select: none;
    -webkit-user-select: none;
    cursor: pointer;
  }
</style>
