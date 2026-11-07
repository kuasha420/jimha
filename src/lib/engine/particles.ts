import { PALETTE, getRandomColor } from './palette';

export type ParticleShape = 'star' | 'circle' | 'heart' | 'confetti';

export interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  shape: ParticleShape;
  life: number; // 1.0 to 0.0
  decayRate: number;
  rotation: number; // in radians or degrees
  rotSpeed: number;
}

export interface FloatingBubble {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
  life: number; // 1.0 to 0.0
}

export const GRAVITY = 400.0; // px/s^2

export function spawnParticleBurst(
  x: number,
  y: number,
  count: number = 35,
  palette: readonly string[] = PALETTE
): Particle[] {
  const shapes: ParticleShape[] = ['star', 'circle', 'heart', 'confetti'];
  const particles: Particle[] = [];

  for (let i = 0; i < count; i++) {
    const angle = Math.random() * 2 * Math.PI;
    const speed = 150.0 + Math.random() * 600.0; // 150 - 750 px/s
    const vx = Math.cos(angle) * speed;
    const vy = Math.sin(angle) * speed - (50.0 + Math.random() * 150.0);
    const size = 8.0 + Math.random() * 16.0;
    const color = getRandomColor(palette);
    const shape = shapes[Math.floor(Math.random() * shapes.length)] ?? 'circle';
    const decayRate = 0.4 + Math.random() * 0.5; // 0.4 - 0.9 per second
    const rotSpeed = (Math.random() * 720.0 - 360.0) * (Math.PI / 180.0); // rad/s

    particles.push({
      x,
      y,
      vx,
      vy,
      size,
      color,
      shape,
      life: 1.0,
      decayRate,
      rotation: Math.random() * 2 * Math.PI,
      rotSpeed,
    });
  }

  return particles;
}

export function spawnBubble(x: number, y: number, color?: string): FloatingBubble {
  const radius = 16.0 + Math.random() * 32.0; // 16 to 48 px
  const chosenColor = color || getRandomColor();
  const vx = Math.random() * 80.0 - 40.0; // -40 to +40 px/s
  const vy = -(40.0 + Math.random() * 80.0); // -40 to -120 px/s (float upwards)

  return {
    x,
    y,
    vx,
    vy,
    radius,
    color: chosenColor,
    life: 1.0,
  };
}

export function updateParticles(
  particles: Particle[],
  dt: number,
  height: number,
  gravity: number = GRAVITY
): Particle[] {
  const alive: Particle[] = [];

  for (const p of particles) {
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy += gravity * dt;
    p.rotation += p.rotSpeed * dt;
    p.life -= p.decayRate * dt;

    if (p.life > 0 && p.y < height + 100) {
      alive.push(p);
    }
  }

  return alive;
}

export const MAX_BUBBLES = 25;

export function updateBubbles(
  bubbles: FloatingBubble[],
  dt: number,
  maxBubbles: number = MAX_BUBBLES
): FloatingBubble[] {
  const alive: FloatingBubble[] = [];

  for (const b of bubbles) {
    b.x += b.vx * dt;
    b.y += b.vy * dt;
    b.life -= 0.15 * dt;

    if (b.life > 0 && b.y > -100) {
      alive.push(b);
    }
  }

  if (alive.length > maxBubbles) {
    return alive.slice(alive.length - maxBubbles);
  }

  return alive;
}
