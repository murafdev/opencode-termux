# Native v2 build

Target: OpenCode `2.1.3` native Android/aarch64 Bionic, no proot or glibc.

Two supported paths:

- CI (current release path): `.github/workflows/build-native-android.yml` fetches pinned OpenCode `2.1.3` source, builds its CLI with Bun 1.4.0, cross-compiles OpenTUI `0.6.6` with the NDK sysroot and Zig, and transplants the compiled graph onto the verified Android Bun 1.4.0 base. The upstream `2.1.3` source pins `bun@1.4.4`, so the source patch rewrites `packageManager` to `bun@1.4.0` before installing. Inputs are locked in `tools/supply-chain-lock.json`. `.github/workflows/publish-native-android.yml` verifies the successful CI artifact and publishes the binary archive. `install.sh` stays in the tagged repository.
- On-device (older transplant path): Termux itself is Bionic, so this path needs no NDK. The full guide is in `docs/transplant.md`. Deps: `pkg install python3 nodejs clang make zig` (`zig` only to rebuild OpenTUI; `upx` optional), plus network for `npm pack` and the Android Bun download. The currently documented local target is `2.0.26`:
  ```sh
  make transplant VER=2.0.26
  ```
  Output: `artifacts/transplant/2.0.26/opencode-native-revived`. Then test: `opencode --version`, TUI smoke, auth, prompt, clean exit. The newer `2.1.3` release uses the CI source-build path above; the older on-device command does not reproduce it.
