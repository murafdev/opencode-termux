#!/usr/bin/env bats
# Release pins must agree across install.sh, both native workflows, the
# supply-chain lock, the renderer patch files, and the release notes.

load '../lib/helper'

@test "native release pins agree" {
	run python3 "$(script_path tools/check-release-pins.py)"
	[ "$status" -eq 0 ]
	[[ "$output" == *"check-release-pins: OK"* ]]
}
