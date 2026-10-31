#!/bin/sh
set -eu

release_tag=v2.2.5-bun144.1
asset=opencode-2.2.5-android-aarch64-source-bun144-sourcegraph
archive="$asset.tar.gz"
base_url="https://github.com/murafdev/opencode-termux/releases/download/$release_tag"
destination="$HOME/.local/bin/opencode"

# Keyless Sigstore identity of the release workflow. Both checks are pinned so a
# signature from any other workflow, repository, or OIDC issuer is rejected.
signer_identity='^https://github\.com/murafdev/opencode-termux/\.github/workflows/publish-native-android\.yml@refs/(heads|tags)/.+$'
signer_issuer='https://token.actions.githubusercontent.com'
signer_repository='murafdev/opencode-termux'

for tool in curl sha256sum tar mktemp install mv uname getprop awk; do
  command -v "$tool" >/dev/null 2>&1 || { printf 'Missing command: %s\n' "$tool" >&2; exit 1; }
done

[ "$(uname -m)" = aarch64 ] || { echo 'This release requires Android aarch64.' >&2; exit 1; }
android_api=$(getprop ro.build.version.sdk)
case "$android_api" in
  ''|*[!0-9]*) echo 'Could not detect Android API level.' >&2; exit 1 ;;
esac
[ "$android_api" -ge 28 ] || { echo 'This release requires Android API 28 or newer.' >&2; exit 1; }

verify_signature() {
  blob=$1
  bundle=$2
  if ! cosign verify-blob \
    --bundle "$bundle" \
    --certificate-identity-regexp "$signer_identity" \
    --certificate-oidc-issuer "$signer_issuer" \
    --certificate-github-workflow-repository "$signer_repository" \
    "$blob"; then
    printf 'Signature verification failed for %s.\n' "$blob" >&2
    exit 1
  fi
}

temporary_dir=$(mktemp -d)
trap 'rm -rf -- "$temporary_dir"' EXIT HUP INT TERM

if command -v cosign >/dev/null 2>&1; then
  signed=1
elif [ "${OPENCODE_REQUIRE_SIGNATURE:-0}" = 1 ]; then
  echo 'OPENCODE_REQUIRE_SIGNATURE=1 but cosign is not installed.' >&2
  exit 1
else
  signed=0
  echo 'Warning: cosign is not installed; skipping signature verification.' >&2
  echo 'Set OPENCODE_REQUIRE_SIGNATURE=1 to make a missing signature fatal.' >&2
fi

curl -fL --retry 3 -o "$temporary_dir/SHA256SUMS" "$base_url/SHA256SUMS"
if [ "$signed" = 1 ]; then
  # Verify the checksum list before trusting any digest in it.
  curl -fL --retry 3 -o "$temporary_dir/SHA256SUMS.cosign.bundle" "$base_url/SHA256SUMS.cosign.bundle"
  verify_signature "$temporary_dir/SHA256SUMS" "$temporary_dir/SHA256SUMS.cosign.bundle"
fi

curl -fL --retry 3 -o "$temporary_dir/$archive" "$base_url/$archive"
checksum_line=$(awk -v name="$archive" '$2 == name && length($1) == 64 { print }' "$temporary_dir/SHA256SUMS")
[ -n "$checksum_line" ] || { echo 'Release checksum for archive is missing.' >&2; exit 1; }
[ "$(printf '%s\n' "$checksum_line" | awk 'END { print NR }')" -eq 1 ] || { echo 'Release archive checksum is ambiguous.' >&2; exit 1; }
printf '%s\n' "$checksum_line" | (cd "$temporary_dir" && sha256sum -c -)

if [ "$signed" = 1 ]; then
  # Bind the downloaded archive itself to the release workflow identity.
  curl -fL --retry 3 -o "$temporary_dir/$archive.cosign.bundle" "$base_url/$archive.cosign.bundle"
  verify_signature "$temporary_dir/$archive" "$temporary_dir/$archive.cosign.bundle"
fi

tar -xzf "$temporary_dir/$archive" -C "$temporary_dir" "$asset"
checksum_line=$(awk -v name="$asset" '$2 == name && length($1) == 64 { print }' "$temporary_dir/SHA256SUMS")
[ -n "$checksum_line" ] || { echo 'Release checksum for binary is missing.' >&2; exit 1; }
[ "$(printf '%s\n' "$checksum_line" | awk 'END { print NR }')" -eq 1 ] || { echo 'Release binary checksum is ambiguous.' >&2; exit 1; }
printf '%s\n' "$checksum_line" | (cd "$temporary_dir" && sha256sum -c -)

mkdir -p "$HOME/.local/bin"
install -m 755 "$temporary_dir/$asset" "$destination.new.$$"
mv -f "$destination.new.$$" "$destination"
printf 'Installed: %s\n' "$destination"

case ":$PATH:" in
  *":$HOME/.local/bin:"*) printf 'Run: opencode\n' ;;
  *)
    printf 'Run now: %s\n' "$destination"
    printf 'To add it to PATH in your shell, add this line to ~/.bashrc (or your shell startup file):\n'
    printf 'export PATH="$HOME/.local/bin:$PATH"\n'
    ;;
esac
