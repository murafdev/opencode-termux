#!/usr/bin/env bats
# install.sh must verify the Sigstore bundles when cosign is available, refuse a
# bad signature, and only skip verification when the user has not opted into
# strict mode.

load '../lib/helper'

ARCHIVE="opencode-2.2.0-android-aarch64-source-bun144-sourcegraph.tar.gz"
ASSET="opencode-2.2.0-android-aarch64-source-bun144-sourcegraph"

setup() {
	make_tmpdir
	INSTALLER="$(script_path install.sh)"
	CORE_BIN="$TEST_TMPDIR/core-bin"
	COSIGN_BIN="$TEST_TMPDIR/cosign-bin"
	mkdir -p "$CORE_BIN" "$COSIGN_BIN" "$TEST_TMPDIR/home" "$TEST_TMPDIR/payload"

	export HOME="$TEST_TMPDIR/home"
	export FAKE_PAYLOAD="$TEST_TMPDIR/payload/$ASSET"
	export FAKE_ARCHIVE="$ARCHIVE"
	export FAKE_ASSET="$ASSET"
	export COSIGN_LOG="$TEST_TMPDIR/cosign.log"
	printf 'fake opencode binary\n' >"$FAKE_PAYLOAD"

	write_core_stubs
	write_cosign_stub
	PATH="$CORE_BIN:$PATH"
	export PATH
}

teardown() {
	clean_tmpdir
}

write_core_stubs() {
	cat >"$CORE_BIN/uname" <<'EOF'
#!/bin/sh
[ "$1" = "-m" ] && echo aarch64
EOF
	cat >"$CORE_BIN/getprop" <<'EOF'
#!/bin/sh
echo 34
EOF
	cat >"$CORE_BIN/sha256sum" <<'EOF'
#!/bin/sh
cat >/dev/null
echo "sha256sum: ok"
EOF
	cat >"$CORE_BIN/install" <<'EOF'
#!/bin/sh
# install -m MODE SRC DST
while [ $# -gt 0 ]; do
	case "$1" in
		-m) shift 2 ;;
		*) break ;;
	esac
done
cp "$1" "$2"
chmod 755 "$2"
EOF
	cat >"$CORE_BIN/tar" <<'EOF'
#!/bin/sh
# tar -xzf ARCHIVE -C DIR ASSET
while [ $# -gt 0 ]; do
	case "$1" in
		-xzf) shift 2 ;;
		-C) dir="$2"; shift 2 ;;
		*) asset="$1"; shift ;;
	esac
done
cp "$FAKE_PAYLOAD" "$dir/$asset"
EOF
	cat >"$CORE_BIN/curl" <<'EOF'
#!/bin/sh
out=
url=
while [ $# -gt 0 ]; do
	case "$1" in
		-fL) shift ;;
		--retry) shift 2 ;;
		-o) out="$2"; shift 2 ;;
		*) url="$1"; shift ;;
	esac
done
case "$url" in
	*/SHA256SUMS)
		{
			printf '%s  %s\n' "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" "$FAKE_ARCHIVE"
			printf '%s  %s\n' "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef" "$FAKE_ASSET"
		} >"$out"
		;;
	*"$FAKE_ARCHIVE".cosign.bundle) printf 'bundle\n' >"$out" ;;
	*"$FAKE_ARCHIVE") cp "$FAKE_PAYLOAD" "$out" ;;
	*SHA256SUMS.cosign.bundle) printf 'bundle\n' >"$out" ;;
	*) exit 22 ;;
esac
EOF
	chmod 755 "$CORE_BIN"/*
}

write_cosign_stub() {
	cat >"$COSIGN_BIN/cosign" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >>"$COSIGN_LOG"
[ "${FAKE_COSIGN_RESULT:-ok}" = ok ]
EOF
	chmod 755 "$COSIGN_BIN/cosign"
}

enable_cosign() {
	PATH="$COSIGN_BIN:$PATH"
	export PATH
}

@test "install.sh verifies both bundles when cosign is present" {
	enable_cosign
	run "$INSTALLER"
	[ "$status" -eq 0 ]
	[ -f "$HOME/.local/bin/opencode" ]
	grep -q 'fake opencode binary' "$HOME/.local/bin/opencode"

	[ -f "$COSIGN_LOG" ]
	[ "$(wc -l <"$COSIGN_LOG")" -eq 2 ]
	grep -q -- "--certificate-oidc-issuer https://token.actions.githubusercontent.com" "$COSIGN_LOG"
	grep -q -- "--certificate-identity-regexp" "$COSIGN_LOG"
	grep -q "publish-native-android" "$COSIGN_LOG"
	grep -q "SHA256SUMS.cosign.bundle" "$COSIGN_LOG"
	grep -q "$ARCHIVE.cosign.bundle" "$COSIGN_LOG"
}

@test "install.sh refuses to install when a signature fails" {
	enable_cosign
	FAKE_COSIGN_RESULT=fail
	export FAKE_COSIGN_RESULT
	run "$INSTALLER"
	[ "$status" -ne 0 ]
	[[ "$output" == *"Signature verification failed"* ]]
	[ ! -e "$HOME/.local/bin/opencode" ]
}

@test "install.sh requires cosign in strict mode" {
	OPENCODE_REQUIRE_SIGNATURE=1
	export OPENCODE_REQUIRE_SIGNATURE
	run "$INSTALLER"
	[ "$status" -ne 0 ]
	[[ "$output" == *"OPENCODE_REQUIRE_SIGNATURE=1 but cosign is not installed"* ]]
	[ ! -e "$HOME/.local/bin/opencode" ]
}

@test "install.sh warns and continues when cosign is absent" {
	run "$INSTALLER"
	[ "$status" -eq 0 ]
	[[ "$output" == *"Warning: cosign is not installed"* ]]
	[ -f "$HOME/.local/bin/opencode" ]
}
