# OpenCode 2.1.3 for Termux

Run OpenCode v2 directly in Termux on Android ARM64, without PRoot or glibc. This release updates the app from 2.1.2 to 2.1.3 and keeps the verified Android/Bionic Bun 1.4.0 runtime, with the single `opencode` command.

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
- OpenCode 2.1.3 is built with the verified Bun `1.4.0` host, Linux target, and Android/Bionic base. The upstream source pins `bun@1.4.4`, so the build rewrites `packageManager` to `bun@1.4.0` and regenerates the module graph with the matching toolchain. A 1.4.4 Android candidate was evaluated but reverted because it segfaulted during Bun/JSC startup before OpenCode code ran; keeping 1.4.0 preserves the runtime that v2.1.2 already proved on-device.
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

This release has been confirmed on-device and is the current stable release. The build comes from pinned OpenCode source and Android/Bionic components in [GitHub Actions](https://github.com/murafdev/opencode-termux/actions/workflows/build-native-android.yml). Checksums and build inputs are attached to the release; the [source-build guide](https://github.com/murafdev/opencode-termux/blob/v2.1.3/docs/native-v2-build.md) shows how to reproduce it.

The release is published only from a successful CI candidate whose archive, binary header, Bionic dependencies, renderer guard, and transplant report were verified by the build job. This candidate is from [Actions run 39926528221](https://github.com/murafdev/opencode-termux/actions/runs/39926528221); the binary SHA-256 is `3005943f97eca150ed07a565bd541f034505502a9c235d225bf5cd8db47f4887`. The build report confirms OpenCode `2.1.3`, the `.bun` section graph, the Bun `1.4.0` Android base in plain-offset mode, and the Play Store self-spawn fix. The release was confirmed on-device and marked as the latest stable release on 2026-10-23. The Bun 1.4.0 pin is a compatibility exception for this Android/Bionic target; it is not equivalent to upstream Bun 1.4.4, which still fails during Bun/JSC startup here. If this release fails on your device, reinstall v2.1.2 with the rollback command above.
