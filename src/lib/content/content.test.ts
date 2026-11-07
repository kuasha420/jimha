import { describe, it, expect } from 'vitest';
import { NUMBERS_0_20, getNumberContent, getStarString } from './numbers';
import { SENSORY_SHAPES, getShapeContent } from './shapes';
import { SENSORY_COLORS, getColorContent } from './colors';
import { ALL_INSTRUMENTS, getInstrumentConfig, INSTRUMENTS } from './instruments';
import { STICKERS, getStickerById } from './stickers';
import { synthesizeChimeSamples } from '../audio/synth-dsp';
import { resolveKeyDisplay } from '../engine/palette';

describe('Numbers Content Pack', () => {
  it('contains exactly 21 numbers from 0 to 20', () => {
    expect(NUMBERS_0_20).toHaveLength(21);
    expect(NUMBERS_0_20[0].number).toBe(0);
    expect(NUMBERS_0_20[20].number).toBe(20);
  });

  it('generates correct star strings', () => {
    expect(getStarString(0)).toBe('✨');
    expect(getStarString(3)).toBe('⭐⭐⭐');
    expect(getStarString(10)).toBe('⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐');
  });

  it('correctly retrieves number content by value', () => {
    const zero = getNumberContent(0);
    expect(zero).toBeDefined();
    expect(zero?.word).toBe('Zero');
    expect(zero?.starCount).toBe(0);

    const seven = getNumberContent(7);
    expect(seven).toBeDefined();
    expect(seven?.word).toBe('Seven');
    expect(seven?.starCount).toBe(7);

    expect(getNumberContent(25)).toBeUndefined();
  });
});

describe('Sensory Shapes Pack', () => {
  it('contains all 7 core shapes', () => {
    expect(SENSORY_SHAPES).toHaveLength(7);
    const ids = SENSORY_SHAPES.map((s) => s.id);
    expect(ids).toContain('circle');
    expect(ids).toContain('square');
    expect(ids).toContain('triangle');
    expect(ids).toContain('star');
    expect(ids).toContain('heart');
    expect(ids).toContain('diamond');
    expect(ids).toContain('hexagon');
  });

  it('retrieves shapes case-insensitively by id or name', () => {
    expect(getShapeContent('circle')?.name).toBe('Circle');
    expect(getShapeContent('TRIANGLE')?.id).toBe('triangle');
    expect(getShapeContent('Heart')?.particleShape).toBe('heart');
    expect(getShapeContent('unknown')).toBeUndefined();
  });
});

describe('Sensory Colors Pack', () => {
  it('has high-contrast sensory colors with valid hex format', () => {
    expect(SENSORY_COLORS.length).toBeGreaterThanOrEqual(9);
    for (const color of SENSORY_COLORS) {
      expect(color.hex).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(color.name.length).toBeGreaterThan(0);
      expect(color.emoji.length).toBeGreaterThan(0);
    }
  });

  it('finds color by name or hex', () => {
    expect(getColorContent('Electric Mint')?.hex).toBe('#00E676');
    expect(getColorContent('#FF4081')?.name).toBe('Bubblegum Pink');
  });
});

describe('Instruments & Timbre DSP Synthesis', () => {
  it('configures 4 distinct instruments', () => {
    expect(ALL_INSTRUMENTS).toHaveLength(4);
    expect(INSTRUMENTS.celesta.name).toBe('Celesta');
    expect(INSTRUMENTS.marimba.name).toBe('Wooden Marimba');
    expect(INSTRUMENTS.kalimba.name).toBe('Gentle Kalimba');
    expect(INSTRUMENTS.music_box.name).toBe('Music Box');
  });

  it('synthesizes distinct harmonic audio samples for each instrument', () => {
    const sr = 44100;
    const dur = 0.1;
    const freq = 440;

    for (const inst of ALL_INSTRUMENTS) {
      const chime = synthesizeChimeSamples(freq, sr, dur, inst.id);
      expect(chime.left.length).toBe(Math.floor(sr * dur));
      expect(chime.right.length).toBe(Math.floor(sr * dur));
      expect(chime.peak).toBeGreaterThan(0);
      // Assert audio is bounded within [-1.0, 1.0]
      let minVal = 0;
      let maxVal = 0;
      for (let i = 0; i < chime.left.length; i++) {
        if (chime.left[i] < minVal) minVal = chime.left[i];
        if (chime.left[i] > maxVal) maxVal = chime.left[i];
      }
      expect(minVal).toBeGreaterThanOrEqual(-1.0);
      expect(maxVal).toBeLessThanOrEqual(1.0);
    }
  });

  it('falls back to celesta for unknown instrument', () => {
    expect(getInstrumentConfig('flute').id).toBe('celesta');
  });
});

describe('Stickers Content Pack', () => {
  it('defines all 7 achievement badges', () => {
    expect(STICKERS).toHaveLength(7);
    const ids = STICKERS.map((s) => s.id);
    expect(ids).toEqual([
      'first_spark',
      'bubble_popper',
      'jimha_crown',
      'jim_heart',
      'star_counter',
      'rainbow_explorer',
      'konami_champion',
    ]);
  });

  it('retrieves sticker by id', () => {
    const crown = getStickerById('jimha_crown');
    expect(crown).toBeDefined();
    expect(crown?.title).toBe('Queen Jimha 👑');

    const spark = getStickerById('first_spark');
    expect(spark?.title).toBe('First Spark ✨');

    const heart = getStickerById('jim_heart');
    expect(heart?.title).toBe('Jim Heart ❤️');

    expect(getStickerById('unknown')).toBeUndefined();
  });
});

describe('Palette and Numbers Integration', () => {
  it('resolves numeric keys to rich sensory numbers content', () => {
    const disp0 = resolveKeyDisplay('0');
    expect(disp0.title).toBe('0');
    expect(disp0.subtitle).toBe('Zero sparkle stars! ✨');
    expect(disp0.color).toBe('#00E5FF');

    const disp5 = resolveKeyDisplay('5');
    expect(disp5.title).toBe('5');
    expect(disp5.subtitle).toContain('5 Sparkling Stars!');
    expect(disp5.color).toBe('#E040FB');
  });

  it('normalizes Queen Jimha in alphabet companions', () => {
    const dispJ = resolveKeyDisplay('J');
    expect(dispJ.subtitle).toContain('Jimha');
    expect(dispJ.subtitle).not.toContain('JimHa');
  });

  it('resolves H for Heart without duplicate hearts or explicit easter egg', () => {
    const dispH = resolveKeyDisplay('H');
    expect(dispH.title).toBe('H');
    expect(dispH.subtitle).toBe('H is for Heart ❤️');
    expect(dispH.emoji).toBe('❤️');
  });

  it('correctly resolves Space key without collapsing to KEY', () => {
    const space1 = resolveKeyDisplay(' ');
    expect(space1.title).toBe('SPACE');
    expect(space1.subtitle).toContain('COSMIC SUPERNOVA');

    const space2 = resolveKeyDisplay('Spacebar');
    expect(space2.title).toBe('SPACE');

    const space3 = resolveKeyDisplay('space');
    expect(space3.title).toBe('SPACE');
  });
});
