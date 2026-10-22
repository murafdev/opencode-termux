# OpenCode 2.1.2 for Termux

Run OpenCode v2 directly in Termux on Android ARM64, without PRoot or glibc. This release updates the app from 2.0.28 to 2.1.2 while keeping the single `opencode` command.

Install in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.2/install.sh | sh
```

Then run `opencode`. The installer checks both the compressed download and the extracted binary against release checksums before replacing `~/.local/bin/opencode`. It keeps your chats, sign-ins, and configuration. Back up your OpenCode data first if you might need to return to v1, because v2 may migrate the session database.

## What changed

- OpenCode updated to upstream `2.1.2`.
- The bundled OpenTUI renderer is rebuilt from pinned `0.6.6` source with the Android/Bionic hardening patches retargeted to that release.
- Bionic heap pointer tagging is disabled when the renderer library loads. Android 11+ tags 64-bit heap pointers in the top byte, and OpenTUI `0.6.6` rejects such addresses with `Pointer exceeds safe integer range`; allocations made after the renderer loads now reach JavaScript untagged.
- The Termux installer guard for `opencode upgrade` and the native-binary handling in `opencode uninstall` are updated for the 2.1.2 command handlers.

`opencode upgrade` refuses to download an incompatible upstream build; to update this fork build, run the install command above. `opencode uninstall --dry-run` previews removal; `opencode uninstall` removes this binary and the shared cache after confirmation, but retains user data.

## Provenance and testing

The build comes from pinned OpenCode source and Android/Bionic components in [GitHub Actions](https://github.com/murafdev/opencode-termux/actions/workflows/build-native-android.yml). Checksums and build inputs are attached to the release; the [source-build guide](https://github.com/murafdev/opencode-termux/blob/native-android/docs/native-v2-build.md) shows how to reproduce it.

The release is published only from a successful CI candidate whose archive, binary header, Bionic dependencies, renderer guard, and transplant report were verified by the build job. The published binary is from [Actions run 39697595422](https://github.com/murafdev/opencode-termux/actions/runs/39697595422); its SHA-256 is `4bdd3f9b1c19ca53ff3cc7eaec0a77195c613999188671cf8cc5344a34e39248`. The TUI has been confirmed working on-device; wider device testing is welcome.
