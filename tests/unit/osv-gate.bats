#!/usr/bin/env bats
# OSV gate: resolve only the production dependency closure, ignore dev-only and
# unreferenced duplicate lockfile entries, and enforce justified, expiring
# suppressions. Fixtures keep the JSONC trailing commas used by upstream bun.lock.

load '../lib/helper'

GATE=""

setup() {
	make_tmpdir
	GATE="$(script_path tools/check-osv.py)"
	LOCKFILE="$TEST_TMPDIR/bun.lock"
	SCAN="$TEST_TMPDIR/scan.json"
	BASELINE="$TEST_TMPDIR/baseline.json"

	cat >"$LOCKFILE" <<'EOF'
{
  "lockfileVersion": 1,
  "configVersion": 1,
  "workspaces": {
    "packages/cli": {
      "name": "@opencode/cli",
      "dependencies": {
        "dep-root": "1.0.0",
      },
      "devDependencies": {
        "dev-only": "1.0.0",
      },
    },
  },
  "packages": {
    "@opencode/cli": ["@opencode/cli@workspace:packages/cli"],
    "dep-root": ["dep-root@1.0.0", "", { "dependencies": { "shared": "^2.0.0" } }],
    "dep-root/shared": ["shared@2.0.1", "", { "dependencies": { "leaf": "^1.0.0" } }],
    "leaf": ["leaf@1.0.0", "", {}],
    "shared": ["shared@3.0.0", "", {}],
    "dev-only": ["dev-only@1.0.0", "", {}],
  },
}
EOF

	write_baseline 2099-01-01
}

teardown() {
	clean_tmpdir
}

scan_entry() {
	cat <<EOF
{
  "package": { "name": "$2", "version": "$3", "ecosystem": "npm" },
  "vulnerabilities": [
    {
      "id": "$4",
      "aliases": ["CVE-0000-0000"],
      "summary": "fixture advisory",
      "database_specific": { "severity": "$1" }
    }
  ]
}
EOF
}

write_scan_entries() {
	{
		printf '{"results":[{"source":{"path":"bun.lock","type":"lockfile"},"packages":['
		first=1
		while [ "$#" -gt 0 ]; do
			[ "$first" = 1 ] || printf ','
			first=0
			scan_entry "$1" "$2" "$3" "$4"
			shift 4
		done
		printf ']}]}'
	} >"$SCAN"
}

write_baseline() {
	cat >"$BASELINE" <<EOF
{
  "schema_version": 1,
  "scope": { "root": "@opencode/cli" },
  "entries": [
    {
      "package": "shared",
      "version": "2.0.1",
      "advisories": ["GHSA-test-0001"],
      "reason": "fixture suppression",
      "expires": "$1"
    }
  ]
}
EOF
}

@test "osv gate ignores dev-only and unreferenced duplicate findings" {
	write_scan_entries CRITICAL dev-only 1.0.0 GHSA-dev-0001 \
		CRITICAL shared 3.0.0 GHSA-top-0001
	cat >"$BASELINE" <<'EOF'
{ "schema_version": 1, "scope": { "root": "@opencode/cli" }, "entries": [] }
EOF

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 0 ]
	[[ "$output" == *"3 production packages"* ]]
	[[ "$output" == *"check-osv: OK"* ]]
}

@test "osv gate resolves nested lockfile duplicates" {
	write_scan_entries HIGH shared 2.0.1 GHSA-test-0001

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 0 ]
	[[ "$output" == *"check-osv: OK"* ]]

	write_scan_entries HIGH shared 3.0.0 GHSA-top-0001
	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 0 ]
	[[ "$output" == *"check-osv: OK"* ]]
}

@test "osv gate fails on a new critical finding" {
	write_scan_entries CRITICAL leaf 1.0.0 GHSA-new-0001

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 1 ]
	[[ "$output" == *"check-osv: FAIL: 1 unbaselined"* ]]
	[[ "$output" == *"CRITICAL leaf@1.0.0 GHSA-new-0001"* ]]
	[[ "$output" == *"security/osv-baseline.json"* ]]
}

@test "osv gate fails when a suppression has expired" {
	write_baseline 2000-01-01
	write_scan_entries HIGH shared 2.0.1 GHSA-test-0001

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 1 ]
	[[ "$output" == *"check-osv: FAIL: 1 expired suppression"* ]]
	[[ "$output" == *"EXPIRED  shared@2.0.1 GHSA-test-0001"* ]]
	[[ "$output" == *"expired 2000-01-01"* ]]
}

@test "osv gate warns about stale suppressions without failing" {
	write_scan_entries LOW leaf 1.0.0 GHSA-low-0001

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 0 ]
	[[ "$output" == *"warning: suppression no longer matches: shared@2.0.1"* ]]
	[[ "$output" == *"check-osv: OK"* ]]
}

@test "osv gate fails closed when severity is missing" {
	cat >"$SCAN" <<'EOF'
{"results":[{"source":{"path":"bun.lock","type":"lockfile"},"packages":[
  {"package":{"name":"leaf","version":"1.0.0","ecosystem":"npm"},
   "vulnerabilities":[{"id":"GHSA-unknown-0001","aliases":[],"summary":"unclassified"}]}
]}]}
EOF

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 1 ]
	[[ "$output" == *"UNKNOWN"* ]]
	[[ "$output" == *"leaf@1.0.0 GHSA-unknown-0001"* ]]
}

@test "osv gate rejects a baseline entry without an expiry" {
	write_scan_entries HIGH shared 2.0.1 GHSA-test-0001
	cat >"$BASELINE" <<'EOF'
{ "schema_version": 1, "scope": { "root": "@opencode/cli" }, "entries": [
  { "package": "shared", "version": "2.0.1", "advisories": ["GHSA-test-0001"], "reason": "fixture" }
] }
EOF

	run python3 "$GATE" --lockfile "$LOCKFILE" --scan "$SCAN" --baseline "$BASELINE"
	[ "$status" -eq 2 ]
	[[ "$output" == *"check-osv: error:"* ]]
	[[ "$output" == *"ISO expiry date"* ]]
}

@test "osv gate verifies the pinned lockfile digest" {
	run python3 "$GATE" --lockfile "$LOCKFILE" --print-closure \
		--expect-sha256 0000000000000000000000000000000000000000000000000000000000000000
	[ "$status" -eq 2 ]
	[[ "$output" == *"SHA-256"* ]]
}
