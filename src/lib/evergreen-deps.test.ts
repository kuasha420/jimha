import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

function parseMajorVersion(versionStr: string): number {
  const clean = versionStr.replace(/^[\^~>=<]/, '').trim();
  const major = parseInt(clean.split('.')[0] || '0', 10);
  return major;
}

describe('Evergreen Dependencies Verification Contract', () => {
  const rootDir = path.resolve(__dirname, '../..');
  const packageJsonPath = path.join(rootDir, 'package.json');
  const cargoTomlPath = path.join(rootDir, 'src-tauri/Cargo.toml');

  const pkg = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8')) as {
    dependencies: Record<string, string>;
    devDependencies: Record<string, string>;
  };
  const cargoToml = fs.readFileSync(cargoTomlPath, 'utf-8');

  it('asserts modern major versions across frontend toolchain (TS>=6, Vite>=8, Svelte>=5, Pixi>=8, Vitest>=5)', () => {
    const tsVersion = pkg.devDependencies['typescript'] || '';
    expect(tsVersion).toBeTruthy();
    expect(parseMajorVersion(tsVersion)).toBeGreaterThanOrEqual(6);

    const viteVersion = pkg.devDependencies['vite'] || '';
    expect(viteVersion).toBeTruthy();
    expect(parseMajorVersion(viteVersion)).toBeGreaterThanOrEqual(8);

    const svelteVersion = pkg.devDependencies['svelte'] || '';
    expect(svelteVersion).toBeTruthy();
    expect(parseMajorVersion(svelteVersion)).toBeGreaterThanOrEqual(5);

    const pixiVersion = pkg.dependencies['pixi.js'] || '';
    expect(pixiVersion).toBeTruthy();
    expect(parseMajorVersion(pixiVersion)).toBeGreaterThanOrEqual(8);

    const vitestVersion = pkg.devDependencies['vitest'] || '';
    expect(vitestVersion).toBeTruthy();
    expect(parseMajorVersion(vitestVersion)).toBeGreaterThanOrEqual(5);
  });

  it('asserts zero wildcard versions across dependencies and devDependencies', () => {
    const allDeps = { ...pkg.dependencies, ...pkg.devDependencies };
    for (const [name, version] of Object.entries(allDeps)) {
      expect(version, `Package ${name} has wildcard version`).not.toBe('*');
      expect(version, `Package ${name} contains wildcard`).not.toContain('*');
    }
  });

  it('asserts zero deprecated or obsolete dependencies', () => {
    const allDeps = { ...pkg.dependencies, ...pkg.devDependencies };
    const bannedPackages = ['rimraf', 'left-pad', 'request', 'urllib', 'ts-node', 'gulp'];
    for (const banned of bannedPackages) {
      expect(allDeps[banned], `Found deprecated package: ${banned}`).toBeUndefined();
    }
  });

  it('asserts src-tauri/Cargo.toml specifies modern Rust edition 2021, tauri v2, zbus absent, and unsafe_code forbidden', () => {
    expect(cargoToml).toMatch(/edition\s*=\s*"2021"/);
    expect(cargoToml).toMatch(/tauri\s*=\s*\{\s*version\s*=\s*"2"/);
    expect(cargoToml).not.toContain('zbus');
    expect(cargoToml).toContain('unsafe_code = "forbid"');
    expect(cargoToml).toContain('[lints.clippy]');
    expect(cargoToml).toContain('unwrap_used = "deny"');
  });
});
