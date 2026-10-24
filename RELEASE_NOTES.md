# OpenCode 2.1.4 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.1.4` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.1.4-bun144.2` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.6.8 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.4-bun144.2/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.1.4`.

## What changed

- OpenCode updated to `2.1.4` from pinned upstream commit `68bc26b7da1990ce10ffecfbc1e09eb13aa5d824`; its pinned Bun source toolchain is `1.4.4`.
- Bionic OpenTUI renderer updated to `0.6.8` with Android hardening patches validated against the pinned upstream source.
- Android/Bionic Bun runtime is `1.4.4`.
- Fixed the transplant layout so ELF metadata appended to a `PT_LOAD` segment does not overwrite the runtime's zero-filled `.bss`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- OpenTUI Android hardening includes heap-pointer-tagging handling and the Google Play Termux self-spawn fix.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.
- Security hardening: project-controlled markdown frontmatter and `instructions` globs now have bounded parsing work. A crafted checkout can no longer stall startup through js-yaml merge-key amplification (CVE-2026-84375) or brace-expansion recursion (CVE-2026-102276 / 102277 / 102278). Normal project configuration is unchanged.

## Release signatures

The publish workflow signs both `SHA256SUMS` and the archive with cosign keyless signing and attaches `SHA256SUMS.cosign.bundle` and `opencode-2.1.4-android-aarch64-source-bun144-sourcegraph.tar.gz.cosign.bundle`. `install.sh` verifies them when `cosign` is installed; `OPENCODE_REQUIRE_SIGNATURE=1` makes an absent or invalid signature fatal. To verify manually:

```sh
cosign verify-blob \
  --bundle SHA256SUMS.cosign.bundle \
  --certificate-identity-regexp '^https://github\.com/murafdev/opencode-termux/\.github/workflows/publish-native-android\.yml@refs/(heads|tags)/.+$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-github-workflow-repository murafdev/opencode-termux \
  SHA256SUMS
```

The signature binds the artifacts to the release workflow and records them in the transparency log. It does not protect against a compromised maintainer account.

## Rollback to the previous OpenCode 2.1.3 builds

Both prior 2.1.3 releases remain available. To use the Bun 1.4.4 build:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3-bun144.1/install.sh | sh
```

To return to the original Bun 1.4.0 build:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

The v2.1.2 release is also retained. Back up OpenCode data before downgrading if you may need to recover an older session database.

## Provenance and testing

This release is published from a successful GitHub Actions artifact, not from a phone-side build. The candidate run ID, OpenCode commit, and pinned runtime inputs are recorded in the attached `build-variant.json`, `supply-chain-lock.json`, and `transplant-report.json`; `SHA256SUMS` carries the binary digest.

On one Android/Termux device, this exact candidate passed checksum and `--version` verification, interactive TUI startup, and a real provider prompt using `flint-40b-free`. The Linux CI runner could verify the build and transplant but skipped its runtime TUI probe because it was not AArch64. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
