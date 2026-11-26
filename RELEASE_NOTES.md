# OpenCode 2.4.2 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.4.2` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.4.2` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.9.9 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.4.2/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.4.2`.

## What changed

- OpenCode updated to `2.4.2` from pinned upstream commit `fc31a485317970bcf6be7b431a9830aaef875731`; this includes the `2.4.0` and `2.4.1` changes.
- Bionic OpenTUI renderer updated to `0.9.9`, built with Zig `0.17.1`. The Android hardening patches were re-verified against the 0.9.9 source: file-prefix mapping, the self-contained TLSDESC resolver, the Android 11+ heap-pointer-tagging opt-out, the scissor/rect overflow guards, and the Bionic clipboard shim. The Android build skips OpenTUI's static archive because its `bundle-libcxx` step cannot resolve Bionic libc; the renderer ships as `libopentui.so`.
- The Bionic build keeps the empty `limits.h` shim after the NDK sysroot. Zig translate-c appends the host system include paths even for Android, so without the shim the host glibc `limits.h` shadows the NDK sysroot and breaks the renderer build.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 732 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The 2.4.2 closure has 489 packages, one gated suppression (transitive `zod@3.25.76`) and four moderate `glob`/`minimatch` findings below the gate. The earlier picomatch suppression was removed after GHSA-fc5q-39xc-vjpf was withdrawn as not a security issue. Normal project configuration is unchanged.

## Upstream 2.4.2 changes to know about

- **GPT-6.2 system prompt.** GPT-6.2 Sol and Astra, and the `gpt-latest` aliases, use a system prompt written for GPT-6.2.
- **Esc takes back your last message.** If the composer is empty and the model has not written anything or called a tool, pressing Esc to stop the response removes your message and puts it back in the composer, images included, so you can edit and resend.
- **Webfetch “Always allow” is per-site.** Approving a web fetch now allows that site only instead of every URL. Approvals saved by earlier versions stay as they were.
- **Automations keep running after a failed run.** The failure is recorded and the next run happens on schedule. A shell command inside an automation's Code Mode action that exceeds its timeout is stopped and fails the call instead of moving to the background.
- **Archived sessions unarchive on send.** Sending a message, command, skill, or shell command to an archived session unarchives it, including through the API.
- **Plan mode rules are in the system prompt.** Sessions already in Plan mode get the rules once more after upgrading, and the reminder is no longer re-added after every compaction.
- **Code Mode media tools.** `generate_image` and `generate_video` now run inside Code Mode instead of as top-level tools, so their definitions no longer add about 700 tokens to every request.
- **Session and cost fixes.** Moving a session also moves its subagents. Service-tier cost estimates use the tier's own prices, including long-context rates. Tools no longer stay visible after a blanket deny followed by narrower denies. MCP sign-in works when the configured URL has a query string. PDFs with bytes before `%PDF-` are read as PDFs. Branches ending in `/HEAD` appear in the branch list. Patches keep a trailing blank line. OpenAI custom tool calls that end only with the completed response no longer fail as malformed.
- **TUI fixes.** The model picker stays responsive with large catalogs, the goal dialog scrolls for long goals, `/models` no longer shows only free models when the TUI opened a session in another directory, type-to-filter works in Message Actions, removing `theme` from config returns to the default theme, quick successive settings changes no longer overwrite each other, and the session list keeps its selected row after a deletion.
- **OpenTUI 0.9.9.** Fixes the `MarkdownRenderable` streaming-list crash from 0.9.4–0.9.8, restores 24-bit color and mouse clicks in ConEmu, and lets `App::set_theme` recolor existing selections through `ot_context_set_selection_colors`.
- **SDK and extensions.** `@opencode/sdk/workerd` can forward a Durable Object's `alarm()` to `opencode.alarm()` so idle remote workspaces suspend. Promise plugin API calls honor `signal`, and plugins can give an agent `instructions` that apply while that agent is selected without busting the prompt cache.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.4.2-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

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

The previous OpenCode 2.4.1 release remains available:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.4.1/install.sh | sh
```

The 2.3.2 release also remains available:

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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `45766913004` was built at commit `385720667d4c60abdeea7520e4fe98196661dff1`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 216,408,440 bytes with SHA-256 `beccee7cf4af74074f234f001f36f3f39752aad053571b3ec17958b07c138601`.

The artifact is an aarch64 PIE ELF with `/system/bin/linker64`. CI verified the embedded Bionic OpenTUI 0.9.9 renderer's `libc.so` linkage, the FFI negative-coordinate guard, and the 732-module graph; the Linux unit suite passed on the candidate commit. Artifact review also confirmed the embedded `libopentui.so` is 4,884,480 bytes with SONAME `libopentui.so`, Bionic-only `NEEDED` entries, 293 exported `ot_*` symbols, and no glibc-only `pthread_tryjoin_np` import. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.4.2`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
