#!/usr/bin/env bash
# Runtime-test candidate: build pinned OpenCode source with Bun 1.4.4, but leave
# JavaScript source (not target-specific bytecode) in the graph before grafting
# it onto the official Android/Bionic Bun 1.4.4 runtime.
#
# The CI artifact is not released automatically. It must pass on-device checks
# and the verified CI publishing workflow before it becomes a user release.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
: "${OPENCODE_VERSION:?OPENCODE_VERSION must be set}"
: "${TERMUX_RELEASE_TAG:?TERMUX_RELEASE_TAG must be set}"

readarray -t locked < <(python3 - "$OPENCODE_VERSION" <<'PY'
import json
import sys

version = sys.argv[1]
lock = json.load(open("tools/supply-chain-lock.json", encoding="utf-8"))
oc = lock["opencode"][version]
host = lock["source_build_bun_1_4_4"]
android = lock["android_bun"]["1.4.4"]
for value in (
    oc["commit"],
    host["linux_x64_archive_sha256"],
    host["linux_aarch64_archive_sha256"],
    android["archive_sha256"],
):
    print(value)
PY
)
test "${#locked[@]}" -eq 4
commit="${locked[0]}"

WORK="work/source-bun144-sourcegraph"
mkdir -p "$WORK" artifacts/transplant/android-bun
for arch in x64 aarch64; do
  case "$arch" in
    x64) expected="${locked[1]}" ;;
    aarch64) expected="${locked[2]}" ;;
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
echo "${locked[3]}  $android_zip" | sha256sum -c -
cp tools/transplant/config/bun-bind-source-1.4.4.json tools/transplant/config/bun-bind.json

src="$ROOT/$WORK/opencode"
mkdir -p "$src"
git -C "$src" init .
git -C "$src" remote add origin https://github.com/anomalyco/opencode.git
git -C "$src" fetch --depth=1 origin "$commit"
git -C "$src" checkout --detach FETCH_HEAD
test "$(git -C "$src" rev-parse HEAD)" = "$commit"
python3 tools/patch-opencode-source-bun140.py \
  "$src" --bun-version 1.4.4 --disable-bytecode \
  --release-tag "$TERMUX_RELEASE_TAG"
python3 tools/patch-opencode-config-guards.py "$src"

python3 - "$WORK/build-variant.json" "$commit" "$TERMUX_RELEASE_TAG" "$OPENCODE_VERSION" <<'PY'
import json
import sys

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(
        {
            "candidate": "runtime-test",
            "host_bun": "1.4.4 Linux x64",
            "target_graph": "bun-linux-arm64",
            "android_runtime": "1.4.4 aarch64 Bionic",
            "bytecode": False,
            "opencode_commit": sys.argv[2],
            "termux_release_tag": sys.argv[3],
            "opencode_version": sys.argv[4],
            "purpose": f"Device-test OpenCode {sys.argv[4]} on Android/Bionic Bun 1.4.4",
        },
        f,
        indent=2,
    )
    f.write("\n")
PY

cd "$src"
"$host_bun" install --frozen-lockfile --ignore-scripts --os=linux --cpu='*'
cd "$src/packages/cli"
# OpenCode 2.2.0 replaced the --target flag with OPENCODE_TARGET and silently
# ignores the old flag. Pass both so pre-2.2 rollback builds and 2.2+ builds
# select the same target; the assertion below fails if neither takes effect and
# the build emits the host graph or every cross target instead.
OPENCODE_TARGET=linux-arm64 \
BUN_SOURCE_TARGET_ELF="$target_bun" \
  "$host_bun" script/build.ts --target=opencode-linux-arm64 --skip-install
test "$(find dist -mindepth 1 -maxdepth 1 -type d -name 'cli-*' | wc -l)" -eq 1
compiled="$src/packages/cli/dist/cli-linux-arm64/bin/opencode"
test -s "$compiled"
mkdir -p "$ROOT/$WORK/package/bin"
cp "$compiled" "$ROOT/$WORK/package/bin/opencode"
cd "$ROOT/$WORK"
tar -czf "opencode-$OPENCODE_VERSION-source-bun144-sourcegraph.tgz" package
cd "$ROOT"

python3 tools/transplant/transplant.py all \
  --ver "$OPENCODE_VERSION" \
  --tgz "$WORK/opencode-$OPENCODE_VERSION-source-bun144-sourcegraph.tgz" \
  --no-execve

out="artifacts/transplant/$OPENCODE_VERSION"
cp "$WORK/build-variant.json" "$out/build-variant.json"
python3 - "$out" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
report = json.loads((out / "report.json").read_text(encoding="utf-8"))
swap = report["steps"].get("swap")
assert swap and swap["status"] == "ok", report["steps"].get("tui_probe")
product = out / "opencode-native-tui"
assert product.is_file() and product.stat().st_size > 50_000_000
print(f"diagnostic source-mode candidate: {product}")
print(f"build variant: {out / 'build-variant.json'}")
PY
