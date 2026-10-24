# Security gates

## OSV dependency gate

`tools/check-osv.py` runs in `.github/workflows/security-osv.yml` on a weekly
schedule, on demand, and on pull requests that touch the gate itself.

What it scans:

- the upstream `bun.lock` pinned in `tools/supply-chain-lock.json` for the
  current `OPENCODE_VERSION`, fetched by commit and verified by SHA-256;
- only the production dependency closure of `@opencode/cli`; dev-only
  workspaces (Astro, Storybook, Vite, and similar) are excluded.

The closure walk follows `dependencies` from the shipped CLI, including nested
lockfile resolutions. Dev dependencies, peer dependencies, and unreferenced
duplicate versions are ignored, so a finding on a dev-only duplicate does not
mask the shipped version.

What fails the job:

- a `CRITICAL` or `HIGH` advisory in that closure with no baseline entry;
- an advisory whose baseline entry has an expiry date in the past;
- an advisory that OSV does not classify (`UNKNOWN` fails closed).

What does not fail the job:

- `MODERATE`/`LOW` advisories, which are counted in the summary;
- baseline entries that no longer match a finding, which are reported as
  warnings so they can be removed during the next review.

## Baseline policy

`security/osv-baseline.json` only suppresses advisories that cannot be fixed
inside the pinned upstream release. Every entry must:

- name the package, version, and advisory IDs;
- explain why the exposure is acceptable or unreachable;
- carry an ISO expiry date (currently `2027-01-31`).

The expiry is a review trigger, not a promise that the risk disappeared. When
the gate reports `EXPIRED`, either fix the dependency (preferred) or renew the
entry with a fresh justification. Do not blanket-ignore a dev-only advisory:
if the package is in the closure, explain the reachability rather than relying
on its name. Adding a suppression without an expiry, or with an empty reason,
is rejected as invalid input.

Refresh locally:

```sh
python3 tools/check-osv.py \
  --lockfile /path/to/pinned/bun.lock \
  --scan /path/to/osv-scan.json
```

`osv-scanner` is pinned by version and SHA-256 in
`tools/supply-chain-lock.json`; the workflow installs that exact binary instead
of a third-party action. The gate itself only uses the Python standard library.

## Deferred risk

[`deferred-hardening.md`](./deferred-hardening.md) records the residual risk
behind each suppression: reachability evidence, in-range versus out-of-range
fixes, the 16 below-threshold advisories, and the missing RELRO/BIND_NOW
hardening in the Android Bun runtime. Re-evaluate it at the baseline expiry
(`2027-01-31`) and on every upstream version pin.

## Not covered

- the Android/Bionic Bun runtime and OpenTUI binaries, which are pinned by
  SHA-256 in `tools/supply-chain-lock.json` rather than tracked by OSV (their
  hardening status is tracked in `deferred-hardening.md`);
- the `@opencode/app` desktop/web workspace, which is not shipped in the
  Termux binary;
- system packages installed by Termux.
