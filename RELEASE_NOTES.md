# OpenCode 2.4.1 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.4.1` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.4.1` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.9.4 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.4.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.4.1`.

## What changed

- OpenCode updated to `2.4.1` from pinned upstream commit `6f0514052a3c859894ad01bb14cc14dda1e44b96`; this includes the `2.4.0` changes.
- Bionic OpenTUI renderer updated to `0.9.4`, built with Zig `0.17.1`. The Android hardening patches were re-verified against the 0.9.4 source: file-prefix mapping, the self-contained TLSDESC resolver, the Android 11+ heap-pointer-tagging opt-out, the scissor/rect overflow guards, and the Bionic clipboard shim. The Android build skips OpenTUI's static archive because its `bundle-libcxx` step cannot resolve Bionic libc; the renderer ships as `libopentui.so`.
- The Bionic build keeps the empty `limits.h` shim after the NDK sysroot. Zig translate-c appends the host system include paths even for Android, so without the shim the host glibc `limits.h` shadows the NDK sysroot and breaks the renderer build.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 714 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The OSV gate now reports only the existing transitive `zod@3.25.76` suppression and six moderate `glob`/`minimatch` findings below the gate; the temporary picomatch suppression was removed after GHSA-fc5q-39xc-vjpf was withdrawn as not a security issue. Normal project configuration is unchanged.

## Upstream 2.4.0–2.4.1 changes to know about

- **New TUI look.** The new designs are on by default, and the theme named `opencode` is the new theme. Set `opencode-classic` in **Theme** for the previous colors, or `experimental["new-designs"]: false` in the TUI config for the previous designs.
- **TUI plugins need OpenTUI 0.9.4.** `@opencode/plugin` requires `@opentui/core` and `@opentui/solid` 0.9.4 or later. Renderers passed to `registerCodeBlockRenderer` now receive an OpenTUI block (`block.text`) instead of a Markdown token; `codeBlockStyle` and `escaped` are gone. Plugins built only for OpenTUI 0.8 or older need an update.
- **Automations.** Ask the agent to run a prompt, Code Mode script, or fixed shell command once, on an interval, on a cron schedule, or when an MCP server pushes an event. Use `/automation` or the `automation` tools. A shell action asks for approval when created and records each run's exit code and output. Set `"automations": false` to turn them off.
- **Video generation.** When a connected provider has a video model, the agent can create videos with `generate_video`. The job runs in the background, survives a server restart, saves finished videos into the workspace, and wakes the agent with their paths. `experimental_image_generate` was renamed to `generate_image`; old permission rules are mapped, but saved “always allow” approvals ask again once.
- **MCP events and protocol negotiation.** OpenCode follows the MCP Events beta for push delivery, with argument checks, heartbeats, and automatic reconnects. MCP servers without a `protocol` setting try the newest protocol first and fall back to the legacy handshake; set `protocol: "legacy"` for a server that misbehaves.
- **Plugin updates.** Plugins written as `name@latest`, a version range, a Git branch, or a Git `semver:` range are checked on startup and every 24 hours; a newer match is installed and reloaded, and a failed update keeps the previous version. Bare names, exact versions, tags, and commit hashes update only through `opencode plugin update`.
- **GitHub Copilot auth.** Copilot no longer reads `GITHUB_TOKEN`. Use `COPILOT_GITHUB_TOKEN` or sign in with OAuth.
- **Code Mode session paths.** `tools.opencode.session_rename` and `session_move` are now `tools.opencode.session.rename` and `.move`. Direct tool names and permission actions are unchanged.
- **SDK plugin loading.** Plugins load in the background again; the server no longer waits up to 5 seconds and returns 503. Right after startup, model/provider/`generate.*`/`voice.*`/`websearch.query` endpoints may return partial data, so long-lived clients should refresh on the matching `*.updated` event and one-shot scripts should poll.
- **TUI details.** `/login` and `/auth` open the same dialog as `/connect`, which now lists one **OpenCode** entry that includes OpenCode Go models. Pressing `↓` opens the picker on the first tab with something running. Text prompt dialogs end with a **Submit** button. The `opencode` theme's light mode uses lighter grays for the prompt box, selected tabs, and hovered rows.
- **2.4.1 fixes.** Config-only providers such as Ollama now show their models in `/models` without a `/connect` login. A `/btw` answer that finishes behind another side-panel tab shows an unread dot. `experimental.model_speeds` exposes service tiers as remembered speeds. Compaction keeps no more than `keep.tokens` of recent history, and long goal sessions no longer incur an extra cache cost after compaction.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.4.1-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

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

The previous OpenCode 2.3.2 release remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.3.2/install.sh | sh
```

The 2.3.0 release also remains available:

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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `45359112921` was built at commit `e2efc67e7959abd5350d3fb1ce770c60a024ee46`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 216,342,904 bytes with SHA-256 `ab39b9c4131ab5664fe1ef12df19f181d1509d455ab20e19bee4cd5adb725d1c`.

The artifact is an aarch64 PIE ELF with `/system/bin/linker64`. CI verified the embedded Bionic OpenTUI 0.9.4 renderer's `libc.so` linkage, the FFI negative-coordinate guard, and the 714-module graph; the Linux unit suite passed after the security baseline cleanup. Artifact review also confirmed the embedded `libopentui.so` is 4,881,928 bytes with SONAME `libopentui.so`, Bionic-only `NEEDED` entries, 292 exported `ot_*` symbols, and no glibc-only `pthread_tryjoin_np` import. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.4.1`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
