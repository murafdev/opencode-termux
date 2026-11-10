# OpenCode 2.2.7 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.2.7` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.2.7-bun144.1` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.8.1 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.7-bun144.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.2.7`.

## What changed

- OpenCode updated to `2.2.7` from pinned upstream commit `fedc6f208aa2bd54c1019227214568083f6380ad`; this includes the `2.2.6` changes. The pinned Bun source toolchain remains `1.4.4`.
- Bionic OpenTUI renderer updated to `0.8.1` and built with Zig `0.17.0`. The Android hardening patches were re-verified against the 0.8.1 source: file-prefix mapping, the self-contained TLSDESC resolver, the Android 11+ heap-pointer-tagging opt-out, and the scissor/rect overflow guards. 0.8.1 keeps the i64 viewport clamp and routes text draws through `drawTextFitted`.
- The Bionic build now terminates Bionic's `#include_next <limits.h>` chain with an empty shim. Zig 0.17 translate-c appends the host system include paths even for Android, so without the shim the host glibc `limits.h` shadowed the NDK sysroot and broke the renderer build.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 689 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The 2.2.7 dependency refresh keeps the nine other critical/high suppressions cleared that 2.2.2 resolved; only the transitive `zod@3.25.76` copy held by `gitlab-ai-provider` remains under an expiring suppression. Six moderate `glob`/`minimatch` findings remain below the critical/high gate and are tracked in `security/deferred-hardening.md`. Normal project configuration is unchanged.

## Upstream 2.2.6–2.2.7 changes to know about

- **Shared MCP connections.** Set `pool: true` on an MCP server to share one connection across projects with the same setup, reducing process count and startup time. MCP OAuth refresh failures are also more resilient: a temporary token-endpoint failure no longer marks the server as needing auth, and rotating refresh tokens no longer sign out other clients.
- **Scripted and CI runs.** `opencode run --archived` creates the session already archived so scripted runs stay out of the inbox and session lists. `opencode run -w` / `--worktree=<name>` starts the session in a new git worktree. `opencode run` now waits for background shell commands, subagents, and image jobs before exiting; there is no time limit, so set a timeout on CI jobs that may start a dev server or file watcher.
- **`read` and shell results.** `read` accepts a negative `offset` to read from the end of a file (for example `-50` for the last 50 lines), returns the line count when the offset is past the end, and suggests close filenames on a miss. Shell results now end with `Exit code: N`; signal and timeout failures name the cause.
- **Prompt cache warming.** Warming pings time themselves from the model's `cache.ttl` by default (`interval: "auto"`), or every 4 minutes without a TTL. Cache warming stops after a cache rebuild, during compaction, and after the session is deleted.
- **GitHub Copilot Auto.** When the Copilot account has an Auto pool, **Auto** in the model picker lets Copilot's router choose the model for each session at the Auto discount, with fallback to the account's default chat model.
- **MCP and policy details.** MCP tool calls no longer fail when a server's result does not match the tool's output schema, and MCP prompts stay available when refreshing the prompt list fails. Added the `websearch.use` policy action and `OPENCODE_FLAGS=all` / `experimental.all_flags` switches.
- **Experimental Code Mode VM.** An opt-in bytecode VM for Code Mode is available with `experimental.codemode_vm: true` or `OPENCODE_FLAGS=codemode_vm`.
- **TUI fixes.** Added **Scroll on send** in Settings (`session.submit_scroll: "keep"`), allowed Ctrl+Z to suspend while a dialog is open, fixed session titles containing newlines, reported clipboard read failures on Ctrl+V, followed the terminal's current light/dark mode, and saved session exports in the current working directory.
- **Security fixes.** Server file reads and media are served as sandboxed downloads, cross-site browser navigations and disallowed origins are refused on `/api/*`, and webfetch / Code Mode `fetch` reject URLs containing credentials, ignore the `#fragment` for permission matching, and check every redirect against the webfetch rules.
- **Breaking changes for SDK users.** `@opencode/ai` no longer exposes `ImageResponse.image`; read `response.images[0]` instead. On a Location that is still loading plugins, `agent.list` returns the agents loaded so far, and `integration.list`, `usage.limits`, `vcs.init`, `rpc.call`, and `artifact.*` no longer wait up to 5 seconds. Model/provider, `generate.*`, `voice.*`, and `websearch.query` still wait.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.2.7-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

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

The previous OpenCode 2.2.5 release remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
```

The 2.2.2 release also remains available:

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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `42819305690` was built at commit `f29efb0e612b19dae71a0899150c54411505d02e`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 201,793,912 bytes with SHA-256 `f1921d9a2690fe1078b780789a64e31d4d6aa0d169e28ced06a50e6a578f6ffb`.

The artifact is an aarch64 PIE ELF with `/system/bin/linker64`. CI verified the embedded Bionic OpenTUI 0.8.1 renderer's `libc.so` linkage, the FFI negative-coordinate guard, and the 689-module graph; the push-triggered Linux unit suite passed on the same commit. Artifact review also confirmed the embedded `libopentui.so` is 4,598,032 bytes with SONAME `libopentui.so`, Bionic-only `NEEDED` entries, 259 exported `ot_*` symbols, and no glibc-only `pthread_tryjoin_np` import. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.2.7`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
