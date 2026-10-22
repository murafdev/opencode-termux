# OpenCode 2 native for Termux

[OpenCode](https://opencode.ai) is an AI-powered terminal coding assistant. This project ships it as a native Android/aarch64 Bionic binary for [Termux](https://termux.dev): no PRoot, no glibc.

This is the `murafdev` fork of [Spectra010s/opencode-termux](https://github.com/Spectra010s/opencode-termux). It publishes the OpenCode **2.1.2** build with OpenTUI 0.6.6, including the Android 11+ heap-pointer-tagging fix. The TUI has been confirmed working on-device; wider device testing is welcome.

## Requirements

- Termux on an Android/aarch64 device running Android 9 (API 28) or newer.
- About 410 MiB free during installation (about 105 MiB archive plus the 305 MiB binary); about 305 MiB after installation.
- `curl` and `sha256sum` in Termux. No Node.js, npm, root, or PRoot is needed to run it.

## Install

In Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.2/install.sh | sh
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

Expected version: `2.1.2`.

No apt/pacman package for this build has been published by this project.

### Android 11+ pointer tagging

Android 11 and newer tag 64-bit heap pointers in the top byte. OpenTUI `0.6.6` converts native pointers to JavaScript numbers and rejects addresses above `Number.MAX_SAFE_INTEGER`, which aborted TUI startup with `Pointer exceeds safe integer range`. This build's renderer library disables heap tagging as soon as it loads, so the context handle and later allocations reach JavaScript untagged. No wrapper script or extra library is installed.

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

The 2.1.2 release is built from pinned source in GitHub Actions, not uploaded from a maintainer's phone. Follow the [native build guide](docs/native-v2-build.md) to reproduce that build or to use the separate on-device build path for supported versions; the [transplant guide](docs/transplant.md) explains the Bionic runtime and native renderer.

## Releases and provenance

The current release is [v2.1.2](https://github.com/murafdev/opencode-termux/releases/tag/v2.1.2): OpenCode 2.1.2 on the Android Bun 1.4.0 base with the Bionic OpenTUI 0.6.6 renderer.

The [build workflow](.github/workflows/build-native-android.yml) produces a candidate. After testing, the [release workflow](.github/workflows/publish-native-android.yml) downloads that CI artifact, verifies its hash, and publishes it. [Build inputs](tools/supply-chain-lock.json) are pinned to specific versions, hashes, or commits. Releases are currently manual, not weekly automatic updates.

This project is derived from [Hope2333/opencode-termux](https://github.com/Hope2333/opencode-termux) via [Spectra010s/opencode-termux](https://github.com/Spectra010s/opencode-termux); OpenCode itself is [upstream](https://github.com/anomalyco/opencode). Older docs in this repository describe upstream package lines and may not apply to this release. See [LICENSE](LICENSE) for this repository; dependencies retain their own licenses.

## Maintainer

Upstream project: Adeloye Adetayo ([Spectra010s](https://spectra010s.com/?utm_source=github)).

Fork builds and releases: [@murafdev](https://github.com/murafdev).
