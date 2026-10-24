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

This release is published from a successful GitHub Actions artifact, not from a phone-side build. The source candidate is [Actions run 40054752500](https://github.com/murafdev/opencode-termux/actions/runs/40054752500); its binary SHA-256 is `a66712db76ce82d9156cffc5ae823ef2c9f6feacec4910da3e8dc1ebcdd7d757`. The attached `SHA256SUMS`, supply-chain lock, build-variant metadata, and transplant report record the artifact and pinned inputs.

On one Android/Termux device, this exact candidate passed `--version`, interactive TUI startup, and one real provider prompt. The Linux CI runner could verify the build and transplant but skipped its runtime TUI probe because it was not AArch64. These results are single-device validation, not a claim of multi-device coverage; please report device-specific problems.
