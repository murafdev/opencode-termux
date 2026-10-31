# OpenCode 2.2.5 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.2.5` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.2.5-bun144.1` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.8.0 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.2.5`.

## What changed

- OpenCode updated to `2.2.5` from pinned upstream commit `9bbb8ce18c80f099e0e448775f59d965ead40a21`; its pinned Bun source toolchain is `1.4.4`.
- Bionic OpenTUI renderer updated to `0.8.0`, with the Android hardening patches re-verified against the 0.8.0 source: file-prefix mapping, the self-contained TLSDESC resolver, the Android 11+ heap-pointer-tagging opt-out, and the scissor/rect overflow guards. OpenTUI 0.8.0 clamps viewport origins in i64, so the older extreme-origin short-circuits are no longer needed.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 669 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The 2.2.5 dependency refresh keeps nine previously suppressed critical/high advisories cleared; only the transitive `zod@3.25.76` copy held by `gitlab-ai-provider` remains under an expiring suppression. Six moderate `glob`/`minimatch` findings remain below the critical/high gate and are tracked in `security/deferred-hardening.md`. Normal project configuration is unchanged.

## Upstream 2.2.3–2.2.5 changes to know about

- **OpenTUI 0.8 is required for TUI plugins.** `@opencode/plugin` now needs `@opentui/core` and `@opentui/solid` 0.8.0 or later. ScrollBox `wrapper`, `viewport`, `content`, and scrollbar facades, plus the `clock` and `onAnimationTick` `RenderContext` methods, are the breaking changes; plugins built only for OpenTUI 0.7 need an update.
- **Claude Agent provider.** Install Claude Code, run `claude auth login`, then select **Claude Agent** in `/connect` to use that login and its models.
- **Managed policy split.** `integration.use` now covers integration accounts only; `mcp.use`, `skill.use`, and `plugin.use` control MCP servers, skills, and plugins. Rules with the old `mcp:`, `skill:`, and `plugin:` resource prefixes are converted automatically.
- **Worktree and shell shortcuts.** `Ctrl+Alt+O` and `Ctrl+Alt+B` choose a worktree and its base branch; `Ctrl+Shift+X` toggles shell mode in the composer.
- **Percentage compaction buffer.** `"compaction": { "buffer": "20%" }` keeps a share of each model's context window free; token counts still work.
- **Persistent desktop terminals and interactive artifacts.** Desktop terminals survive server restarts with scrollback; `"experimental": { "artifacts": true }` enables agent-published HTML/static artifacts.
- **Core fixes.** MCP stdio messages over 10 MiB no longer disconnect, compaction caps prompts at the model context window, LiteLLM context errors trigger compaction, and reasoning stays reasoning when switching models or resuming.
- **TUI fixes.** Lazy stored-image references, PHP highlighting without `<?php`, `#` preservation in file-search paths, and cursor-style persistence across config reloads.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.2.5-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

```sh
cosign verify-blob \
  --bundle SHA256SUMS.cosign.bundle \
  --certificate-identity-regexp '^https://github\.com/murafdev/opencode-termux/\.github/workflows/publish-native-android\.yml@refs/(heads|tags)/.+$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-github-workflow-repository murafdev/opencode-termux \
  SHA256SUMS
```

The signature binds the artifacts to the release workflow and records them in the transparency log. It does not protect against a compromised maintainer account.

## Rollback to the previous builds

The previous OpenCode 2.2.2 release remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.2-bun144.1/install.sh | sh
```

The 2.2.0 release also remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.0-bun144.1/install.sh | sh
```

The 2.1.4 release also remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.4-bun144.2/install.sh | sh
```

Both 2.1.3 releases also remain available. To use the 2.1.3 Bun 1.4.4 build:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3-bun144.1/install.sh | sh
```

To return to the original Bun 1.4.0 build:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

The v2.1.2 release is also retained. Back up OpenCode data before downgrading if you may need to recover an older session database.

## Provenance and testing

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `41193063342` was built at commit `26f920a6e013f44f51e3c19e4b9ff6ab7c341b57`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 198,451,576 bytes with SHA-256 `e2f2a4da522f5f132b5d78eb46df905df6e25e23a14a496e78429e3d1dd07045`.

CI built the artifact and verified its aarch64 PIE ELF metadata with `/system/bin/linker64`, the embedded Bionic OpenTUI 0.8.0 renderer's `libc.so` linkage, the FFI negative-coordinate guard, and the 669-module graph; the push-triggered Linux unit suite passed. Artifact review also confirmed the embedded `libopentui.so` is 4,522,624 bytes with SONAME `libopentui.so`, Bionic-only `NEEDED` entries, 244 exported `ot_*` symbols, and no glibc-only `pthread_tryjoin_np` import. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.2.5`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
