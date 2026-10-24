# Native v2 build

Target: OpenCode `2.1.3` native Android/aarch64 Bionic, no proot or glibc. The latest release is `v2.1.3-bun144.1`; the original `v2.1.3` Bun 1.4.0 release remains available as rollback.

Two supported paths:

- CI (current release path): `.github/workflows/build-native-android.yml` fetches pinned OpenCode `2.1.3` source, builds the source-mode graph with Bun 1.4.4, cross-compiles OpenTUI `0.6.6` with the NDK sysroot and Zig, and transplants the graph onto the hash-verified Android/Bionic Bun 1.4.4 runtime. The transplant fix preserves zero-filled `.bss` when ELF metadata is relocated. Inputs are locked in `tools/supply-chain-lock.json`.
- Release gate: the Bun 1.4.4 strategy is initially a diagnostic candidate, not a release artifact. It is promoted only after on-device checks. `.github/workflows/publish-native-android.yml` downloads the successful CI run, verifies its checksums, Bun/build metadata, and transplant report, then publishes the release archive. CI's Linux runner cannot execute the Android ELF; device results are recorded separately in `RELEASE_NOTES.md`. The original `v2.1.3` Bun 1.4.0 release remains a rollback path. `install.sh` is pinned to the latest release tag in the source tree.
- On-device (older transplant path): Termux itself is Bionic, so this path needs no NDK. The full guide is in `docs/transplant.md`. Deps: `pkg install python3 nodejs clang make zig` (`zig` only to rebuild OpenTUI; `upx` optional), plus network for `npm pack` and the Android Bun download. The currently documented local target is `2.0.26`:
  ```sh
  make transplant VER=2.0.26
  ```
  Output: `artifacts/transplant/2.0.26/opencode-native-revived`. Then test: `opencode --version`, TUI smoke, auth, prompt, clean exit. The newer `2.1.3` release uses the CI source-build path above; the older on-device command does not reproduce it.
