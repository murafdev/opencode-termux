#!/usr/bin/env python3
"""Check native candidate pins and the release-facing version pins.

The candidate may advance before install.sh, README, and the publisher workflow
are promoted. This check verifies both sets independently so a test build does
not accidentally redirect users to an unpublished release or stale artifact.
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
    osv = read(".github/workflows/security-osv.yml")

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
    candidate_tag = re.compile(rf"v{re.escape(version)}-bun144\.\d+")
    if not candidate_tag.fullmatch(build_release_tag):
        fail(f"build TERMUX_RELEASE_TAG {build_release_tag!r} does not match v{version}-bun144.<n>")
    # The candidate may run ahead of the published stable (afce61e built
    # v2.1.4-bun144.1 while install.sh still served v2.1.3-bun144.1), but the
    # publisher must never target a tag the installer does not serve yet: that
    # would publish an unvalidated candidate under the public release tag.
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
    for rollback_tag in ("v2.2.2-bun144.1", "v2.2.0-bun144.1", "v2.1.4-bun144.2", "v2.1.3-bun144.1", "v2.1.3"):
        rollback_installer = f"raw/{rollback_tag}/install.sh"
        if rollback_installer not in readme or rollback_installer not in notes:
            fail(f"README and release notes must retain the {rollback_tag} rollback installer")
    for tag in ("v2.2.2-bun144.1", "v2.2.0-bun144.1", "v2.1.4-bun144.2", "v2.1.3-bun144.1", "v2.1.3"):
        if tag not in publish:
            fail(f"publish workflow must preserve and annotate rollback release {tag}")

    cosign_pins = lock.get("cosign", {})
    if len(cosign_pins) != 1:
        fail("tools/supply-chain-lock.json must pin exactly one cosign release")
    cosign_version, cosign_pin = next(iter(cosign_pins.items()))
    if not re.fullmatch(r"\d+\.\d+\.\d+", cosign_version):
        fail(f"cosign version {cosign_version!r} is not a release version")
    for key in ("linux_amd64_sha256", "linux_arm64_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", cosign_pin.get(key, "")):
            fail(f"cosign {cosign_version} is missing a valid {key}")
    if f"cosign/releases/download/v$cosign_version/cosign-linux-amd64" not in publish:
        fail("publish workflow does not download the pinned cosign release")
    if "id-token: write" not in publish:
        fail("publish workflow must request id-token: write for keyless signing")
    if "sigstore/cosign-installer" in publish:
        fail("publish workflow must install cosign from the hash-pinned release, not a third-party action")
    for bundle in ("dist/SHA256SUMS.cosign.bundle", "dist/$ASSET.tar.gz.cosign.bundle"):
        if f'--bundle "{bundle}"' not in publish:
            fail(f"publish workflow must pass --bundle {bundle} to cosign sign-blob")
        if f'"{bundle}"' not in publish:
            fail(f"publish workflow must upload {bundle}")
    if '--certificate-oidc-issuer "$signer_issuer"' not in installer:
        fail("install.sh must pin the Sigstore OIDC issuer")
    if r"publish-native-android\.yml@refs/(heads|tags)/.+$" not in installer:
        fail("install.sh must pin the release workflow certificate identity")
    if "OPENCODE_REQUIRE_SIGNATURE" not in installer:
        fail("install.sh must document the strict signature mode")

    osv_version_pin = find(r'^\s+OPENCODE_VERSION: "([^"]+)"', osv, "OSV workflow")
    if osv_version_pin != version:
        fail(f"OSV workflow scans OpenCode {osv_version_pin} but the build uses {version}")
    if not re.fullmatch(r"[0-9a-f]{64}", lock["opencode"][version].get("lockfile_sha256", "")):
        fail(f"candidate OpenCode {version} is missing a valid lockfile_sha256")
    osv_pins = lock.get("osv-scanner", {})
    if len(osv_pins) != 1:
        fail("tools/supply-chain-lock.json must pin exactly one osv-scanner release")
    osv_version, osv_pin = next(iter(osv_pins.items()))
    if not re.fullmatch(r"\d+\.\d+\.\d+", osv_version):
        fail(f"osv-scanner version {osv_version!r} is not a release version")
    for key in ("linux_amd64_sha256", "linux_arm64_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", osv_pin.get(key, "")):
            fail(f"osv-scanner {osv_version} is missing a valid {key}")
    if f"osv-scanner/releases/download/v$osv_version/osv-scanner_linux_amd64" not in osv:
        fail("OSV workflow does not download the pinned osv-scanner release")
    if "raw.githubusercontent.com/anomalyco/opencode/$commit/bun.lock" not in osv:
        fail("OSV workflow does not fetch the pinned upstream lockfile")
    if "security-input/bun.lock | sha256sum -c -" not in osv:
        fail("OSV workflow does not verify the pinned lockfile digest")
    if "python3 tools/check-osv.py" not in osv or '--expect-sha256 "$UPSTREAM_LOCK_SHA256"' not in osv:
        fail("OSV workflow must run tools/check-osv.py against the pinned lockfile digest")
    if not (ROOT / "tools/check-osv.py").is_file():
        fail("missing tools/check-osv.py")
    baseline = json.loads(read("security/osv-baseline.json"))
    if baseline.get("schema_version") != 1:
        fail("security/osv-baseline.json must declare schema_version 1")
    if (baseline.get("scope") or {}).get("root") != "@opencode/cli":
        fail("security/osv-baseline.json must scope the @opencode/cli closure")
    for line in osv.splitlines():
        stripped = line.strip()
        if not stripped.startswith("uses:"):
            continue
        reference = stripped.split("uses:", 1)[1].strip().split()[0]
        action, _, revision = reference.partition("@")
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            fail(f"OSV workflow action {action!r} is not pinned to a commit SHA")

    compatible_patch_versions = {
        "0.6.6": {"0.6.6", "0.6.8"},
        "0.7.0": {"0.7.0"},
        "0.8.0": {"0.8.0"},
    }
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
        f"release tag {installer_tag}; osv-scanner {osv_version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
