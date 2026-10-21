# OpenCode 2.1.2 for Termux

Run OpenCode v2 directly in Termux on Android ARM64, without PRoot or glibc. This release updates the app from 2.0.28 to 2.1.2 while keeping the single `opencode` command.

Install in Termux:

```sh
curl -fsSL https://github.com/Spectra010s/opencode-termux/raw/v2.1.2/install.sh | sh
```

Then run `opencode`. The installer checks both the compressed download and executable against release checksums before replacing `~/.local/bin/opencode`. It keeps your chats, sign-ins, and configuration. Back up your OpenCode data first if you might need to return to v1, because v2 may migrate the session database.

## What changed

- OpenCode updated to upstream `2.1.2`.
- The bundled OpenTUI renderer is rebuilt from pinned `0.6.6` source with the Android/Bionic hardening patches retargeted to that release.
- The Termux installer guard for `opencode upgrade` and the native-binary handling in `opencode uninstall` are updated for the 2.1.2 command handlers.

`opencode upgrade` points to this verified installer rather than downloading an incompatible upstream build. `opencode uninstall --dry-run` previews removal; `opencode uninstall` removes this binary and the shared cache after confirmation, but retains user data.

## Provenance and testing

The build comes from pinned OpenCode source and Android/Bionic components in [GitHub Actions](https://github.com/Spectra010s/opencode-termux/actions/workflows/build-native-android.yml). Checksums and build inputs are attached to the release; the [source-build guide](https://github.com/Spectra010s/opencode-termux/blob/native-android/docs/native-v2-build.md) shows how to reproduce it.

The release is published only from a successful CI candidate whose archive, binary header, Bionic dependencies, renderer guard, and transplant report were verified by the build job. It has not yet had a wide device test; please report any device-specific TUI or clipboard issues. Wider device testing is welcome.
