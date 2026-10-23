#!/system/bin/sh
# Compare official Bun Android/aarch64 release binaries without installing them.
# This script downloads only pinned GitHub release assets, verifies their hashes,
# runs startup/ICU/SQLite/HTTP smoke tests, and writes a report under $HOME.

set -eu

usage() {
  cat <<'EOF'
Usage: sh bun-android-diagnostic.sh [--help]

Run on an Android/Termux aarch64 device. Downloads the official Bun 1.4.0,
1.4.3, and 1.4.4 Android binaries, verifies each archive SHA-256, runs startup,
ICU/locale, SQLite, and local HTTP checks, then saves a report under $HOME.

The script does not install Bun, alter PATH, or modify the existing opencode.
Required commands: curl, unzip, sha256sum, mktemp, date, uname, env, and tee.
EOF
}

case "${1:-}" in
  '') ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

die() {
  printf 'bun-android-diagnostic: ERROR: %s\n' "$*" >&2
  exit 1
}

for tool in curl unzip sha256sum mktemp date uname env tee; do
  command -v "$tool" >/dev/null 2>&1 || die "missing '$tool' (in Termux: pkg install curl unzip coreutils)"
done

: "${HOME:?HOME is not set}"
ARCH=$(uname -m)
case "$ARCH" in
  aarch64|arm64) ;;
  *) die "this diagnostic tests the aarch64 Android assets; uname -m reported '$ARCH'" ;;
esac

STAMP=$(date -u '+%Y%m%dT%H%M%SZ')
REPORT_DIR="$HOME/bun-android-diagnostic-$STAMP-$$"
mkdir -m 700 "$REPORT_DIR" || die "cannot create report directory: $REPORT_DIR"
SUMMARY="$REPORT_DIR/results.txt"
: > "$SUMMARY"

WORK_DIR=
cleanup() {
  case "${WORK_DIR:-}" in
    "$HOME"/.bun-android-check.*) rm -rf "$WORK_DIR" || : ;;
  esac
}
trap cleanup 0
WORK_DIR=$(mktemp -d "$HOME/.bun-android-check.XXXXXX") || die 'mktemp failed'

log() {
  printf '%s\n' "$*" | tee -a "$SUMMARY"
}

run_test() {
  label=$1
  shift
  logfile="$REPORT_DIR/$label.log"

  log ""
  log "===== $label ====="
  if command -v timeout >/dev/null 2>&1; then
    if timeout 25 "$@" > "$logfile" 2>&1; then rc=0; else rc=$?; fi
  else
    if "$@" > "$logfile" 2>&1; then rc=0; else rc=$?; fi
  fi
  LAST_RC=$rc
  log "exit_code=$rc"
  if [ -s "$logfile" ]; then
    cat "$logfile" | tee -a "$SUMMARY"
  else
    log '(no output)'
  fi
  return 0
}

{
  printf 'Created UTC: %s\n' "$STAMP"
  printf 'Architecture: %s\n' "$ARCH"
  printf 'Kernel: '
  uname -a
  if command -v getprop >/dev/null 2>&1; then
    printf 'Android release: '
    getprop ro.build.version.release
    printf 'Android API: '
    getprop ro.build.version.sdk
  fi
  printf 'TERMUX_VERSION=%s\n' "${TERMUX_VERSION-<unset>}"
  printf 'PREFIX=%s\n' "${PREFIX-<unset>}"
  printf 'LANG=%s\n' "${LANG-<unset>}"
  printf 'LC_ALL=%s\n' "${LC_ALL-<unset>}"
  printf 'LC_MESSAGES=%s\n' "${LC_MESSAGES-<unset>}"
  printf 'LD_PRELOAD=%s\n' "${LD_PRELOAD-<unset>}"
  printf 'LD_LIBRARY_PATH=%s\n' "${LD_LIBRARY_PATH-<unset>}"
  printf 'PATH=%s\n' "$PATH"
} > "$REPORT_DIR/system.txt" 2>&1

log "Report directory: $REPORT_DIR"
log "System details are in system.txt. No Bun is installed and PATH/config files are not changed."

if command -v opencode >/dev/null 2>&1; then
  run_test installed-opencode-version opencode --version
else
  log 'No opencode command found in PATH; continuing with official Bun assets.'
fi

EVAL_140=not-run
EVAL_143=not-run
EVAL_144=not-run
INTL_140=not-run
INTL_143=not-run
INTL_144=not-run

for version in 1.4.0 1.4.3 1.4.4; do
  case "$version" in
    1.4.0)
      expected_sha256=42544d7438bb92c7e7df7d30b9a5858cb7a834636608e5b850f59138283567fc
      ;;
    1.4.3)
      expected_sha256=e8848b6c67769ef1dcf932c1aabafbeaefdea0dd98f715e9455424998242deda
      ;;
    1.4.4)
      expected_sha256=d72e42c60e895ccbc16144bb1e0e0ad7ee384841c35b5501a7ec28b4d6d759c9
      ;;
  esac

  asset=bun-linux-aarch64-android.zip
  archive="$WORK_DIR/$asset"
  extract_dir="$WORK_DIR/unpacked-$version"
  url="https://github.com/oven-sh/bun/releases/download/bun-v$version/$asset"

  log ""
  log "===== Downloading official Bun $version ====="
  log "$url"
  curl --fail --location --silent --show-error --retry 2 \
    --connect-timeout 20 --max-time 600 "$url" -o "$archive" || die "download failed for Bun $version"

  checksum_line=$(sha256sum "$archive")
  actual_sha256=${checksum_line%% *}
  log "archive_sha256=$actual_sha256"
  [ "$actual_sha256" = "$expected_sha256" ] || die "SHA-256 mismatch for Bun $version archive"

  if ! unzip -t "$archive" >> "$SUMMARY" 2>&1; then
    die "ZIP integrity check failed for Bun $version"
  fi
  mkdir "$extract_dir"
  unzip -q "$archive" -d "$extract_dir" || die "unzip failed for Bun $version"

  bun="$extract_dir/bun-linux-aarch64-android/bun"
  [ -f "$bun" ] || die "expected Bun executable missing from Bun $version archive"
  chmod 700 "$bun"
  checksum_line=$(sha256sum "$bun")
  log "binary_sha256=${checksum_line%% *} (recorded; archive hash is the pinned check)"

  run_test "bun-$version-version" "$bun" --version
  run_test "bun-$version-eval" "$bun" -e 'console.log("eval-ok", process.versions.bun)'
  eval_rc=$LAST_RC

  run_test "bun-$version-intl-default" "$bun" -e 'console.log(new Date(0).toString()); console.log(Intl.DateTimeFormat().resolvedOptions().locale)'
  intl_rc=$LAST_RC

  run_test "bun-$version-intl-clean-locale" env -u LANG -u LC_ALL -u LC_MESSAGES \
    "$bun" -e 'console.log(new Date(0).toString()); console.log(Intl.DateTimeFormat().resolvedOptions().locale)'

  run_test "bun-$version-intl-invalid-lang" env -u LC_ALL -u LC_MESSAGES LANG=abcdefghijkl \
    "$bun" -e 'console.log(new Date(0).toString()); console.log(Intl.DateTimeFormat().resolvedOptions().locale)'

  if [ "$eval_rc" -eq 0 ]; then
    run_test "bun-$version-sqlite" "$bun" -e 'import { Database } from "bun:sqlite"; const db = new Database(":memory:"); console.log(db.query("select 7 as n").get()); db.close()'
    run_test "bun-$version-http" "$bun" -e 'const s = Bun.serve({port: 0, fetch: () => new Response("ok")}); const r = await fetch("http://127.0.0.1:" + s.port); console.log(r.status, await r.text()); s.stop(true)'
  else
    log "Skipping SQLite and HTTP tests for Bun $version because basic eval failed."
  fi

  case "$version" in
    1.4.0) EVAL_140=$eval_rc; INTL_140=$intl_rc ;;
    1.4.3) EVAL_143=$eval_rc; INTL_143=$intl_rc ;;
    1.4.4) EVAL_144=$eval_rc; INTL_144=$intl_rc ;;
  esac

  rm -f "$archive"
  rm -rf "$extract_dir"
done

log ""
log '===== Result matrix (0 means pass) ====='
log "Bun 1.4.0: eval=$EVAL_140 Intl=$INTL_140"
log "Bun 1.4.3: eval=$EVAL_143 Intl=$INTL_143"
log "Bun 1.4.4: eval=$EVAL_144 Intl=$INTL_144"

if [ "$EVAL_144" = 0 ] && [ "$EVAL_143" != 0 ]; then
  log 'Interpretation: official 1.4.4 eval passed while 1.4.3 failed; this is not the expected pattern. Inspect per-version logs.'
elif [ "$EVAL_144" != 0 ] && [ "$EVAL_143" = 0 ]; then
  log 'Interpretation: official 1.4.4 failed basic JS startup while 1.4.3 passed on this device; this supports a 1.4.4-specific Android runtime regression.'
elif [ "$EVAL_144" = 0 ] && [ "$EVAL_143" = 0 ]; then
  log 'Interpretation: both official binaries passed basic JS startup; if the OpenCode transplant still fails, investigate the compiled/transplanted executable path next.'
else
  log 'Interpretation: basic startup failed for both 1.4.3 and 1.4.4; this does not isolate a 1.4.4-only regression. Compare locale results and system.txt.'
fi

log "Full report: $REPORT_DIR"
log 'Share results.txt and system.txt, plus any failing per-test .log files. Review paths/environment details before sharing.'
