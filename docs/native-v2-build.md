# Native v2 build

Target: OpenCode native Android/aarch64 Bionic, no proot or glibc. The current stable release is `v2.1.4-bun144.2`. Both OpenCode 2.1.3 builds—the Bun 1.4.4 release and the original Bun 1.4.0 release—remain available for rollback.

Two supported paths:

- CI release path: `.github/workflows/build-native-android.yml` fetches pinned OpenCode `2.1.4` source, builds its source-mode graph with Bun 1.4.4, cross-compiles OpenTUI `0.6.8` with the NDK sysroot and Zig, and transplants the graph onto the hash-verified Android/Bionic Bun 1.4.4 runtime. The existing Bionic safety guards and release patches were checked against the pinned OpenTUI 0.6.8 source. The transplant fix preserves zero-filled `.bss` when ELF metadata is relocated. Inputs are locked in `tools/supply-chain-lock.json`.
- Release gate: candidate run [40069487737](https://github.com/murafdev/opencode-termux/actions/runs/40069487737) passed the build and artifact checks for `v2.1.4-bun144.1`. The `v2.1.4-bun144.2` security rebuild must pass the same gate before publishing. The exact CI binary passed checksum/version verification, interactive TUI startup, and a real provider prompt on one Android device. `.github/workflows/publish-native-android.yml` publishes only that CI artifact after rechecking its hashes, metadata, and transplant report; a phone-built binary is never uploaded. The publish job installs a hash-pinned cosign binary from `tools/supply-chain-lock.json` and signs `SHA256SUMS` plus the archive with keyless Sigstore signing; `install.sh` verifies both bundles when cosign is available and fails closed with `OPENCODE_REQUIRE_SIGNATURE=1`. CI's Linux runner cannot execute the Android ELF, so its runtime TUI probe is skipped. The `v2.1.3-bun144.1` release and original `v2.1.3` Bun 1.4.0 release remain available for rollback.
- On-device (older transplant path): Termux itself is Bionic, so this path needs no NDK. The full guide is in `docs/transplant.md`. Deps: `pkg install python3 nodejs clang make zig` (`zig` only to rebuild OpenTUI; `upx` optional), plus network for `npm pack` and the Android Bun download. The currently documented local target is `2.0.26`:
  ```sh
  make transplant VER=2.0.26
  ```
   Output: `artifacts/transplant/2.0.26/opencode-native-revived`. Then test: `opencode --version`, TUI smoke, auth, prompt, clean exit. The `2.1.4` release uses the CI source-build path above; the older on-device command does not reproduce it.
