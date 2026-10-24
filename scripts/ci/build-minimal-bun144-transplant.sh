#!/usr/bin/env bash
# Build a tiny source-only standalone graph with Bun 1.4.4 and transplant it
# onto the official Android/Bionic Bun 1.4.4 ELF. This isolates the transplant
# startup path from OpenCode's application graph. Diagnostic-only; not a release.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
: "${OPENCODE_VERSION:?OPENCODE_VERSION must be set}"

readarray -t locked < <(python3 - "$OPENCODE_VERSION" <<'PY'
import json
import sys

version = sys.argv[1]
lock = json.load(open("tools/supply-chain-lock.json", encoding="utf-8"))
host = lock["source_build_bun_1_4_4"]
android = lock["android_bun"]["1.4.4"]
for value in (
    host["linux_x64_archive_sha256"],
    host["linux_aarch64_archive_sha256"],
    android["archive_sha256"],
):
    print(value)
PY
)
test "${#locked[@]}" -eq 3

WORK="work/minimal-bun144-transplant"
mkdir -p "$WORK" artifacts/transplant/android-bun "$WORK/package/bin"
for arch in x64 aarch64; do
  case "$arch" in
    x64) expected="${locked[0]}" ;;
    aarch64) expected="${locked[1]}" ;;
  esac
  archive="$WORK/bun-linux-$arch.zip"
  curl -fsSLo "$archive" "https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-linux-$arch.zip"
  echo "$expected  $archive" | sha256sum -c -
  unzip -oq "$archive" -d "$WORK/$arch"
done

host_bun="$ROOT/$WORK/x64/bun-linux-x64/bun"
target_bun="$ROOT/$WORK/aarch64/bun-linux-aarch64/bun"
test -x "$host_bun"
test -x "$target_bun"
test "$("$host_bun" --version)" = 1.4.4

android_zip="artifacts/transplant/android-bun/bun-1.4.4.zip"
curl -fsSLo "$android_zip" https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-linux-aarch64-android.zip
echo "${locked[2]}  $android_zip" | sha256sum -c -
cp tools/transplant/config/bun-bind-source-1.4.4.json tools/transplant/config/bun-bind.json

cat > "$WORK/main.ts" <<'TS'
console.log("MINIMAL_BUN144_STANDALONE_OK")
TS

cat > "$WORK/build.ts" <<'TS'
const targetElf = process.env.BUN_SOURCE_TARGET_ELF
if (!targetElf) throw new Error("BUN_SOURCE_TARGET_ELF must point to the pinned Linux ARM64 Bun")

const result = await Bun.build({
  entrypoints: ["./main.ts"],
  target: "bun",
  compile: {
    target: "bun-linux-arm64",
    outfile: "./package/bin/opencode",
    executablePath: targetElf,
    execArgv: [
      "--smol",
      `--user-agent=opencode/latest/${process.env.OPENCODE_VERSION}/cli`,
      "--use-system-ca",
      "--no-warnings",
    ],
    autoloadTsconfig: false,
    autoloadPackageJson: false,
    autoloadDotenv: false,
    autoloadBunfig: false,
  },
  bytecode: false,
  throw: true,
})

if (!result.success) throw new Error("Bun.build did not produce the minimal standalone")
TS

(
  cd "$WORK"
  BUN_SOURCE_TARGET_ELF="$target_bun" \
    OPENCODE_VERSION="$OPENCODE_VERSION" \
    "$host_bun" build.ts
)
compiled="$WORK/package/bin/opencode"
test -s "$compiled"
chmod 0755 "$compiled"
tar -czf "$WORK/minimal-bun144-$OPENCODE_VERSION.tgz" -C "$WORK" package

python3 tools/transplant/transplant.py all \
  --ver "$OPENCODE_VERSION" \
  --tgz "$WORK/minimal-bun144-$OPENCODE_VERSION.tgz" \
  --no-execve

out="artifacts/transplant/$OPENCODE_VERSION"
python3 - "$out" "$OPENCODE_VERSION" <<'PY'
import json
import shutil
import sys
from pathlib import Path

out = Path(sys.argv[1])
version = sys.argv[2]
report = json.loads((out / "report.json").read_text(encoding="utf-8"))
revive = report["steps"].get("revive")
assert revive and revive.get("status") == "ok", revive
product = out / "opencode-native-revived"
assert product.is_file() and product.stat().st_size > 50_000_000
candidate = out / "opencode-minimal-bun144-transplant"
shutil.copyfile(product, candidate)
candidate.chmod(0o755)

variant = {
    "candidate": "diagnostic-only",
    "opencode_version_for_transplant_pipeline": version,
    "host_bun": "1.4.4 Linux x64",
    "graph_runtime": "1.4.4 Linux arm64",
    "android_runtime": "1.4.4 aarch64 Bionic",
    "embedded_app": "console.log(MINIMAL_BUN144_STANDALONE_OK)",
    "bytecode": False,
    "execArgv": [
        "--smol",
        f"--user-agent=opencode/latest/{version}/cli",
        "--use-system-ca",
        "--no-warnings",
    ],
    "purpose": "Isolate Bun standalone startup and Android ELF grafting from the OpenCode application graph",
    "on_device_test_required": True,
}
(out / "build-variant.json").write_text(
    json.dumps(variant, indent=2) + "\n", encoding="utf-8"
)
print(f"minimal Bun 1.4.4 transplant candidate: {candidate}")
print(f"build variant: {out / 'build-variant.json'}")
PY
