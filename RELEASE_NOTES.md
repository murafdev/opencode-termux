# OpenCode 2.3.2 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.3.2` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.3.2` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.8.4 renderer while preserving the `opencode` command. Starting with this release, the tag is the plain upstream version; the Bun/OpenTUI details stay in the build metadata and asset name.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.3.2/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.3.2`.

## What changed

- OpenCode updated to `2.3.2` from pinned upstream commit `c0ad18b402eb2827fc1ee71c171b1177b3fc02d1`; this includes the `2.3.1` changes. The pinned Bun source toolchain remains `1.4.4`.
- Bionic OpenTUI renderer remains `0.8.4` and is built with Zig `0.17.0`. The Android hardening patches were re-verified against the 0.8.4 source: file-prefix mapping, the self-contained TLSDESC resolver, the Android 11+ heap-pointer-tagging opt-out, the scissor/rect overflow guards, and the Bionic clipboard shim. 0.8.4 keeps the i64 viewport clamp and the `drawTextFitted` text path, and adds `ot_scene_reaches_hooks`.
- The Bionic build keeps the empty `limits.h` shim after the NDK sysroot. Zig 0.17 translate-c appends the host system include paths even for Android, so without the shim the host glibc `limits.h` shadows the NDK sysroot and breaks the renderer build.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 701 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The 2.3.2 lockfile adds two HIGH `picomatch` ReDoS advisories (GHSA-fc5q-39xc-vjpf) for which no fixed release exists yet; both are suppressed with a reachability justification and expire `2027-01-31`. The existing transitive `zod@3.25.76` suppression and the six moderate `glob`/`minimatch` findings below the gate remain tracked in `security/deferred-hardening.md`. Normal project configuration is unchanged.

## Upstream 2.3.1–2.3.2 changes to know about

- **Timed-out shell commands keep running.** A shell command still running when its timeout expires now moves to the background instead of being killed, so long builds and test runs can finish and report back. The `shell_timeout_background` flag is gone, and a foreground `timeout: 0` now means the default 120 seconds.
- **Compaction without the wait.** Background compaction is on by default, so the summary is written in the background and the next prompt does not pause for it. Set `compaction.background: false` to turn it off; a background summary that is never used still costs tokens. `experimental.background_compaction` is removed.
- **GPT 6.2 with ChatGPT sign-in.** GPT 6.2 Sol and GPT 6.2 Astra, plus their fast variants, appear in the model picker when you sign in with ChatGPT. `2.3.2` fixes GPT-6.2 prompt caching so the system prompt is sent as a leading developer message and cached from the second step on.
- **CLAUDE.md fallback restored.** OpenCode again reads `CLAUDE.md` in directories that have no `AGENTS.md`, and falls back to `~/.claude/CLAUDE.md` when the global `AGENTS.md` is missing. Set `OPENCODE_DISABLE_CLAUDE_CODE` or `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` to skip it.
- **Shell and read reliability.** Finished shell commands no longer leave zombie processes under `opencode-pty`. Small text files now apply the default line and byte limits, `limit: 0` is rejected, paged reads that select a blank line return it, and emoji/multi-byte characters are no longer split in shell output, grep previews, generated titles, read lines, or shell tails.
- **Code Mode and tools.** Code Mode gets structured `read` results, Node `Buffer`, the `search("issues")` shorthand, and 500-character tool summaries. A missing tool now returns a rejected promise, plugin tool renames apply inside Code Mode, and a program that only logs no longer prints a stray `null`.
- **Providers and plugins.** ChatGPT/OpenAI subscription logins keep their sharing-limit and context caps across token refresh failures; Claude Agent models keep their context window when Claude Code renames a model; switching models mid-session no longer sends the wrong reasoning field. Plugin replacement recovers when cleanup of an earlier plugin fails.
- **TUI fixes.** Permission prompts from subagents appear while viewing the subagent's session and in front of an open composer. Closing a session another TUI shares moves to the neighbouring tab. The export dialog can save to the system temp directory. Shell output no longer has broken characters at the edges. Time to first token was removed from the message footer.
- **Experimental automations.** Experimental schedules are now automations behind the `automations` flag: a time, interval, cron, or pushed MCP event can send a prompt or run a Code Mode program. Use `/automation` or the `automation_*` tools. The old `schedules` flag still works; plain prompt schedules carry over.
- **2.3.2 webfetch fix.** `webfetch` structured output no longer repeats the `url` and `format` it was called with.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.3.2-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

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

The previous OpenCode 2.3.0 release remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.3.0-bun144.1/install.sh | sh
```

The 2.2.7 release also remains available:

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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `44289708544` was built at commit `64d5d0757f5b8fec7dc6ee6c5fdbffe6dfaae0c4`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 202,842,488 bytes with SHA-256 `e1956c93b827cffe5cccbc19787b7e51a3228c8d70052932d43a970f323455e9`.

The artifact is an aarch64 PIE ELF with `/system/bin/linker64`. CI verified the embedded Bionic OpenTUI 0.8.4 renderer's `libc.so` linkage, the FFI negative-coordinate guard, and the 701-module graph; the Linux unit suite passed after the security baseline update. Artifact review also confirmed the embedded `libopentui.so` is 4,620,328 bytes with SONAME `libopentui.so`, Bionic-only `NEEDED` entries, 270 exported `ot_*` symbols, and no glibc-only `pthread_tryjoin_np` import. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.3.2`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
