import { describe, it, expect } from 'vitest';
import {
  spawnParticleBurst,
  spawnBubble,
  updateParticles,
  updateBubbles,
  GRAVITY,
  MAX_BUBBLES,
  type Particle,
  type FloatingBubble
} from './particles';

describe('Particle Physics & Lifecycle Contract', () => {
  it('spawns requested number of particles with correct initial states', () => {
    const burst = spawnParticleBurst(100, 200, 40);
    expect(burst.length).toBe(40);

    for (const p of burst) {
      expect(p.x).toBe(100);
      expect(p.y).toBe(200);
      expect(p.life).toBe(1.0);
      expect(p.decayRate).toBeGreaterThanOrEqual(0.4);
      expect(p.decayRate).toBeLessThanOrEqual(0.9);
      expect(['star', 'circle', 'heart', 'confetti']).toContain(p.shape);
    }
  });

  it('updates particle physics applying velocity, gravity, and life decay', () => {
    const p: Particle = {
      x: 50,
      y: 50,
      vx: 100,
      vy: 0,
      size: 10,
      color: '#FF4081',
      shape: 'star',
      life: 1.0,
      decayRate: 0.5,
      rotation: 0,
      rotSpeed: 1.0
    };

    const dt = 0.1;
    const updated = updateParticles([p], dt, 1000, GRAVITY);
    expect(updated.length).toBe(1);

    const updatedP = updated[0];
    // x = 50 + 100 * 0.1 = 60
    expect(updatedP.x).toBeCloseTo(60, 2);
    // vy = 0 + 400 * 0.1 = 40
    expect(updatedP.vy).toBeCloseTo(40, 2);
    // y = 50 + 0 * 0.1 = 50 (since initial vy was 0 before dt or step)
    expect(updatedP.y).toBeCloseTo(50, 2);
    // life = 1.0 - 0.5 * 0.1 = 0.95
    expect(updatedP.life).toBeCloseTo(0.95, 2);
  });

  it('culls particles that have fully decayed or fallen past screen bottom', () => {
    const deadP: Particle = {
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      size: 10,
      color: '#FF4081',
      shape: 'circle',
      life: 0.01,
      decayRate: 1.0,
      rotation: 0,
      rotSpeed: 0
    };

    const fallenP: Particle = {
      x: 0,
      y: 1200,
      vx: 0,
      vy: 100,
      size: 10,
      color: '#00E676',
      shape: 'confetti',
      life: 1.0,
      decayRate: 0.1,
      rotation: 0,
      rotSpeed: 0
    };

    const remaining = updateParticles([deadP, fallenP], 0.1, 1000);
    expect(remaining.length).toBe(0);
  });

  it('spawns floating bubbles that move upwards and decay slowly', () => {
    const bubble = spawnBubble(300, 400);
    expect(bubble.x).toBe(300);
    expect(bubble.y).toBe(400);
    expect(bubble.vy).toBeLessThan(0); // upward velocity
    expect(bubble.radius).toBeGreaterThanOrEqual(16);
    expect(bubble.radius).toBeLessThanOrEqual(48);

    const dt = 0.5;
    const updated = updateBubbles([bubble], dt);
    expect(updated.length).toBe(1);
    expect(updated[0].y).toBeLessThan(400);
    expect(updated[0].life).toBeCloseTo(0.925, 3);
  });

  it('caps bubble lagoon at MAX_BUBBLES (25) and prunes excess oldest bubbles', () => {
    expect(MAX_BUBBLES).toBe(25);
    const bubbles: FloatingBubble[] = [];
    for (let i = 0; i < 30; i++) {
      const b = spawnBubble(100 + i, 200);
      b.vx = 0;
      bubbles.push(b);
    }
    const updated = updateBubbles(bubbles, 0.1);
    expect(updated.length).toBe(25);
    // Oldest 5 bubbles (x=100..104) pruned; remaining are x=105..129
    expect(updated[0].x).toBe(105);
    expect(updated[24].x).toBe(129);
  });
});
