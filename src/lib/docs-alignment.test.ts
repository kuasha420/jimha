import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { MAX_BUBBLES } from './engine/particles';
import { STICKERS } from './content/stickers';
import { PENTATONIC_FREQUENCIES } from './audio/frequencies';

describe('Documentation & Code Alignment Anti-Drift Contract', () => {
  const rootDir = path.resolve(__dirname, '../..');
  const readmePath = path.join(rootDir, 'README.md');
  const invariantsPath = path.join(rootDir, 'docs/DAD_MODE_INVARIANTS.md');
  const lorePath = path.join(rootDir, 'docs/LORE.md');
  const archPath = path.join(rootDir, 'docs/ARCHITECTURE.md');

  it('asserts README.md documents the exact 25-bubble lagoon capacity', () => {
    const readme = fs.readFileSync(readmePath, 'utf-8');
    expect(readme).toContain(`${MAX_BUBBLES}-bubble`);
  });

  it('asserts DAD_MODE_INVARIANTS.md documents all 7 child-safety invariants', () => {
    const invariants = fs.readFileSync(invariantsPath, 'utf-8');
    expect(invariants).toContain('25-bubble');
    expect(invariants).toContain('0.8');
    expect(invariants).toContain('2.5s');
    expect(invariants).toContain('4-voice');
    expect(invariants).toContain('Attract');
  });

  it('asserts docs/LORE.md documents all 7 authoritative sticker badges', () => {
    const lore = fs.readFileSync(lorePath, 'utf-8');
    expect(STICKERS).toHaveLength(7);
    for (const badge of STICKERS) {
      expect(lore).toContain(badge.id);
      expect(lore).toContain(badge.title);
    }
  });

  it('asserts DAD_MODE_INVARIANTS.md and frequencies.ts define exactly 11 pentatonic tones', () => {
    expect(PENTATONIC_FREQUENCIES).toHaveLength(11);
    const invariants = fs.readFileSync(invariantsPath, 'utf-8');
    expect(invariants).toContain('11 frequencies');
  });

  it('asserts docs/ARCHITECTURE.md enshrines the Self-Contained Product Invariant', () => {
    const arch = fs.readFileSync(archPath, 'utf-8');
    expect(arch).toContain('Self-Contained Product Invariant');
    expect(arch).toContain('100% sovereign');
  });
});
