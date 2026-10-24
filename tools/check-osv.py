#!/usr/bin/env python3
"""Gate critical/high OSV findings in the shipped OpenCode production closure.

The pinned upstream `bun.lock` covers every workspace, including dev-only
tooling. Scanning the whole file produces noise from Storybook, Astro, Vite,
and similar packages that never ship. This gate resolves the production
dependency closure of a workspace root (default: `@opencode/cli`), applies a
checked-in baseline of justified, expiring suppressions, and fails when a
critical/high advisory in that closure is new or its suppression expired.

The closure walk follows only `dependencies`, mirroring what the shipped CLI
can import. Dev dependencies, peer dependencies, and unreferenced duplicate
lockfile entries are ignored.

Exit codes:
  0  no unbaselined critical/high findings and no expired suppressions
  1  gate failure (new finding or expired suppression)
  2  invalid input (lockfile, scan, baseline, or arguments)
"""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = ROOT / "security" / "osv-baseline.json"
DEFAULT_FAIL_ON = ("critical", "high")
EXPIRY_WARNING_DAYS = 14


class GateError(Exception):
    """Invalid input or an unusable lockfile/scan/baseline."""


@dataclass(frozen=True)
class Finding:
    package: str
    version: str
    advisory: str
    aliases: tuple
    severity: str
    summary: str


@dataclass(frozen=True)
class Suppression:
    package: str
    version: str
    advisories: tuple
    reason: str
    expires: date


def strip_trailing_commas(text: str) -> str:
    """Remove JSONC trailing commas without touching string contents."""
    out = []
    in_string = False
    escaped = False
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < length and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < length and text[lookahead] in "}]":
                index += 1
                continue
        out.append(char)
        index += 1
    return "".join(out)


def load_json(path: Path, label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GateError(f"cannot read {label} {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise GateError(f"{label} {path} is not valid JSON: {exc}") from exc


def load_lockfile(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GateError(f"cannot read lockfile {path}: {exc}") from exc
    try:
        data = json.loads(strip_trailing_commas(text))
    except json.JSONDecodeError as exc:
        raise GateError(f"lockfile {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GateError(f"lockfile {path} must contain a JSON object")
    for field in ("packages", "workspaces"):
        if not isinstance(data.get(field), dict):
            raise GateError(f"lockfile {path} is missing the {field!r} object")
    return data


def split_package(resolved: str):
    """Split a lockfile `name@version` string, including scoped names."""
    separator = resolved.find("@", 1) if resolved.startswith("@") else resolved.find("@")
    if separator <= 0 or separator == len(resolved) - 1:
        raise GateError(f"cannot parse lockfile package identity {resolved!r}")
    return resolved[:separator], resolved[separator + 1 :]


def dependency_names(lock) -> tuple:
    names = set()
    for workspace in lock["workspaces"].values():
        names.update((workspace.get("dependencies") or {}).keys())
    for entry in lock["packages"].values():
        info = entry[2] if len(entry) >= 3 else None
        if isinstance(info, dict):
            names.update((info.get("dependencies") or {}).keys())
    return tuple(sorted(names, key=len, reverse=True))


def strip_last_name(key: str, names: tuple):
    """Remove the final package name from a lockfile key path."""
    for name in names:
        if key == name:
            return ""
        suffix = "/" + name
        if key.endswith(suffix):
            return key[: -len(suffix)]
    return None


def resolve_dependency(parent_key: str, name: str, packages: dict, names: tuple):
    """Resolve a dependency the way Bun nests lockfile keys.

    Bun stores a conflicting resolution under `parentKey/name`. Walking the
    parent path outwards handles scoped names (for example
    `@npmcli/run-script` -> `node-gyp/undici`) without treating the scope
    separator as a path separator.
    """
    key = parent_key
    while key:
        candidate = f"{key}/{name}"
        if candidate in packages:
            return candidate
        key = strip_last_name(key, names)
        if key is None:
            break
    if name in packages:
        return name
    return None


def workspace_dependencies(lock, key: str) -> dict:
    entry = lock["packages"][key]
    resolved = entry[0] if entry else None
    if not isinstance(resolved, str):
        raise GateError(f"lockfile entry {key!r} has no resolved package identity")
    if "@workspace:" in resolved:
        path = resolved.rsplit("@workspace:", 1)[1]
        workspace = lock["workspaces"].get(path)
        if workspace is None:
            raise GateError(f"workspace link {resolved!r} points at missing path {path!r}")
        return workspace.get("dependencies") or {}
    info = entry[2] if len(entry) >= 3 else None
    if isinstance(info, dict):
        return info.get("dependencies") or {}
    return {}


def resolve_closure(lock, root: str):
    packages = lock["packages"]
    workspaces = lock["workspaces"]
    root_name = root
    if root in workspaces:
        root_name = workspaces[root].get("name") or root
    if resolve_dependency("", root_name, packages, dependency_names(lock)) is None:
        available = sorted(
            {workspace.get("name") for workspace in workspaces.values() if workspace.get("name")}
        )
        raise GateError(
            f"scope root {root!r} is not in the lockfile; workspace names: {', '.join(available)}"
        )

    names = dependency_names(lock)
    closure = set()
    visited = set()
    pending = [("", root_name)]
    while pending:
        parent_key, name = pending.pop()
        key = resolve_dependency(parent_key, name, packages, names)
        if key is None:
            raise GateError(f"cannot resolve dependency {name!r} from {parent_key or '<root>'}")
        if key in visited:
            continue
        visited.add(key)
        entry = packages[key]
        resolved = entry[0] if entry else None
        if not isinstance(resolved, str):
            raise GateError(f"lockfile entry {key!r} has no resolved package identity")
        if "@workspace:" not in resolved:
            package, version = split_package(resolved)
            closure.add((package, version))
        for child in workspace_dependencies(lock, key):
            pending.append((key, child))
    if not closure:
        raise GateError(f"production closure of {root!r} is empty")
    return closure


def load_findings(path: Path, closure) -> list:
    data = load_json(path, "scan")
    results = data.get("results")
    if not isinstance(results, list):
        raise GateError(f"scan {path} is missing the results list")
    findings = {}
    for result in results:
        for package_entry in result.get("packages") or []:
            package = package_entry.get("package") or {}
            name = package.get("name")
            version = package.get("version")
            if not isinstance(name, str) or not isinstance(version, str):
                raise GateError(f"scan {path} contains a package without name/version")
            if (name, version) not in closure:
                continue
            for vulnerability in package_entry.get("vulnerabilities") or []:
                advisory = vulnerability.get("id")
                if not isinstance(advisory, str):
                    raise GateError(f"scan {path} contains an advisory without an id")
                severity = (vulnerability.get("database_specific") or {}).get("severity")
                severity = str(severity).strip().upper() if severity else "UNKNOWN"
                if severity == "MEDIUM":
                    severity = "MODERATE"
                key = (name, version, advisory)
                if key in findings:
                    continue
                findings[key] = Finding(
                    package=name,
                    version=version,
                    advisory=advisory,
                    aliases=tuple(vulnerability.get("aliases") or ()),
                    severity=severity,
                    summary=(vulnerability.get("summary") or "").strip(),
                )
    return sorted(
        findings.values(), key=lambda item: (item.package, item.version, item.advisory)
    )


def load_baseline(path: Path, root: str) -> list:
    data = load_json(path, "baseline")
    if data.get("schema_version") != 1:
        raise GateError(f"baseline {path} must declare schema_version 1")
    scope = data.get("scope")
    if not isinstance(scope, dict) or scope.get("root") != root:
        raise GateError(
            f"baseline {path} must declare scope.root {root!r} (found {scope!r})"
        )
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise GateError(f"baseline {path} must contain an entries list")
    suppressions = []
    seen = set()
    for index, entry in enumerate(entries, start=1):
        where = f"baseline {path} entry {index}"
        if not isinstance(entry, dict):
            raise GateError(f"{where} must be an object")
        package = entry.get("package")
        version = entry.get("version")
        advisories = entry.get("advisories")
        reason = entry.get("reason")
        expires = entry.get("expires")
        if not isinstance(package, str) or not package:
            raise GateError(f"{where} must declare a package name")
        if not isinstance(version, str) or not version:
            raise GateError(f"{where} must declare a package version")
        if (
            not isinstance(advisories, list)
            or not advisories
            or not all(isinstance(item, str) and item for item in advisories)
        ):
            raise GateError(f"{where} must declare a non-empty advisories list")
        if not isinstance(reason, str) or not reason.strip():
            raise GateError(f"{where} must explain why the suppression is acceptable")
        try:
            expires_on = date.fromisoformat(expires)
        except (TypeError, ValueError) as exc:
            raise GateError(f"{where} must declare an ISO expiry date (YYYY-MM-DD)") from exc
        for advisory in advisories:
            marker = (package, version, advisory)
            if marker in seen:
                raise GateError(f"{where} duplicates {advisory} for {package}@{version}")
            seen.add(marker)
        suppressions.append(
            Suppression(package, version, tuple(advisories), reason.strip(), expires_on)
        )
    return suppressions


def matches(suppression: Suppression, finding: Finding) -> bool:
    if (suppression.package, suppression.version) != (finding.package, finding.version):
        return False
    candidates = {finding.advisory, *finding.aliases}
    return bool(candidates.intersection(suppression.advisories))


def is_gated(severity: str, fail_on) -> bool:
    # Unknown severity fails closed: an unclassified advisory still needs a
    # reviewed suppression instead of silently passing the gate.
    return severity == "UNKNOWN" or severity.lower() in fail_on


def format_identifiers(finding: Finding) -> str:
    if not finding.aliases:
        return finding.advisory
    return f"{finding.advisory} ({', '.join(finding.aliases)})"


def describe_finding(finding: Finding) -> str:
    line = f"  {finding.severity:<8} {finding.package}@{finding.version} {format_identifiers(finding)}"
    if finding.summary:
        line += f": {finding.summary}"
    return line


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail on new critical/high OSV findings in the production closure."
    )
    parser.add_argument("--lockfile", required=True, type=Path, help="pinned upstream bun.lock")
    parser.add_argument("--scan", type=Path, help="osv-scanner JSON output")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=DEFAULT_BASELINE,
        help=f"suppression baseline (default: {DEFAULT_BASELINE})",
    )
    parser.add_argument("--root", default="@opencode/cli", help="production workspace root")
    parser.add_argument(
        "--fail-on",
        default=",".join(DEFAULT_FAIL_ON),
        help="comma-separated severities that fail the gate (default: critical,high)",
    )
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD) for expiry checks")
    parser.add_argument(
        "--expect-sha256",
        help="fail unless the lockfile matches this SHA-256 digest",
    )
    parser.add_argument(
        "--print-closure",
        action="store_true",
        help="print the resolved production closure and exit",
    )
    args = parser.parse_args(argv)

    try:
        if args.expect_sha256:
            try:
                digest = hashlib.sha256(args.lockfile.read_bytes()).hexdigest()
            except OSError as exc:
                raise GateError(f"cannot hash lockfile {args.lockfile}: {exc}") from exc
            if digest != args.expect_sha256:
                raise GateError(
                    f"lockfile {args.lockfile} has SHA-256 {digest}, expected {args.expect_sha256}"
                )
        lock = load_lockfile(args.lockfile)
        closure = resolve_closure(lock, args.root)
        if args.print_closure:
            for package, version in sorted(closure):
                print(f"{package}@{version}")
            return 0
        if args.scan is None:
            raise GateError("--scan is required unless --print-closure is used")

        fail_on = {item.strip().lower() for item in args.fail_on.split(",") if item.strip()}
        if not fail_on:
            raise GateError("--fail-on must name at least one severity")
        unexpected = fail_on - {"critical", "high", "moderate", "low", "unknown"}
        if unexpected:
            raise GateError(f"--fail-on has unknown severity: {', '.join(sorted(unexpected))}")
        if args.today:
            try:
                today = date.fromisoformat(args.today)
            except ValueError as exc:
                raise GateError("--today must be an ISO date (YYYY-MM-DD)") from exc
        else:
            today = datetime.now(timezone.utc).date()

        findings = load_findings(args.scan, closure)
        suppressions = load_baseline(args.baseline, args.root)
    except GateError as exc:
        print(f"check-osv: error: {exc}", file=sys.stderr)
        return 2

    gated = [finding for finding in findings if is_gated(finding.severity, fail_on)]
    unbaselined = []
    expired = []
    used = set()
    for finding in gated:
        matched = [entry for entry in suppressions if matches(entry, finding)]
        if not matched:
            unbaselined.append(finding)
            continue
        used.update(id(entry) for entry in matched)
        for entry in matched:
            if entry.expires < today and id(entry) not in {id(item[0]) for item in expired}:
                expired.append((entry, finding))

    stale = [entry for entry in suppressions if id(entry) not in used]
    expiring = [
        entry
        for entry in suppressions
        if id(entry) in used and today <= entry.expires <= today + timedelta(days=EXPIRY_WARNING_DAYS)
    ]

    print(f"check-osv: scope {args.root}: {len(closure)} production packages")
    print(
        f"check-osv: scan: {len(findings)} advisories in scope "
        f"({len(gated)} at gate severity, {len(findings) - len(gated)} below threshold)"
    )
    print(f"check-osv: baseline: {args.baseline} ({len(suppressions)} suppressions)")

    for entry in stale:
        print(
            "check-osv: warning: suppression no longer matches: "
            f"{entry.package}@{entry.version} [{', '.join(entry.advisories)}]"
        )
    for entry in expiring:
        remaining = (entry.expires - today).days
        print(
            "check-osv: warning: suppression expires soon: "
            f"{entry.package}@{entry.version} [{', '.join(entry.advisories)}] in {remaining} day(s)"
        )

    if unbaselined or expired:
        if unbaselined:
            print(
                f"check-osv: FAIL: {len(unbaselined)} unbaselined finding(s) "
                "at or above the gate severity"
            )
            for finding in unbaselined:
                print(describe_finding(finding))
        if expired:
            print(f"check-osv: FAIL: {len(expired)} expired suppression(s)")
            for entry, finding in expired:
                print(
                    f"  EXPIRED  {entry.package}@{entry.version} "
                    f"{format_identifiers(finding)} (expired {entry.expires.isoformat()}): "
                    f"{entry.reason}"
                )
        print(
            "check-osv: fix the dependency, or add a justified suppression with an expiry "
            "to security/osv-baseline.json"
        )
        return 1

    print(
        "check-osv: OK (no unbaselined gated findings, no expired suppressions)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
