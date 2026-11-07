import { describe, it, expect } from 'vitest';
import { APP_NAME, APP_ID, APP_VERSION } from './constants';

describe('Jimha Core Metadata and Brand Naming', () => {
  it('enforces strict brand naming: Jimha instead of JimHa', () => {
    expect(APP_NAME).toBe('Jimha');
    expect(APP_NAME).not.toBe('JimHa');
  });

  it('declares the authoritative application identifier', () => {
    expect(APP_ID).toBe('org.purrfect.jimha');
  });

  it('asserts version 2.0.0 milestone', () => {
    expect(APP_VERSION).toBe('2.0.0');
  });
});
