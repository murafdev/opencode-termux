# Social media pack — OpenCode 2.2.5 for Termux

Copy for announcing the native Termux build. Every claim here is traceable to
`README.md` and `RELEASE_NOTES.md`; see [Claim guardrails](#claim-guardrails)
before editing.

**This is a fork.** Every format below credits the upstream project in the post
body, not only in a reply, bio, or alt text. If you cut a post down, cut a
feature line before you cut the credit line.

**Before posting:** all copy pins `v2.2.5-bun144.1`. If a newer release exists,
update that tag everywhere (search for it) and re-check the install command.

**Canonical links**

- This fork: <https://github.com/murafdev/opencode-termux>
- Release: <https://github.com/murafdev/opencode-termux/releases/tag/v2.2.5-bun144.1>
- Parent project: <https://github.com/Spectra010s/opencode-termux>
- Original Termux port: <https://github.com/Hope2333/opencode-termux>
- Upstream OpenCode: <https://github.com/anomalyco/opencode>
- Install:
  ```sh
  curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
  ```

---

## Credits — paste one

**Short (fits X)**

> Fork of Spectra010s/opencode-termux. Upstream OpenCode: anomalyco/opencode.

**Medium (Reddit, HN, Mastodon)**

> This is a fork of Adeloye Adetayo's (Spectra010s) Termux project, derived
> from Hope2333/opencode-termux. OpenCode itself is anomalyco/opencode. I only
> maintain the fork builds, installer, and release pipeline.

**Full (video description, blog, README)**

> Upstream OpenCode: anomalyco/opencode. Immediate parent project:
> Spectra010s/opencode-termux, maintained by Adeloye Adetayo. That project was
> derived from Hope2333/opencode-termux. This repository contains only the fork
> builds, installer, and release pipeline.

---

## 1. X / Twitter — single post

> OpenCode 2.2.5, running natively in Termux.
>
> No PRoot. No glibc. No Node.js.
>
> One Android/aarch64 Bionic binary (~190 MB). Checksums + optional Sigstore.
>
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
>
> Fork of Spectra010s/opencode-termux. Upstream OpenCode: anomalyco/opencode.

X counts any URL as 23 characters, so this fits in 280. The command is meant to
be copied, not clicked. The credit line is part of the post, not a reply.

---

## 2. X / Twitter — thread

**1/**

> OpenCode 2.2.5 is running natively on Android.
>
> No PRoot. No glibc. No Node.js. Just a single Bionic ELF for aarch64.
>
> Fork of Spectra010s/opencode-termux; OpenCode itself is anomalyco/opencode.
>
> Here is what that means, and how to install it 🧵

**2/**

> Most "AI coding on Android" setups stack a Linux userland on top of Android: PRoot, glibc, a whole distro.
>
> It works, but it is slow to start, fragile to maintain, and heavy.
>
> This build links directly against Android's Bionic libc. One binary, `opencode`, ~190 MB.

**3/**

> Install in Termux:
>
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
>
> Needs Android 9 (API 28)+ on aarch64, and about 500 MB free during install. No root, no storage permission, no shell rc edits.

**4/**

> It is built in GitHub Actions from pinned inputs, not uploaded from a phone.
>
> Releases ship `SHA256SUMS` plus keyless Sigstore bundles. The installer always checks hashes, and checks signatures when `cosign` is present. Set `OPENCODE_REQUIRE_SIGNATURE=1` to make a missing signature fatal.

**5/**

> Two Android-specific fixes:
>
> • Android 11+ tags heap pointers in the top byte. OpenTUI rejected those addresses and aborted startup. The renderer now disables tagging as it loads.
> • Google Play Termux execs binaries through `linker64`. The build detects that and re-execs its server via `/system/bin/sh`.

**6/**

> Your data stays put: the installer only replaces `~/.local/bin/opencode`. Chats, sign-ins, and config are untouched, and `opencode uninstall --dry-run` previews removal.

**7/**

> Caveat, stated plainly: runtime validation is one device (Poco X6 Pro, Android 16). Other Android versions are untested by the maintainer.
>
> If it breaks, open an issue with device model, Android version, and Termux source.
>
> https://github.com/murafdev/opencode-termux

**8/**

> Credit: this build is a fork of Adeloye Adetayo's (Spectra010s) Termux project, derived from Hope2333/opencode-termux. OpenCode itself is anomalyco/opencode.
>
> I only maintain the fork builds, installer, and release pipeline. Credit for the port belongs to them.

---

## 3. Mastodon

> OpenCode 2.2.5 now runs natively in #Termux.
>
> No PRoot, no glibc, no Node.js — a single Android/aarch64 Bionic binary (~190 MB), built in CI from pinned inputs and signed with keyless Sigstore.
>
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
>
> Android 9+ (API 28), aarch64. Validated on one device so far; reports welcome.
>
> Fork of Adeloye Adetayo's (Spectra010s) Termux project; OpenCode by anomalyco/opencode.
>
> https://github.com/murafdev/opencode-termux

Under the default 500-character limit.

---

## 4. Reddit — r/termux

**Title**

> OpenCode 2.2.5 as a native Bionic binary for Termux (no PRoot, no glibc, no Node)

**Body**

> I maintain the fork builds of OpenCode 2 for Termux. The current release runs
> 2.2.5 directly on Android's Bionic libc as a single aarch64 ELF — no PRoot, no
> glibc, no Node.js or npm.
>
> **Credit where it is due:** this is a fork of Adeloye Adetayo's (Spectra010s)
> Termux project, derived from Hope2333/opencode-termux. OpenCode itself is
> anomalyco/opencode. I only maintain the fork builds, installer, and release
> pipeline.
>
> **Install**
>
> ```sh
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
> ```
>
> Requires Android 9 (API 28)+ on aarch64. Allow about 500 MB free during
> install; the installed binary is roughly 190 MB. It lands in
> `~/.local/bin/opencode` and does not edit your shell startup files.
>
> **Why native**
>
> The usual Android setup runs a Linux userland on top of Android. This one
> links against Bionic directly, so there is no container layer to boot or
> maintain.
>
> **Provenance**
>
> Built in GitHub Actions from pinned inputs. Releases include `SHA256SUMS` and
> keyless Sigstore bundles. The installer always verifies checksums, and
> verifies signatures when `cosign` is installed. `OPENCODE_REQUIRE_SIGNATURE=1`
> makes a missing signature fatal. Dependencies are scanned with OSV in CI.
>
> **Android fixes**
>
> - Android 11+ top-byte heap pointer tagging broke OpenTUI startup; the
>   renderer disables tagging on load.
> - The Google Play Termux build execs binaries through `linker64`; the build
>   detects that and re-execs its server through `/system/bin/sh`.
>
> **Caveat**
>
> I have validated this on one device (Poco X6 Pro, Android 16). Other Android
> versions are untested by me. If you try it, please report device model,
> Android version, and Termux source (GitHub, F-Droid, or Play).
>
> **Rollback**
>
> The 2.2.2, 2.2.0, 2.1.4, and both 2.1.3 builds remain available, and the README
> documents how to return to them.
>
> Repo: https://github.com/murafdev/opencode-termux
> Release: https://github.com/murafdev/opencode-termux/releases/tag/v2.2.5-bun144.1

---

## 5. Hacker News — Show HN

**Title**

> Show HN: OpenCode 2.2.5 as a native Bionic binary for Termux

**Text**

> I have been maintaining the fork builds of OpenCode 2 for Termux. The latest
> release runs 2.2.5 on Android/aarch64 as a native Bionic binary — no PRoot, no
> glibc, no Node.js.
>
> It is produced by transplanting the OpenCode source module graph onto a
> hash-verified Android Bun 1.4.4 binary, then patching OpenTUI 0.8.0 for two
> Android issues: top-byte heap pointer tagging on Android 11+, which made the
> TUI abort with "Pointer exceeds safe integer range", and the Google Play
> Termux `linker64` exec path.
>
> Releases are built in GitHub Actions from pinned inputs and published with
> `SHA256SUMS` plus keyless Sigstore bundles. The installer verifies checksums
> and, when `cosign` is present, signatures. There is also an OSV dependency
> gate.
>
> Credit: this is a fork of Adeloye Adetayo's (Spectra010s) Termux project,
> derived from Hope2333/opencode-termux. OpenCode itself is anomalyco/opencode.
> I only maintain the fork builds, installer, and release pipeline.
>
> Caveat: runtime validation is one device (Poco X6 Pro, Android 16), not a
> device matrix. Reports from Android 9–10 and other OEMs would be especially
> useful.
>
> ```sh
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
> ```
>
> Code and build docs: https://github.com/murafdev/opencode-termux

Post Tuesday–Thursday morning US time. Do not ask for votes.

---

## 6. LinkedIn

> Running a full AI coding agent on a phone usually means stacking a Linux
> userland on top of Android: PRoot, glibc, a distro, and a lot of patience.
>
> This release takes a different route. OpenCode 2.2.5 runs as a single native
> Android/aarch64 Bionic binary in Termux — no PRoot, no glibc, no Node.js.
>
> What is inside:
>
> • OpenCode 2.2.5 on Android/Bionic Bun 1.4.4 with OpenTUI 0.8.0
> • CI-built from pinned inputs, with checksums and keyless Sigstore signing
> • Android 11+ pointer-tagging fix and Google Play Termux startup fix
> • One-command install, about 190 MB installed
>
> ```sh
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
> ```
>
> **Credits:** this is a fork of Adeloye Adetayo's (Spectra010s) Termux
> project, derived from Hope2333/opencode-termux. OpenCode itself is
> anomalyco/opencode. I maintain the fork builds and release pipeline.
>
> Caveat worth stating plainly: validation is one device so far. If you run it,
> device reports are genuinely useful.
>
> https://github.com/murafdev/opencode-termux
>
> #Termux #Android #DevTools #OpenSource

---

## 7. Telegram / Discord

> **OpenCode 2.2.5 — native Termux build (fork)**
>
> No PRoot, no glibc, no Node.js. Single Android/aarch64 Bionic binary.
>
> ```sh
> curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.2.5-bun144.1/install.sh | sh
> ```
>
> Android 9+ · ~190 MB installed · checksums always, Sigstore when `cosign` is present
>
> Fork of Adeloye Adetayo's (Spectra010s) Termux project, derived from Hope2333/opencode-termux. OpenCode itself is anomalyco/opencode.
>
> https://github.com/murafdev/opencode-termux
>
> Caveat: validated on one device; reports welcome.

---

## 8. Short video / Reels — 50 seconds

| Time | Visual | Voiceover | On-screen text |
|---|---|---|---|
| 0:00–0:03 | Phone in hand, Termux open | "This is a full AI coding agent running on a phone. Natively." | "No PRoot. No glibc." |
| 0:03–0:10 | `opencode --version` → `2.2.5` | "OpenCode 2.2.5, on Android, as a single Bionic binary." | "OpenCode 2.2.5 · Android/aarch64" |
| 0:10–0:18 | `file ~/.local/bin/opencode` | "No PRoot. No glibc. No Node. It links straight to Android's libc." | "Bionic ELF · ~190 MB" |
| 0:18–0:26 | Paste install command, show checksum lines | "One command installs it. The installer verifies the archive and the binary before replacing anything." | "checksums + optional Sigstore" |
| 0:26–0:34 | TUI, send a prompt, response streams | "Then it is just OpenCode: sessions, tools, your project." | "opencode" |
| 0:34–0:42 | Release page with `SHA256SUMS` and cosign bundles | "Releases are built in CI from pinned inputs, with checksums and Sigstore signatures." | "CI-built · pinned inputs" |
| 0:42–0:50 | Repo page, then the two upstream repos | "This is a fork of Spectra010s's Termux project; OpenCode itself is anomalyco/opencode. Validated on one device so far — tell me how it runs on yours." | "Fork of Spectra010s/opencode-termux · Upstream: anomalyco/opencode" |

---

## 9. Alt text for a TUI screenshot

> Termux terminal on Android showing the OpenCode 2.2.5 TUI: a chat pane with a
> coding prompt and a file tree, with `opencode --version` above it returning
> `2.2.5`.

---

## Claim guardrails

**Safe to say**

- "Native Android/aarch64 Bionic binary"
- "No PRoot, no glibc, no Node.js"
- "Validated on one device (Poco X6 Pro, Android 16)"
- "Checksums always; Sigstore verification when `cosign` is installed"
- "Built in GitHub Actions from pinned inputs"
- "Installed binary is about 190 MB; allow about 500 MB free during install"
- "Fork of Spectra010s/opencode-termux, derived from Hope2333/opencode-termux"
- "OpenCode itself is anomalyco/opencode"

**Do not say**

- "Works on all Android devices" — validation is single-device
- "Tested on Android 9–16" — only Android 16 was tested
- "Faster than PRoot" — no benchmark exists in the repo
- "Audited", "unhackable", "zero dependencies" — it needs `curl`, `sha256sum`,
  `tar`, and Termux itself
- "Replaces your laptop" — not a claim the project makes
- "Official OpenCode build" — this is a fork, not upstream
- "I built OpenCode" or "my OpenCode" — you maintain the fork builds; the app is
  upstream and the Termux port is Spectra010s/Hope2333
- "My Termux port" — same reason

---

## Posting checklist

1. Credit check: every post names Spectra010s/opencode-termux and
   anomalyco/opencode in the body. Not just a reply, not just a bio.
2. Confirm the release tag in the command still matches the latest release.
3. Attach a screenshot or short screen recording; use the alt text above.
4. Put the repo link in the post body, not only in a bio.
5. Good subreddits: r/termux, r/commandline, r/opensource. Avoid r/android —
   this is a Termux tool, not an Android app.
6. Answer device reports with the same questions: model, Android version,
   Termux source, exact error.
