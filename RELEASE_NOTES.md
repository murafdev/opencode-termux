# OpenCode 2.1.4 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.1.4` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.1.4-bun144.1` uses the verified Android/Bionic Bun 1.4.4 runtime and Bionic OpenTUI 0.6.8 renderer while preserving the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.4-bun144.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version is `opencode v2.1.4`.

## What changed

- OpenCode updated to `2.1.4` from pinned upstream commit `68bc26b7da1990ce10ffecfbc1e09eb13aa5d824`; its pinned Bun source toolchain is `1.4.4`.
- Bionic OpenTUI renderer updated to `0.6.8` with Android hardening patches validated against the pinned upstream source.
- Android/Bionic Bun runtime is `1.4.4`.
- Fixed the transplant layout so ELF metadata appended to a `PT_LOAD` segment does not overwrite the runtime's zero-filled `.bss`.
- The release binary was built in GitHub Actions as a source-mode module graph (`bytecode: false`) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- OpenTUI Android hardening includes heap-pointer-tagging handling and the Google Play Termux self-spawn fix.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.

## Rollback to the previous OpenCode 2.1.3 builds

Both prior 2.1.3 releases remain available. To use the Bun 1.4.4 build:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3-bun144.1/install.sh | sh
```

To return to the original Bun 1.4.0 build:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

The v2.1.2 release is also retained. Back up OpenCode data before downgrading if you may need to recover an older session database.

## Provenance and testing

This release is published from a successful GitHub Actions artifact, not from a phone-side build. The source candidate is [Actions run 40069487737](https://github.com/murafdev/opencode-termux/actions/runs/40069487737); its binary SHA-256 is `1c2c107ddc27edc627c27c1d099b3c96a238f9efb5734f2275ccc265c03b6986`. The attached `SHA256SUMS`, supply-chain lock, build-variant metadata, and transplant report record the artifact and pinned inputs.

On one Android/Termux device, this exact candidate passed checksum and `--version` verification, interactive TUI startup, and a real provider prompt using `flint-40b-free`. The Linux CI runner could verify the build and transplant but skipped its runtime TUI probe because it was not AArch64. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
