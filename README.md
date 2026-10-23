# OpenCode 2 native for Termux

[OpenCode](https://opencode.ai) is an AI-powered terminal coding assistant. This project ships it as a native Android/aarch64 Bionic binary for [Termux](https://termux.dev): no PRoot, no glibc.

This is the `murafdev` fork of [Spectra010s/opencode-termux](https://github.com/Spectra010s/opencode-termux). It publishes the OpenCode **2.1.3** build on the verified Android/Bionic Bun **1.4.0** runtime with OpenTUI 0.6.6, including the Android 11+ heap-pointer-tagging fix and Google Play Termux startup support. Both v2.1.3 and v2.1.2 have been confirmed working on-device.

## Requirements

- Termux on an Android/aarch64 device running Android 9 (API 28) or newer.
- About 415 MiB free during installation (about 110 MiB archive plus the 305 MiB binary); about 305 MiB after installation.
- `curl` and `sha256sum` in Termux. No Node.js, npm, root, or PRoot is needed to run it.

## Install

In Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

The installer downloads the [GitHub release](https://github.com/murafdev/opencode-termux/releases) archive, checks both the archive and the extracted binary against the release checksum file, and installs the binary as `~/.local/bin/opencode`. It does not silently edit your shell startup files.

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

Expected version: `2.1.3`.

### Rollback to 2.1.2

The `v2.1.2` tag and release assets are kept unchanged. If v2.1.3 causes any problem, reinstall the previous build with:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.2/install.sh | sh
```

The v2.1.2 installer is pinned to the v2.1.2 asset and checksum, so rollback does not depend on the v2.1.3 release. Back up your OpenCode data first if you might need the older session database.

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

Android 11 and newer tag 64-bit heap pointers in the top byte. OpenTUI `0.6.6` converts native pointers to JavaScript numbers and rejects addresses above `Number.MAX_SAFE_INTEGER`, which aborted TUI startup with `Pointer exceeds safe integer range`. This build's renderer library disables heap tagging as soon as it loads, so the context handle and later allocations reach JavaScript untagged. No wrapper script or extra library is installed.

### Google Play Termux

The Google Play build of Termux executes app-data binaries through `/system/bin/linker64` (the Android 10+ W^X workaround). This build detects that mode, resolves the real `opencode` path from `argv[0]`, and re-execs its server through `/system/bin/sh`, so the TUI and standalone mode start normally.

If you installed an earlier v2.1.2 build (before the Play Store fix) and see `error: expected absolute path: "serve"` or `Standalone server exited before reporting readiness`, reinstall with the command above. GitHub/F-Droid Termux is unaffected.

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

The 2.1.3 release is built from pinned source in GitHub Actions, not uploaded from a maintainer's phone. Follow the [native build guide](docs/native-v2-build.md) to reproduce that build or to use the separate on-device build path for supported versions; the [transplant guide](docs/transplant.md) explains the Bionic runtime and native renderer.

## Releases and provenance

The current stable release is [v2.1.3](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.3): OpenCode 2.1.3 on the verified Android Bun 1.4.0 base with the Bionic OpenTUI 0.6.6 renderer. The verified [v2.1.2](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.2) release remains available for rollback.

The [build workflow](.github/workflows/build-native-android.yml) produces a candidate. After testing, the [release workflow](.github/workflows/publish-native-android.yml) downloads that CI artifact, verifies its hash, and publishes it. [Build inputs](tools/supply-chain-lock.json) are pinned to specific versions, hashes, or commits. Releases are currently manual, not weekly automatic updates.

This project is derived from [Hope2333/opencode-termux](https://github.com/Hope2333/opencode-termux) via [Spectra010s/opencode-termux](https://github.com/Spectra010s/opencode-termux); OpenCode itself is [upstream](https://github.com/anomalyco/opencode). Older docs in this repository describe upstream package lines and may not apply to this release. See [LICENSE](LICENSE) for this repository; dependencies retain their own licenses.

## Maintainer

Upstream project: Adeloye Adetayo ([Spectra010s](https://spectra010s.com/?utm_source=github)).

Fork builds and releases: [@murafdev](https://github.com/murafdev).
