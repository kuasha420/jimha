<!-- Added by AGYIS-HARNESS -->

---

trigger: manual
description: Universal agent rules template for target workspace onboarding
---

<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Arafat Zahan (@kuasha420) -->
<!-- Corporate Stewardship & Infrastructure: Purrfect Software Limited (PSL) -->
<!-- Governed by: ICARO-42/b Ordinance (Company-Supported Personal IP Framework) -->

# Universal Empirical Agent Rules: Agyis Harness Guidelines

These operational rules govern cognitive behavior and human-in-the-loop alignment for software engineering projects powered by the **Agyis Harness**. All deterministic environment guarantees (runtime injection, pager normalization, surgical grep exit sanitization, output compaction) are enforced transparently by harness hooks.

---

## 1. Explicit Project Command Dictionary (The Victory Pattern)

_Explicit CLI palettes yield 10x lower human intervention rates:_

```bash
# 🧪 Project Verification & Native Toolchain
pnpm test                                      # Run complete project test suite
pnpm build                                     # Build project artifacts
pnpm lint                                      # Code quality & linting checks
pnpm dev                                       # Start local development server
pnpm check                                     # Verification & type check
pnpm format                                    # Code style & formatting
pnpm preview                                   # Execute preview
pnpm check:watch                               # Execute check:watch
pnpm lint:fix                                  # Execute lint:fix
pnpm lint:diff                                 # Execute lint:diff
pnpm format:check                              # Execute format:check
pnpm format:diff                               # Execute format:diff

# 🩺 Environment Diagnostics & Auto-Healing
agyis doctor                                   # Audit workstation runtimes & auto-heal
agyis status                                   # Print harness health, active hooks & telemetry

# 🧩 Skills & Subagents Discovery
agyis skills                                   # List installed modular skills & triggers
agyis agents                                   # List registered specialist subagents & tools

# 🌐 Remote Operations & Cloud/Mesh Triage (ADR-027)
agyis remote exec <target> "<cmd>"             # Multiplexed SSH with login-shell promotion
agyis remote script <target> <file>            # Stdin script streaming (zero disk footprint)
agyis remote triage <target>                   # Compact (<2KB) multi-component health report

# 📊 Empirical Telemetry Laboratory
agyis sync                                     # Audit & synchronize active session telemetry
```

---

## 2. Mandatory Project-Native Automated Verification Contract

1. **Mandatory Automated Verification**:
   - Never declare a task "complete", "fixed", or "verified" without executing the active project's native test runner (e.g. `pnpm test`, `pytest`, `cargo test`, `go test`) and asserting exit code 0.
2. **Sub-Second to Fast Benchmark Invariant**:
   - Unit and integration tests must run as fast and hermetically as possible. Avoid slow network calls, unbounded sleeps, or unneeded whole-filesystem sweeps in verification loops.
3. **Hermetic Isolation**:
   - Tests must never access untracked external services without hermetic mocks or local temporary environments. All state-persisting operations should use temporary directories.

---

## 3. Terminal Invariants & Grep Probing Exception (ADR-013)

1. **Pre-flight Tool Availability (Mitigate Exit Code 127)**:
   - Verify tool availability (`command -v <bin>`) or handle fallback paths gracefully.
2. **Context Flood Prevention (The 200+ Step Cliff)**:
   - Never execute unfiltered commands that dump thousands of lines. Pipe large outputs through `head -n <N>`, `tail -n <N>`, or `wc -l`.
3. **Pattern Probing Exception**:
   - Error swallowing is banned in production code, but standalone terminal pattern probes (`grep`, `diff`) without conditionals must use `|| [ $? -eq 1 ]` to avoid panicking on benign empty matches.
4. **Multi-line Script Hygiene**:
   - Write multi-line scripts to temporary scratch files (`scratch/script.sh` or `scratch/script.py`) rather than escaping fragile multi-line bash `-c` one-liners.

---

## 4. Surgical Contiguous Edits Invariant (99.9% Tool Success)

_Audit revealed single contiguous block replacements achieve 99.9% tool success:_

1. Always make single contiguous block replacements for targeted edits (`replace_file_content`).
2. Do NOT overwrite whole files when modifying specific functions, classes, or blocks.
3. Preserve surrounding comments, docstrings, imports, and formatting.

---

## 5. Context Preservation & Subagent Ladder

_Trajectories <50 steps / <50k tokens maintain 0.8 errors/session; >200 steps suffer a 20x error spike:_

1. **Keep Primary Context in the Healthy Zone (<50k tokens)**.
2. **Anti-Loop Heuristics**:
   - Do NOT repeatedly call `view_file` on the same file within consecutive steps.
   - Evolve search queries; do not repeat identical `grep_search` patterns.
   - Never poll task status in a loop (`manage_task(Action='status')`); await reactive wakeups.
3. **Subagent Delegation Protocol**:
   - Decompose multi-phase refactoring, test debugging, or massive build sweeps, delegating to specialist subagents (`@harness_builder`, `@harness_reviewer`, `@harness_auditor`, `@planner`, `@harness_custodian`, `@coordinator`) in isolated worktrees (`Workspace: "share"` or `"branch"`).
   - Follow the 6-stage Ladder lifecycle: Plan -> Implement (Executioner) -> Review (Hammer) -> Commit Gate (Custodian) -> Verification (Auditor) -> Archival (Coordinator).

---

## 6. The Artifact-First Planning Invariant (ADR-012) & Dynamic Aperture

1. **Anti-Chatbot Seduction**:
   - Never propose multi-component architectural changes or execution plans in raw conversational chat turns.
   - All non-trivial proposals must immediately crystallize into an interactive `implementation_plan.md` artifact before requesting operator confirmation.
2. **Dynamic Sliding Aperture**:
   - High resolution for current task execution.
   - Medium resolution for near-future milestones (macro boundaries; no speculative code).
   - Low resolution for far-future vision.
3. **Retroactive Horizon Compaction**:
   - When completing a phase or milestone, compact findings into the project ledger under 50 lines, update the project roadmap, commit clean code to git, and instruct the operator to reset session.

---

## 7. The 5 Ground Rules

1. **Rule 1 (Zero Error Swallowing)**: Never hide or swallow errors. Zero bare `except:`, no unhandled pipe errors (`set -euo pipefail`).
2. **Rule 2 (No Product Homework in Tests)**: Never redefine product logic or duplicate production calculations in test asserts.
3. **Rule 3 (Complete Deliveries)**: Deliver complete packages (code + types + tests + docs). No partial drafts or broken stubs.
4. **Rule 4 (Zero Verification Homework)**: Self-verify all changes using the project's native test runner before declaring completion.
5. **Rule 5 (Stop & Inquire)**: Stop and ask the operator if an unforeseen blocker, architectural conflict, or ambiguity arises.

---

## 8. Human-in-the-Loop & Steering Alignment

1. **Anti-Drift Commitment**: Anchor all implementation decisions to the agreed plan. If novel obstacles arise, pause and present options.
2. **Proactive Confirmation Gates**: When encountering destructive operations (file deletion, git branch force-push, node reboots), pause for explicit review.
3. **Clear Error Reporting**: If a command fails twice, stop thrashing. State the error concisely and propose a concrete path forward.

<!-- End AGYIS-HARNESS -->

---

## Jimha Project Context & Multi-Stack Standards

### Active Technology Stacks & Architectural Roles

- **Frontend / Desktop UI (`typescript` / `desktop_gui` / `frontend`)**: TypeScript 6, Svelte 5 Runes, Pixi.js v8, Vite 8, Vitest 5 (`happy-dom`) in `src/`.
- **Native Desktop Backend & Audio/Input (`rust` / `audio` / `desktop_gui`)**: Rust (Edition 2021), Tauri v2, `rodio`, `gilrs`, and Wayland/KWin kiosk integration in `src-tauri/`.
- **Systems, Packaging & Automation (`systems` / `shell`)**: Bash scripts in `scripts/`, Arch `PKGBUILD`, Flatpak (`org.purrfect.jimha.yml`), and XDG desktop/metainfo files.
- **Historical Archive**: `legacy/python_prototype/` is archival reference only — **not** an active Python runtime stack.

### Full Multi-Stack Verification Commands

```bash
pnpm verify                                    # Full 7-tier gate (build, check, lint, clippy, cargo fmt, vitest, cargo test)
pnpm verify:diff                               # Fast diff gate (eslint diff, vitest related, cargo clippy)
pnpm test:diff                                 # Sub-second Vitest diff-targeted tests
pnpm test:rust                                 # Rust unit tests (cargo test --manifest-path src-tauri/Cargo.toml)
pnpm clippy                                    # Rust Clippy strict lints (-D warnings)
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
pnpm tauri:dev                                 # Launch Tauri desktop dev mode
pnpm tauri:build                               # Build Tauri desktop binary (--no-bundle)
agyis test && agyis test --diff                # Harness verification & completion-fence clearance
```

### Global Layer 1 Skills (Single-Source)

Do **not** copy global plugin skills into `.agents/skills/`. Use the globally loaded Layer 1 skills directly:

- `psl-stack-typescript`, `psl-test-node`, `modern-web-guidance`, `psl-test-harmonize`
- `psl-test-cargo`, `psl-stack-systems`, `psl-stack-shell`
- `display-ops`, `audio-ops`

### Sovereign & Child-Safety Domain Invariants

- Follow `docs/DAD_MODE_INVARIANTS.md` and `docs/ARCHITECTURE.md`: 100% air-gapped sovereign app (0 network sockets/telemetry), 25-bubble FIFO ceiling, 2.5s parent hold-to-exit gate, and strict Rust safety (`unsafe_code = "forbid"`, `unwrap_used = "deny"`).
