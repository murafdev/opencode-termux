#!/usr/bin/env python3
"""Check that the native release version pins agree across the repository.

A release touches install.sh, both native workflows, the supply-chain lock, the
OpenTUI patch script names, and the release notes. This check fails fast (and
in CI, before a build) when one of them is left on an older version.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def find(pattern: str, text: str, where: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        fail(f"cannot find {pattern!r} in {where}")
    return match.group(1)


def fail(message: str) -> None:
    print(f"check-release-pins: ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    lock = json.loads(read("tools/supply-chain-lock.json"))
    build = read(".github/workflows/build-native-android.yml")
    publish = read(".github/workflows/publish-native-android.yml")
    installer = read("install.sh")

    version = find(r'^\s+OPENCODE_VERSION: "([^"]+)"', build, "build workflow")
    opentui_version = find(r'^\s+OPENTUI_VERSION: "([^"]+)"', build, "build workflow")
    opentui_commit = find(r'^\s+OPENTUI_COMMIT: "([0-9a-f]{40})"', build, "build workflow")
    release_tag = find(r'^\s+RELEASE_TAG: "([^"]+)"', publish, "publish workflow")
    asset = find(r'^\s+ASSET: "([^"]+)"', publish, "publish workflow")
    installer_tag = find(r"^release_tag=(.+)$", installer, "install.sh")
    installer_asset = find(r"^asset=(.+)$", installer, "install.sh")

    if version not in lock["opencode"]:
        fail(f"OpenCode {version} is not pinned in tools/supply-chain-lock.json")
    if opentui_version not in lock["opentui"]:
        fail(f"OpenTUI {opentui_version} is not pinned in tools/supply-chain-lock.json")
    if lock["opentui"][opentui_version]["commit"] != opentui_commit:
        fail(f"OpenTUI {opentui_version} commit does not match the lock")
    if release_tag != f"v{version}":
        fail(f"publish RELEASE_TAG {release_tag!r} does not match v{version}")
    if installer_tag != f"v{version}":
        fail(f"install.sh release_tag {installer_tag!r} does not match v{version}")
    expected_asset = f"opencode-{version}-android-aarch64-source-bun144"
    if asset != expected_asset:
        fail(f"publish ASSET {asset!r} does not match {expected_asset!r}")
    if installer_asset != expected_asset:
        fail(f"install.sh asset {installer_asset!r} does not match {expected_asset!r}")
    if f"opencode-{version}-android-aarch64-source-bun144-candidate" not in publish:
        fail("publish workflow does not download the current candidate artifact")
    if f"raw/v{version}/install.sh" not in read("tools/patch-opencode-source-bun144.py"):
        fail("upgrade guard installer URL does not match the current release tag")
    if f"OpenCode {version} for Termux" not in read("RELEASE_NOTES.md"):
        fail(f"RELEASE_NOTES.md does not describe OpenCode {version}")

    patch_script = f"tools/patch-opentui-{opentui_version}.py"
    if not (ROOT / patch_script).is_file():
        fail(f"missing version-locked renderer patch script: {patch_script}")
    for patch in (
        f"patches/opentui/v{opentui_version}-file-prefix-map.patch",
        f"patches/opentui/v{opentui_version}-tlsdesc-self-resolver.patch",
    ):
        if not (ROOT / patch).is_file():
            fail(f"missing version-locked renderer patch: {patch}")

    print(
        f"check-release-pins: OK (OpenCode {version}, OpenTUI {opentui_version}, "
        f"tag {release_tag})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
