# OpenCode 2 native for Termux

[OpenCode](https://opencode.ai) is an AI-powered terminal coding assistant. This project ships it as a native Android/aarch64 Bionic binary for [Termux](https://termux.dev): no PRoot, no glibc.

This is the `murafdev` fork of [Spectra010s/opencode-termux](https://github.com/Spectra010s/opencode-termux). The latest Termux build runs OpenCode **2.2.5** on Android/Bionic Bun **1.4.4** with OpenTUI 0.8.0, including the Android 11+ heap-pointer-tagging fix and Google Play Termux startup support. The previous 2.2.2, 2.2.0, 2.1.4, and both 2.1.3 builds are preserved as rollback options.

## Why this fork

- **Native single binary.** OpenCode 2 on Android/aarch64 Bionic. No PRoot, glibc, Node.js, or npm.
- **Verifiable releases.** Built in GitHub Actions from pinned inputs and checked against a hash-pinned lock file. Checksums and the release archive are signed with keyless Sigstore; install `cosign` and set `OPENCODE_REQUIRE_SIGNATURE=1` to enforce verification.
- **Vulnerability gate.** Dependencies are scanned with OSV in CI.
- **Android 11+ and Google Play Termux fixes** for TUI startup.

## How this was made

Developed with AI coding agents. I read the installer and release workflow, and I test each release on a real device (Xiaomi Poco X6 Pro, Android 16) as part of release validation and record the result in the release notes. Other Android versions are untested by me; the build targets Android 9+. Please report problems with your device model, Android and Termux version.

## Requirements

- Termux on an Android/aarch64 device running Android 9 (API 28) or newer.
- About 500 MiB free during installation for download, extraction, and atomic replacement; the installed Bun 1.4.4 binary is about 190 MiB. The exact archive size and checksums are listed on the release page.
- `curl` and `sha256sum` in Termux. `cosign` is optional and enables Sigstore signature verification. No Node.js, npm, root, or PRoot is needed to run it.

## Install

In Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
```

The installer downloads the [GitHub release](https://github.com/murafdev/opencode-termux/releases) archive, checks both the archive and the extracted binary against the release checksum file, and installs the binary as `~/.local/bin/opencode`. It does not silently edit your shell startup files.

When `cosign` is on `PATH`, the installer also verifies the keyless Sigstore bundles attached to `SHA256SUMS` and the archive. Verification is pinned to the `publish-native-android.yml` workflow certificate identity, the `murafdev/opencode-termux` repository, and GitHub's OIDC issuer, so a signature from another workflow or repository is rejected. Without `cosign` the installer prints a warning and continues; set `OPENCODE_REQUIRE_SIGNATURE=1` to make a missing or invalid signature fatal.

### Add `opencode` to PATH

If `~/.local/bin` is not already on your `PATH`, add it once. Termux uses Bash by default, so append it to `~/.bashrc`:

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

For other shells: use `~/.zshrc` for Zsh, or run `fish_add_path ~/.local/bin` for Fish.

Verify the installation:

```sh
command -v opencode
opencode --version
```

Expected version: `2.2.5`.

### Rollback to the previous OpenCode 2.2.2, 2.2.0, 2.1.4, or 2.1.3 builds

The previous 2.2.2 release remains available:

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

Both 2.1.3 releases also remain available. For the 2.1.3 Bun 1.4.4 build, run:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3-bun144.1/install.sh | sh
```

To return to the original Bun 1.4.0 build instead, run:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

The older v2.1.2 release is also retained. Back up your OpenCode data before downgrading in case a future OpenCode version migrates the session database.

### Shared storage and project files

Installing and running OpenCode needs **no Android storage permission**: the binary, configuration, and sessions live inside Termux's private home directory.

To open projects stored in shared storage (Downloads, Documents, an SD card), grant Termux access once:

```sh
termux-setup-storage
```

Approve the Android prompt. On Android 11 and newer you may also need to allow **All files access** for Termux in Android Settings → Apps → Termux → Permissions. The command creates shortcuts under `~/storage`, for example `~/storage/shared` (`/sdcard`) and `~/storage/downloads`:

```sh
cd ~/storage/shared/Documents/my-project
opencode
```

OpenCode writes its own data under `~/.local/share/opencode` and only touches the project files you open. Keeping projects under the Termux home directory (for example `~/projects`) avoids Android scoped-storage restrictions entirely.

No apt/pacman package for this build has been published by this project.

### Android 11+ pointer tagging

Android 11 and newer tag 64-bit heap pointers in the top byte. OpenTUI converts native pointers to JavaScript numbers and rejects addresses above `Number.MAX_SAFE_INTEGER`, which aborted TUI startup with `Pointer exceeds safe integer range`. This build's renderer library disables heap tagging as soon as it loads, so the context handle and later allocations reach JavaScript untagged. No wrapper script or extra library is installed.

### OpenTUI 0.8 plugin compatibility

OpenCode 2.2.3 and newer require TUI plugins to use `@opentui/core` and `@opentui/solid` 0.8.0 or later. A ScrollBox's `wrapper`, `viewport`, `content`, and scrollbars are facade objects instead of renderables, and a custom `RenderContext` must implement `clock` and `onAnimationTick`. Plugins built only for OpenTUI 0.7 need an update before they work with this release.

### Google Play Termux

The Google Play build of Termux executes app-data binaries through `/system/bin/linker64` (the Android 10+ W^X workaround). This build detects that mode, resolves the real `opencode` path from `argv[0]`, and re-execs its server through `/system/bin/sh`, so the TUI and standalone mode start normally.

If you installed an earlier v2.1.2 build (before the Play Store fix) and see `error: expected absolute path: "serve"` or `Standalone server exited before reporting readiness`, install the current build with the command above. GitHub/F-Droid Termux is unaffected.

## Migrating from v1

The installer replaces only `~/.local/bin/opencode`; it does not delete your chats, sign-ins, or configuration. OpenCode v2 can migrate the existing SQLite database at `~/.local/share/opencode/opencode.db` in place. Back up your OpenCode data before switching if you might need to return to v1. The command remains `opencode`, not `opencode2`.

## Uninstall

`opencode uninstall` stops its background services, removes its cache and this project's installed binary, but keeps chats, sign-ins, and configuration. Preview it first:

```sh
opencode uninstall --dry-run
opencode uninstall
```

If the command cannot start, remove only the installed binary manually:

```sh
rm -f ~/.local/bin/opencode
```

## Build from source

The current build is produced from pinned source in GitHub Actions, not uploaded from a maintainer's phone. Follow the [native build guide](docs/native-v2-build.md) to reproduce it or use the separate on-device build path for supported versions; the [transplant guide](docs/transplant.md) explains the Bionic runtime and native renderer.

## Releases and provenance

The latest release is [v2.2.5-bun144.1](https://github.com/murafdev/opencode-termux/releases/tag/v2.2.5-bun144.1): OpenCode 2.2.5 on Android/Bionic Bun 1.4.4 with the Bionic OpenTUI 0.8.0 renderer. The exact CI artifact passed checksum and `--version` verification, interactive TUI startup, and a clean exit on one Android device; broader device coverage is still welcome. The previous [v2.2.2](https://github.com/murafdev/opencode-termux/releases/tag/v2.2.2-bun144.1), [v2.2.0](https://github.com/murafdev/opencode-termux/releases/tag/v2.2.0-bun144.1), [v2.1.4](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.4-bun144.2), [v2.1.3 Bun 1.4.4](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.3-bun144.1), and original [v2.1.3 Bun 1.4.0](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.3) remain available for rollback, as does [v2.1.2](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.2).

The [build workflow](.github/workflows/build-native-android.yml) builds the Bun 1.4.4 source graph. The [release workflow](.github/workflows/publish-native-android.yml) downloads the tested CI artifact, verifies its hashes and transplant report, then publishes it; the phone's local copy is never uploaded. The CI runner skipped its Android runtime probe because it is not AArch64, so the on-device checks are reported separately. [Build inputs](tools/supply-chain-lock.json) are pinned to specific versions, hashes, or commits. Releases are manual, not weekly automatic updates.

This project is derived from [Hope2333/opencode-termux](https://github.com/Hope2333/opencode-termux) via [Spectra010s/opencode-termux](https://github.com/Spectra010s/opencode-termux); OpenCode itself is [upstream](https://github.com/anomalyco/opencode). Older docs in this repository describe upstream package lines and may not apply to this release. See [LICENSE](LICENSE) for this repository; dependencies retain their own licenses.

## Maintainer

Upstream project: Adeloye Adetayo ([Spectra010s](https://spectra010s.com/?utm_source=github)).

Fork builds and releases: [@murafdev](https://github.com/murafdev).
