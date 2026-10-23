# OpenCode 2.1.2 for Termux

Run OpenCode v2 directly in Termux on Android ARM64, without PRoot or glibc. This release updates the app from 2.0.28 to 2.1.2 while keeping the single `opencode` command.

Install in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.2/install.sh | sh
```

If `~/.local/bin` is not already on your `PATH`, add it once and reload your shell:

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

For Zsh use `~/.zshrc`; for Fish run `fish_add_path ~/.local/bin`. Then run `opencode --version` (expected: `2.1.2`) and `opencode`.

Installing and running OpenCode needs no Android storage permission; everything stays in Termux's private home. To open projects in shared storage, run `termux-setup-storage` once and approve the Android prompt (on Android 11+ you may also need **All files access** for Termux), then use paths such as `~/storage/shared/Documents/my-project`.

The installer checks both the compressed download and the extracted binary against release checksums before replacing `~/.local/bin/opencode`. It keeps your chats, sign-ins, and configuration. Back up your OpenCode data first if you might need to return to v1, because v2 may migrate the session database.

## What changed

- OpenCode updated to upstream `2.1.2`.
- The bundled OpenTUI renderer is rebuilt from pinned `0.6.6` source with the Android/Bionic hardening patches retargeted to that release.
- Bionic heap pointer tagging is disabled when the renderer library loads. Android 11+ tags 64-bit heap pointers in the top byte, and OpenTUI `0.6.6` rejects such addresses with `Pointer exceeds safe integer range`; allocations made after the renderer loads now reach JavaScript untagged.
- The Termux installer guard for `opencode upgrade` and the native-binary handling in `opencode uninstall` are updated for the 2.1.2 command handlers.
- Google Play Termux compatibility: Play Store Termux runs app-data executables through `/system/bin/linker64` (the Android 10+ W^X workaround), so `process.execPath` is the linker and the TUI could not spawn its own server (`error: expected absolute path: "serve"` or `Standalone server exited before reporting readiness`). The TUI now resolves its real executable from `argv[0]` and launches the server through `/system/bin/sh` so Termux's exec interception still applies. GitHub/F-Droid Termux behavior is unchanged.

`opencode upgrade` refuses to download an incompatible upstream build; to update this fork build, run the install command above. `opencode uninstall --dry-run` previews removal; `opencode uninstall` removes this binary and the shared cache after confirmation, but retains user data.

## Provenance and testing

The build comes from pinned OpenCode source and Android/Bionic components in [GitHub Actions](https://github.com/murafdev/opencode-termux/actions/workflows/build-native-android.yml). Checksums and build inputs are attached to the release; the [source-build guide](https://github.com/murafdev/opencode-termux/blob/native-android/docs/native-v2-build.md) shows how to reproduce it.

The release is published only from a successful CI candidate whose archive, binary header, Bionic dependencies, renderer guard, and transplant report were verified by the build job. This build replaces the earlier v2.1.2 asset, so reinstall to pick up the Google Play Termux startup fix. The published binary is from [Actions run 39909948345](https://github.com/murafdev/opencode-termux/actions/runs/39909948345); its SHA-256 is `9c5945dcd0fa771ae4badfb38c2268151759a09f231e31f0c990af82a780e69e`. The TUI has been confirmed working on-device; wider device testing is welcome.
