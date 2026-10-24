#!/usr/bin/env bats
# Config guards bound workspace-controlled parsing in the pinned OpenCode
# source. The patcher must apply cleanly, remain idempotent, and refuse to
# proceed when an upstream anchor has moved.

load '../lib/helper'

PATCHER=""

setup() {
	make_tmpdir
	PATCHER="$(script_path tools/patch-opencode-config-guards.py)"
	python3 "$PATCHER" --write-fixtures "$TEST_TMPDIR"
}

teardown() {
	clean_tmpdir
}

@test "config guard limits reject amplified input" {
	if ! command -v node >/dev/null 2>&1; then
		skip "node not available"
	fi
	run python3 "$PATCHER" --selftest
	[ "$status" -eq 0 ]
	[[ "$output" == *"config-guard self-test: ok"* ]]
}

@test "config guards apply once and re-run as a no-op" {
	run python3 "$PATCHER" "$TEST_TMPDIR"
	[ "$status" -eq 0 ]
	[[ "$output" == *"applied"* ]]
	grep -q "frontmatterBudget(content)" "$TEST_TMPDIR/packages/core/src/config/markdown.ts"
	grep -q "unsafeInstructionPattern(path.isAbsolute(expanded)" \
		"$TEST_TMPDIR/packages/core/src/config/plugin/instruction.ts"

	run python3 "$PATCHER" --check "$TEST_TMPDIR"
	[ "$status" -eq 0 ]
	[[ "$output" == *"applied"* ]]
	[[ "$output" != *"drift"* ]]

	run python3 "$PATCHER" "$TEST_TMPDIR"
	[ "$status" -eq 0 ]
	[[ "$output" == *"skipped"* ]]
	[[ "$output" != *"applied "* ]]
}

@test "config guards export upstream patch files without writing the tree" {
	run python3 "$PATCHER" "$TEST_TMPDIR" --export-patches "$TEST_TMPDIR/patches"
	[ "$status" -eq 0 ]

	local patch
	for patch in opencode-frontmatter-budget.patch opencode-instruction-budget.patch; do
		[ -s "$TEST_TMPDIR/patches/$patch" ]
		grep -q '^--- a/packages/core/src/config/' "$TEST_TMPDIR/patches/$patch"
		grep -q '^+++ b/packages/core/src/config/' "$TEST_TMPDIR/patches/$patch"
	done
	grep -q 'frontmatterBudget(content)' \
		"$TEST_TMPDIR/patches/opencode-frontmatter-budget.patch"
	grep -q 'unsafeInstructionPattern' \
		"$TEST_TMPDIR/patches/opencode-instruction-budget.patch"

	# Export must not modify the checkout it reads.
	! grep -q 'opencode-termux:frontmatter-budget' \
		"$TEST_TMPDIR/packages/core/src/config/markdown.ts"
}

@test "config guards refuse to export from an already patched tree" {
	run python3 "$PATCHER" "$TEST_TMPDIR"
	[ "$status" -eq 0 ]

	run python3 "$PATCHER" "$TEST_TMPDIR" --export-patches "$TEST_TMPDIR/patches"
	[ "$status" -ne 0 ]
	[[ "$output" == *"already contains"* ]]
	[ ! -d "$TEST_TMPDIR/patches" ]
}

@test "config guards fail loudly when the upstream anchor moves" {
	printf 'export function parse(content: string) {\n  // unrelated body\n}\n' \
		> "$TEST_TMPDIR/packages/core/src/config/markdown.ts"

	run python3 "$PATCHER" "$TEST_TMPDIR"
	[ "$status" -ne 0 ]
	[[ "$output" == *"drift"* ]]
	[[ "$output" == *"before re-enabling the guard"* ]]
}
