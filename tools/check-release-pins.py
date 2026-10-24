#!/usr/bin/env python3
"""Check the native candidate pins while keeping the published release stable.

The candidate may advance before install.sh, README, and the publisher workflow
are promoted. This check verifies both sets independently so a test build does
not accidentally redirect users to an unpublished release.
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
    readme = read("README.md")
    notes = read("RELEASE_NOTES.md")
    sourcegraph = read("scripts/ci/build-opencode-source-bun144-sourcegraph.sh")

    version = find(r'^\s+OPENCODE_VERSION: "([^"]+)"', build, "build workflow")
    opentui_version = find(r'^\s+OPENTUI_VERSION: "([^"]+)"', build, "build workflow")
    opentui_patch_version = find(r'^\s+OPENTUI_PATCH_VERSION: "([^"]+)"', build, "build workflow")
    opentui_commit = find(r'^\s+OPENTUI_COMMIT: "([0-9a-f]{40})"', build, "build workflow")
    build_release_tag = find(r'^\s+TERMUX_RELEASE_TAG: "([^"]+)"', build, "build workflow")
    release_tag = find(r'^\s+RELEASE_TAG: "([^"]+)"', publish, "publish workflow")
    asset = find(r'^\s+ASSET: "([^"]+)"', publish, "publish workflow")
    installer_tag = find(r"^release_tag=(.+)$", installer, "install.sh")
    installer_asset = find(r"^asset=(.+)$", installer, "install.sh")

    stable_match = re.fullmatch(r"v(\d+\.\d+\.\d+)(?:-[A-Za-z0-9.-]+)?", installer_tag)
    if not stable_match:
        fail(f"cannot derive the current stable version from installer tag {installer_tag!r}")
    stable_version = stable_match.group(1)

    if version not in lock["opencode"]:
        fail(f"candidate OpenCode {version} is not pinned in tools/supply-chain-lock.json")
    if stable_version not in lock["opencode"]:
        fail(f"stable OpenCode {stable_version} is not pinned in tools/supply-chain-lock.json")
    if lock["opencode"][version].get("bun_version") != "1.4.4":
        fail(f"candidate OpenCode {version} does not select the Bun 1.4.4 runtime")
    if opentui_version not in lock["opentui"]:
        fail(f"OpenTUI {opentui_version} is not pinned in tools/supply-chain-lock.json")
    if lock["opentui"][opentui_version]["commit"] != opentui_commit:
        fail(f"OpenTUI {opentui_version} commit does not match the lock")
    expected_candidate_tag = f"v{version}-bun144.1"
    if build_release_tag != expected_candidate_tag:
        fail(f"build TERMUX_RELEASE_TAG {build_release_tag!r} does not match {expected_candidate_tag!r}")
    if release_tag != installer_tag:
        fail(f"publish RELEASE_TAG {release_tag!r} differs from current installer tag {installer_tag!r}")
    expected_stable_asset = f"opencode-{stable_version}-android-aarch64-source-bun144-sourcegraph"
    if asset != expected_stable_asset:
        fail(f"publish ASSET {asset!r} does not match current stable asset {expected_stable_asset!r}")
    if installer_asset != expected_stable_asset:
        fail(f"install.sh asset {installer_asset!r} does not match current stable asset {expected_stable_asset!r}")
    if "opencode-$OPENCODE_VERSION-android-aarch64-source-bun144-sourcegraph-candidate" not in publish:
        fail("publish workflow does not download the current candidate artifact")
    if '"$TERMUX_RELEASE_TAG"' not in sourcegraph or "--release-tag" not in sourcegraph:
        fail("Bun 1.4.4 build does not embed the current release installer URL")
    if "default: source-bun144-sourcegraph" not in build:
        fail("Bun 1.4.4 source-graph strategy must be the default build")
    if f"OpenCode {stable_version} for Termux" not in notes:
        fail(f"RELEASE_NOTES.md does not describe current stable OpenCode {stable_version}")
    if f"releases/tag/{installer_tag}" not in readme:
        fail("README does not link to the current stable release page")
    if f"raw/{installer_tag}/install.sh" not in readme or f"raw/{installer_tag}/install.sh" not in notes:
        fail("README and release notes must use the current stable release installer")
    if f"raw/v{stable_version}/install.sh" not in readme or f"raw/v{stable_version}/install.sh" not in notes:
        fail(f"README and release notes must retain the v{stable_version} Bun 1.4.0 rollback")

    compatible_patch_versions = {"0.6.6": {"0.6.6", "0.6.8"}}
    if opentui_patch_version not in compatible_patch_versions or opentui_version not in compatible_patch_versions[opentui_patch_version]:
        fail(f"OpenTUI {opentui_version} has no validated Android patch set {opentui_patch_version}")
    patch_script = f"tools/patch-opentui-{opentui_patch_version}.py"
    if not (ROOT / patch_script).is_file():
        fail(f"missing version-locked renderer patch script: {patch_script}")
    for patch in (
        f"patches/opentui/v{opentui_patch_version}-file-prefix-map.patch",
        f"patches/opentui/v{opentui_patch_version}-tlsdesc-self-resolver.patch",
    ):
        if not (ROOT / patch).is_file():
            fail(f"missing version-locked renderer patch: {patch}")

    print(
        f"check-release-pins: OK (candidate OpenCode {version}, OpenTUI {opentui_version} "
        f"with Android patch set {opentui_patch_version}; "
        f"stable tag {installer_tag})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
