/**
 * RekkaBuffer: Arcade combo buffer tracking key sequences with timeout decay.
 * Reference: legacy/python_prototype/jimha/main.py (lines 154-197)
 */

export const KONAMI_SEQUENCE: readonly string[] = [
  'UP',
  'UP',
  'DOWN',
  'DOWN',
  'LEFT',
  'RIGHT',
  'LEFT',
  'RIGHT',
  'B',
  'A',
] as const;

export const QUICK_SWITCH_SEQUENCE: readonly string[] = ['UP', 'UP', 'DOWN', 'DOWN'] as const;

export const NAVIGATOR_SEQUENCE: readonly string[] = ['UP', 'UP'] as const;

export class RekkaBuffer {
  public decayTimeout: number;
  private buffer: string[] = [];
  private lastInputTime: number = 0;

  constructor(decayTimeout: number = 0.8) {
    this.decayTimeout = decayTimeout;
  }

  /**
   * Add a key token to the buffer.
   * Clears if elapsed time since last input exceeds decayTimeout.
   * Caps buffer capacity at 30 entries.
   */
  public add(keyToken: string, now: number = Date.now() / 1000): void {
    if (this.buffer.length > 0 && now - this.lastInputTime > this.decayTimeout) {
      this.buffer = [];
    }
    this.buffer.push(keyToken.toUpperCase());
    this.lastInputTime = now;
    if (this.buffer.length > 30) {
      this.buffer = this.buffer.slice(-30);
    }
  }

  /**
   * Clear the buffer immediately.
   */
  public clear(): void {
    this.buffer = [];
    this.lastInputTime = 0;
  }

  /**
   * Check if decay timeout expired and clear buffer if so.
   * Returns true if decay triggered a clear.
   */
  public checkDecay(now: number = Date.now() / 1000): boolean {
    if (this.buffer.length > 0 && now - this.lastInputTime > this.decayTimeout) {
      this.buffer = [];
      return true;
    }
    return false;
  }

  /**
   * Check if trailing buffer matches the given sequence.
   */
  public matches(sequence: readonly string[] | string[]): boolean {
    if (this.buffer.length < sequence.length) {
      return false;
    }
    const trailing = this.buffer.slice(-sequence.length);
    return trailing.every((token, idx) => token === sequence[idx]?.toUpperCase());
  }

  /**
   * Alias for matches to inspect trailing key sequence.
   */
  public endsWith(sequence: readonly string[] | string[]): boolean {
    return this.matches(sequence);
  }

  /**
   * Get current buffer snapshot.
   */
  public getTokens(): string[] {
    return [...this.buffer];
  }

  /**
   * Get buffer length.
   */
  public get length(): number {
    return this.buffer.length;
  }
}
