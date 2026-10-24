# Native v2 build

Target: OpenCode native Android/aarch64 Bionic, no proot or glibc. The current stable release remains `v2.1.3-bun144.1`; OpenCode `2.1.4` is being prepared as a runtime-test candidate, not yet a user release. Both the Bun 1.4.4 and original Bun 1.4.0 releases remain available for rollback.

Two supported paths:

- CI candidate: `.github/workflows/build-native-android.yml` fetches pinned OpenCode `2.1.4` source, builds its source-mode graph with Bun 1.4.4, cross-compiles OpenTUI `0.6.8` with the NDK sysroot and Zig, and transplants the graph onto the hash-verified Android/Bionic Bun 1.4.4 runtime. The existing Bionic safety guards and release patches were checked against the pinned OpenTUI 0.6.8 source. The transplant fix preserves zero-filled `.bss` when ELF metadata is relocated. Inputs are locked in `tools/supply-chain-lock.json`.
- Release gate: the 2.1.4 build is only a runtime-test candidate. It will not replace the current release until the exact CI artifact passes on-device checks. `.github/workflows/publish-native-android.yml` still targets the existing stable release and must be updated only after candidate approval. CI's Linux runner cannot execute the Android ELF; device results will be recorded separately. The `v2.1.3-bun144.1` release and the original `v2.1.3` Bun 1.4.0 build remain available for rollback.
- On-device (older transplant path): Termux itself is Bionic, so this path needs no NDK. The full guide is in `docs/transplant.md`. Deps: `pkg install python3 nodejs clang make zig` (`zig` only to rebuild OpenTUI; `upx` optional), plus network for `npm pack` and the Android Bun download. The currently documented local target is `2.0.26`:
  ```sh
  make transplant VER=2.0.26
  ```
  Output: `artifacts/transplant/2.0.26/opencode-native-revived`. Then test: `opencode --version`, TUI smoke, auth, prompt, clean exit. The newer `2.1.3` release uses the CI source-build path above; the older on-device command does not reproduce it.
