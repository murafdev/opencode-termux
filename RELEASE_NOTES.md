# OpenCode 2.1.3 for Termux

Run OpenCode v2 directly in Termux on Android ARM64, without PRoot or glibc. This release updates the app from 2.1.2 to 2.1.3 and moves the Android/Bionic runtime to Bun 1.4.4 while keeping the single `opencode` command.

Install in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

If `~/.local/bin` is not already on your `PATH`, add it once and reload your shell:

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

For Zsh use `~/.zshrc`; for Fish run `fish_add_path ~/.local/bin`. Then run `opencode --version` (expected: `2.1.3`) and `opencode`.

Installing and running OpenCode needs no Android storage permission; everything stays in Termux's private home. To open projects in shared storage, run `termux-setup-storage` once and approve the Android prompt (on Android 11+ you may also need **All files access** for Termux), then use paths such as `~/storage/shared/Documents/my-project`.

The installer checks both the compressed download and the extracted binary against release checksums before replacing `~/.local/bin/opencode`. It keeps your chats, sign-ins, and configuration. Back up your OpenCode data first if you might need to return to v2.1.2 or v1, because v2 may migrate the session database.

## What changed

- OpenCode updated to upstream `2.1.3`.
- The Android/Bionic Bun runtime and source-build toolchain are updated from `1.4.0` to `1.4.4`. Bun 1.4.4 includes security fixes for TLS, WebSocket, database clients, and the package manager.
- The bundled OpenTUI renderer remains pinned to `0.6.6` with the Android/Bionic hardening patches.
- The Google Play Termux startup fix is retained: app-data executables are resolved through `argv[0]`, and self-spawned servers are launched through `/system/bin/sh` when the process runs under the bionic linker.
- The Termux installer guard for `opencode upgrade` and the native-binary handling in `opencode uninstall` are updated for the 2.1.3 command handlers.

`opencode upgrade` refuses to download an incompatible upstream build; to update this fork build, run the install command above. `opencode uninstall --dry-run` previews removal; `opencode uninstall` removes this binary and the shared cache after confirmation, but retains user data.

## Rollback to 2.1.2

The `v2.1.2` tag and its release assets are kept unchanged. If this release causes any problem, reinstall the previous build with:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.2/install.sh | sh
```

That installer is pinned to the v2.1.2 asset and checksum, so it does not depend on the v2.1.3 release. Back up your OpenCode data first if you might need the older session database.

## Provenance and testing

This is a **pre-release** until the Android build has been confirmed on-device. The build comes from pinned OpenCode source and Android/Bionic components in [GitHub Actions](https://github.com/murafdev/opencode-termux/actions/workflows/build-native-android.yml). Checksums and build inputs are attached to the release; the [source-build guide](https://github.com/murafdev/opencode-termux/blob/native-android/docs/native-v2-build.md) shows how to reproduce it.

The release is published only from a successful CI candidate whose archive, binary header, Bionic dependencies, renderer guard, and transplant report were verified by the build job. This candidate is from [Actions run 39920238320](https://github.com/murafdev/opencode-termux/actions/runs/39920238320); the binary SHA-256 is `d3e1d4d3d6c59cc137287b851515908edc30ca4c6fb42fd42333b0f588f9fd93`. The build report confirms OpenCode `2.1.3`, the `.bun` section graph, the Bun `1.4.4` Android base in plain-offset mode, and the Play Store self-spawn fix. After on-device confirmation, the release will be marked as the latest stable release. If it fails, users can reinstall v2.1.2 with the rollback command above.
