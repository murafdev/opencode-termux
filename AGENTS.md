# PROJECT KNOWLEDGE BASE

## ACTIVE NATIVE V2 WORK (2026-10-31)

- Native Android/OpenCode v2 `2.2.5` (Bun 1.4.4, OpenTUI 0.8.0) is the current user-facing release. Branch `native-android` is the release line.
- Current user-facing path: `README.md` and `install.sh` installing `~/.local/bin/opencode`. Current build path: `docs/native-v2-build.md` and the native Android workflows.
- Release builds run in GitHub Actions for reproducibility. On-device local builds are allowed; Termux already is Bionic so no NDK. Needs Termux `python3`, `npm`, `clang`, `make` (`zig` only to rebuild OpenTUI), network, and pinned inputs in `tools/supply-chain-lock.json`. Guide: `docs/transplant.md` + `make transplant VER=2.0.26`.
- Source/Bun 1.4.4 release candidate from Actions run 41193063342 passed on-device checksum, `--version`, TUI startup, and clean exit. Publish from a verified CI artifact only; never upload the phone's local copy.
- Keep third-party Actions pinned to immutable commit SHAs. Use v6 action lines when available; do not downgrade to v4.
- Do not replace the manual repository fetch with `actions/checkout` until the malformed upstream `termux-packages` gitlink/submodule metadata is repaired.

**Generated:** 2026-06-12  
**Branch:** pure-android

## OVERVIEW
Termux-first OpenCode build/packaging workspace. Stable mainline since 27/28 is the native bionic line: a single zero-glibc Android ELF produced by the transplant revive pipeline (`tools/transplant/`, `make transplant`; see `docs/transplant.md`). The wrapper line is renamed `opencode-wrapper` and demoted to appendix maintenance (local build path `tools/produce-local.sh` + `scripts/*`); `opencode-wrapper-standalone` is the frozen single-version rollback package that can coexist with `opencode`. `opencode` and `opencode-wrapper` remain mutually exclusive. GitHub Actions workflows are diagnostic/handoff, not final runtime release.

## STRUCTURE
```text
opencode-termux/
├── Makefile                    # top-level orchestration (all/batch/selfcheck/matrix)
├── scripts/                    # staging, packaging, hook runners, CI helper scripts
├── tools/                      # operator-facing CLIs (make wrapper, plugin lifecycle, matrix)
├── packing/                  # package templates + manifests (mixed with generated outputs)
├── docs/                       # canonical runbooks, architecture notes, incident records (e.g. docs/transplant.md)
├── security/                   # OSV gate policy + expiring advisory baseline
├── artifacts/                  # generated runtime/staging outputs (disposable)
└── .github/workflows/          # CI handoff workflows
```

## WHERE TO LOOK
| Task | Location | Notes |
|---|---|---|
| Build orchestration | `Makefile`, `tools/make-opencode` | `make` is source of truth; wrapper maps CLI flags to make vars |
| Prepare runtime artifact | `tools/produce-local.sh` | resolves version, wraps runtime, cleans stale generated dirs |
| Stage install tree | `scripts/build.sh`, `scripts/common.sh` | writes staged prefix + build metadata |
| Build DEB package (wrapper appendix) | `scripts/package/package_deb.sh`, `packing/deb/DEBIAN/control` | builds the `opencode-wrapper` deb; postinst hook calls system-skill runner |
| Build pacman package (wrapper appendix) | `scripts/package/package_pacman.sh`, `packing/pacman/PKGBUILD*` | builds the `opencode-wrapper` pacman package; dynamic pkgver/pkgrel rewrite + makepkg flow |
| Native provider packaging | `scripts/package/package_deb_native.sh`, `scripts/package/package_pacman_native.sh`, `packing/pacman/PKGBUILD.native` | `opencode-native` deb/pacman providers for the native bionic mainline (stable since 27/28; see docs/dual-track-install.md) |
| Standalone rollback packaging | `scripts/package/package_deb_standalone.sh`, `scripts/package/package_pacman_standalone.sh`, `packing/pacman/PKGBUILD.standalone` | `opencode-wrapper-standalone` frozen rollback package (coexists with `opencode`); stage via `STANDALONE=1 ./scripts/build.sh` |
| System-skill hook behavior | `scripts/hooks/run-system-skills.sh`, `packing/manifests/system-skills/*.json` | strict/network flags default to safe mode |
| Plugin lifecycle | `tools/plugin-manager.sh`, `tools/plugin-selfcheck.sh`, `docs/plugin-management.md` | local file plugin path + snapshot rollback model |
| Upgrade/downgrade simulation | `tools/upgrade-matrix.sh`, `docs/execution-checklist.md` | machine2 lifecycle validation with cached deb artifacts |
| Transplant 管线 | `tools/transplant/transplant.py` | 原生 android Bun 拼接 + ELF 复活手术（C1 已复活，见 `docs/transplant.md`） |
| Native Android CI diagnostics | `.github/workflows/build-native-android.yml`, `scripts/ci/build-minimal-bun144-transplant.sh` | opt-in runtime-test candidate workflow; artifacts are diagnostic-only |
| CI armv7 handoff | `.github/workflows/prebuild-armv7.yml`, `scripts/ci/*` | attempt-based build evidence, not final Termux release path |
| Dependency vulnerability gate | `tools/check-osv.py`, `security/osv-baseline.json`, `.github/workflows/security-osv.yml` | scans the pinned upstream lockfile's `@opencode/cli` closure; critical/high findings need an expiring, justified suppression |
| Accepted residual risk | `security/deferred-hardening.md` | per-suppression reachability, below-threshold inventory, Bun RELRO/BIND_NOW status |
| Upstream guard submission | `docs/upstream-opencode-guards.md`, `patches/opencode/` | ready-to-file PR text + generated diffs for the config guards (parsing budgets + normalization failure isolation) |

## CODE MAP
| Symbol | Type | Location | Refs | Role |
|---|---|---|---:|---|
| `all`, `batch`, `selfcheck`, `matrix` | Make targets | `Makefile` | high | primary workflow control surface |
| `build_plugin` | shell function | `tools/plugin-manager.sh` | medium | plugin build pipeline (bun/npm + fallback) |
| `cmd_install` / `cmd_update` / `cmd_rollback` | shell functions | `tools/plugin-manager.sh` | high | plugin lifecycle commands |
| `run-system-skills.sh` entry flow | hook runner | `scripts/hooks/run-system-skills.sh` | high | post-install/post-upgrade hook orchestration |
| `produce-local.sh` main flow | script entrypoint | `tools/produce-local.sh` | medium | runtime acquisition + wrapper + cleanup |
| `upgrade-matrix.sh` main flow | script entrypoint | `tools/upgrade-matrix.sh` | medium | remote install/upgrade/downgrade simulation |

## CONVENTIONS
- Shell scripts use strict mode (`set -euo pipefail`) and fail-fast checks for required binaries/files.
- Runtime/package scripts rely on uppercase env knobs (`VER`, `VERS`, `PKG`, `ODIR`, `MIX`, `STAGED_PREFIX`, `PACKAGER_NAME`).
- Hook execution is explicit and safe-by-default (`OPENCODE_HOOK_STRICT=0`, `OPENCODE_HOOK_ENABLE_NETWORK=0`) in package lifecycle paths.
- Packaging sources live under `packing/*` templates; versioned package files are generated artifacts.

## ANTI-PATTERNS (THIS PROJECT)
- Do not use musl/proot as official Termux final runtime path (`README.md`, `docs/local-production.md`).
- Do not treat CI armv7 handoff artifacts as final release binaries.
- Do not edit generated outputs (`artifacts/`, `packing/dpkg/work/`, `packing/pacman/pkg/`, versioned `.deb` / `.pkg.tar.xz`).
- Do not run staging/packaging scripts against shared or wrong prefixes: several flows use destructive `rm -rf` cleanup.

## UNIQUE STYLES
- Packaging and hook flows are manifest-driven (`packing/manifests/system-skills/*.json`) with idempotency + registry updates.
- Plugin management is Termux-biased toward local `file://.../index.js` registration instead of bare plugin name mode.
- CI armv7 jobs emit JSON status artifacts (`status/*.json`) and logs for diagnosis-first iteration.

## COMMANDS
```bash
# Runtime preparation (mainline local flow)
./tools/produce-local.sh 1.2.10

# Build/package via make
make all VER=1.2.10 PKG=both
make batch VERS='1.2.10 1.2.11' PKG=deb

# Validation
make selfcheck
make matrix VERS='1.2.9 1.2.10' TARGET_HOST=192.168.1.22 TARGET_USER=u0_a258

# Direct package scripts
./scripts/package/package_deb.sh
./scripts/package/package_pacman.sh
```

## NOTES
- `packing/` (default outputs) and `packing/` (templates/manifests) are different; keep them conceptually separate.
- When adding new workflow-critical scripts, update both `docs/README.md` navigation and this root map.

<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->
