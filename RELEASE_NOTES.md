# OpenCode 2.2.2 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.2.2` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.2.2-bun144.1` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.7.0 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.2-bun144.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.2.2`.

## What changed

- OpenCode updated to `2.2.2` from pinned upstream commit `098aa7fd6e02b03d6fc410f0b052038c7d4c5e81`; its pinned Bun source toolchain is `1.4.4`.
- Bionic OpenTUI renderer remains `0.7.0`, with the Android hardening patches re-verified against the same 0.7.0 source: file-prefix mapping, the self-contained TLSDESC resolver, and the Android 11+ heap-pointer-tagging opt-out.
- Android/Bionic Bun runtime is `1.4.4`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`, 670 modules) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs still have bounded parsing work (CVE-2026-84375, CVE-2026-102276 / 102277 / 102278), and config loading still isolates normalization failures so one malformed `command`, `agent`, `mcp`, or `provider` entry is logged and skipped instead of aborting config load (upstream #59684). The 2.2.2 dependency refresh clears nine of the ten previously suppressed critical/high advisories; only the transitive `zod@3.25.76` copy held by `gitlab-ai-provider` remains under an expiring suppression. Normal project configuration is unchanged.

## Upstream 2.2.1 and 2.2.2 changes to know about

- `/goal <objective>` keeps a session working until a reviewer confirms the objective is met; use `/goal pause`, `/goal resume`, and `/goal clear` to control it.
- Opt-in scheduled prompts are available through `/schedule`, agent tools, and `experimental.schedules`.
- Image generation (`experimental.image_generate`) is enabled by default in 2.2.2 when a connected provider supports image models. Set a preferred model with `experimental.image_generate.model`.
- The `@opencode/ai` package removes the fal, Black Forest Labs, Replicate, and Stability providers and several legacy entry points. This affects code that imports the library directly; it does not change the CLI, TUI, or HTTP API.
- The 2.2.2 release also fixes terminal requests for deleted working directories, media preservation when sessions are forked or imported, attachment handling, and usage-limit messages.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.2.2-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

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

The previous OpenCode 2.2.0 release remains available:

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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. Candidate run `40971490976` was built at commit `10fd5d5ae3711c65740543b49259364bee0ccc32`. The run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest. The artifact is 199,106,936 bytes with SHA-256 `b6f8587a35135b02098bff8be6536acf298305e2d938b86b2c380f57e0103a5d`.

CI verified the artifact checksum, aarch64 PIE ELF metadata with `/system/bin/linker64`, the embedded Bionic `libopentui.so` (SONAME and Bionic-only `NEEDED` entries), the FFI negative-coordinate guard, all 239 callable FFI symbols, the 670-module graph, and the Linux unit suite. The Linux CI runner skipped its runtime TUI probe because it is not AArch64.

On device, the exact artifact passed the SHA-256 check, `--version` reported `opencode v2.2.2`, the interactive TUI started, and `/q` exited cleanly. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
