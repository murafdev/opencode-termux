# OpenCode 2.1.3 for Termux — Bun 1.4.4 build

This Termux build runs OpenCode `2.1.3` directly on Android ARM64/Bionic, without PRoot or glibc. Release tag `v2.1.3-bun144.1` updates the Android runtime from Bun 1.4.0 to the matching Bun 1.4.4 runtime while preserving the OpenTUI 0.6.6 Android renderer and the `opencode` command.

Install or update in Termux:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3-bun144.1/install.sh | sh
```

The installer verifies the downloaded archive and extracted binary before atomically replacing `~/.local/bin/opencode`. It retains chats, sign-ins, and configuration. The reported CLI version remains `opencode v2.1.3`.

## What changed

- Android/Bionic Bun runtime updated to `1.4.4`, matching the pinned OpenCode 2.1.3 source toolchain.
- Fixed the transplant layout so ELF metadata appended to a `PT_LOAD` segment does not overwrite the runtime's zero-filled `.bss`.
- The candidate was built in GitHub Actions as a source-mode module graph (`bytecode: false`) and transplanted onto the hash-verified Android Bun 1.4.4 binary.
- OpenTUI `0.6.6` remains pinned with the Android/Bionic hardening patches, including heap-pointer-tagging handling and the Google Play Termux self-spawn fix.
- The native `opencode upgrade` guard points at this release's installer. `opencode uninstall --dry-run` previews removal; uninstall keeps user data.

## Rollback to the previous Bun 1.4.0 build

The existing `v2.1.3` release remains unchanged and is the rollback target. It contains OpenCode 2.1.3 on the previously verified Android/Bionic Bun 1.4.0 runtime:

```sh
curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.3/install.sh | sh
```

The v2.1.2 release is also retained. Back up OpenCode data before downgrading if you may need to recover an older session database.

## Provenance and testing

This release is published from a successful GitHub Actions artifact, not from a phone-side build. The source candidate is [Actions run 40062665076](https://github.com/murafdev/opencode-termux/actions/runs/40062665076); its binary SHA-256 is `22291b8f0d0951d8c8608de7f2800e51d6bfd715e2f24f6e1a4c264de5fa8594`. The attached `SHA256SUMS`, supply-chain lock, build-variant metadata, and transplant report record the artifact and pinned inputs.

On one Android/Termux device, this exact candidate passed `--version`, interactive TUI startup, and one real provider prompt. The Linux CI runner could verify the build and transplant but skipped its runtime TUI probe because it was not AArch64. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
