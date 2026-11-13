# OpenCode 2.3.0 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.3.0` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.3.0-bun144.1` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.8.4 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.3.0-bun144.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.3.0`.

## What changed

- OpenCode updated to `2.3.0` from pinned upstream commit `a6b15d33daf6ab7d35569f6d711fdb630b9f04e7`; this includes the earlier `2.2.6` and `2.2.7` changes. The pinned Bun source toolchain remains `1.4.4`.
- Bionic OpenTUI renderer updated to `0.8.4` and built with Zig `0.17.0`. The Android hardening patches were re-verified against the 0.8.4 source: file-prefix mapping, the self-contained TLSDESC resolver, the Android 11+ heap-pointer-tagging opt-out, the scissor/rect overflow guards, and the Bionic clipboard shim. 0.8.4 keeps the i64 viewport clamp and the `drawTextFitted` text path; it adds `ot_scene_reaches_hooks` for culled streaming text.
- The Bionic build keeps the empty `limits.h` shim after the NDK sysroot. Zig 0.17 translate-c appends the host system include paths even for Android, so without the shim the host glibc `limits.h` shadows the NDK sysroot and breaks the renderer build.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 698 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The 2.3.0 dependency refresh keeps the same cleared critical/high suppressions as 2.2.7; only the transitive `zod@3.25.76` copy held by `gitlab-ai-provider` remains under an expiring suppression. Six moderate `glob`/`minimatch` findings remain below the critical/high gate and are tracked in `security/deferred-hardening.md`. Normal project configuration is unchanged.

## Upstream 2.3.0 changes to know about

- **Background subagents by default.** Subagents now return their session ID immediately, continue in the background, and report back whenever they become idle. Multiple subagents can run concurrently while you keep working in the parent session. If a subagent goes idle while its own background work is still running, its report says it is still running so the parent waits for the final result.
- **Quieter transcripts by default.** The TUI defaults to `session.verbosity: "low"`, which summarizes each run of tool calls and thoughts into one collapsible activity row. Set **Verbosity** to `medium` or `high`, or set `session.verbosity` in the TUI config, to see every step. An existing setting is kept.
- **Shell and process handling.** Shell commands now survive server handoffs and keep their output when interrupted. The experimental `shell_timeout_background` flag moves a command to the background when its timeout expires. Tool-output truncation keeps the beginning of the output and a usable preview when the full output cannot be saved; tail reads no longer load the whole file into memory.
- **MCP and local models.** Added experimental MCP events behind the `mcp_events` flag. Local model discovery (Ollama, LM Studio, vLLM) waits up to 15 seconds per request, LM Studio decision models are supported, and compatible models can use freeform tool input. MCP OAuth refreshes and localhost redirects are fixed when a server rewrites `127.0.0.1`.
- **Provider and plugin reliability.** Providers can present a mutual-TLS client certificate through `settings.tls` with `cert`, `key`, and an optional `passphrase`. Retryable provider streams keep completed work when interrupted, and plugin replacement no longer stops when cleanup of an earlier plugin fails. Case-only file renames work on case-insensitive filesystems.
- **TUI fixes.** Session IDs found in messages open directly; activity tabs are clickable; undo restores pasted text; browsing prompt history restores the live draft; copying a paste from the prompt selection works; the Mini composer keeps its caret when the command palette closes; image bytes are not retained in transcript storage when previews are disabled; plugin themes update live; session lists open at the top; and Mini scrollback shows the subagent card instead of obsolete launch instructions.
- **SDK and extensions.** Event subscriptions can receive experimental MCP events, model capability schemas advertise freeform tool-input formats, session throughput is measured from the first streamed token, and the experimental `session.fork` hook is available. `@opencode/plugin/effect` now exports `Tool` so an `execute.before` hook can reject a call with `Tool.Error`.
- **OpenTUI 0.8.4.** A culled streaming `CodeRenderable` with `drawUnstyledText: false` now measures new content immediately instead of showing stale text and a stale scroll height. The new `ot_scene_reaches_hooks` C API answers whether the next frame's hooks reach a node.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.3.0-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

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

The previous OpenCode 2.2.7 release remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.7-bun144.1/install.sh | sh
```

The 2.2.5 release also remains available:

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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `43417252454` was built at commit `58bc0e6aba871a79a22003a4050b82f8df62d278`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 201,924,984 bytes with SHA-256 `ab8e2b393edb8aba1795a2e6c6f596d28c8bf227462c5481eecb6eb7cb16b5ef`.

The artifact is an aarch64 PIE ELF with `/system/bin/linker64`. CI verified the embedded Bionic OpenTUI 0.8.4 renderer's `libc.so` linkage, the FFI negative-coordinate guard, and the 698-module graph; the Linux unit suite passed on the same commit. Artifact review also confirmed the embedded `libopentui.so` is 4,620,328 bytes with SONAME `libopentui.so`, Bionic-only `NEEDED` entries, 270 exported `ot_*` symbols, and no glibc-only `pthread_tryjoin_np` import. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.3.0`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
