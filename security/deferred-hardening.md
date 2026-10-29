# Deferred hardening

Residual risk accepted in the native Termux release, with the evidence behind
each decision and the trigger that reopens it. The gate that produces these
lists is documented in [`README.md`](./README.md).

The build installs from the upstream pinned lockfile with `--frozen-lockfile`.
Dependency bumps therefore land upstream and flow in with the next commit pin;
this repository does not re-resolve the graph. That is why several entries below
are "in range, needs a lockfile refresh" rather than "blocked".

Baseline expiry: **2027-01-31**. Re-evaluate on every upstream version pin as
well as at expiry.

## Gated advisories under suppression (1 entry, 1 advisory)

These are the entries in `security/osv-baseline.json`. All are critical/high.

| Package | Advisory | Fix | Holder | Why deferred |
|---|---|---|---|---|
| `zod@3.25.76` | GHSA-mrhx-c7xc-m3w5 (HIGH) | 4.6.6 | `gitlab-ai-provider@6.23.1`: `^3.25.76` | Major-version gap: the provider does not accept zod 4 yet. Reachable in principle by schema validation of an oversized constrained collection; no such input path is known. |

The 2.2.2 lockfile clears the nine other suppressions that applied to 2.2.0:
`seroval`, both `brace-expansion` copies, `http-cache-semantics`, `js-yaml`,
both `undici` copies, and the workspace/MCP `zod` copies now resolve to fixed
releases. The fix column is the release that removes the advisory.

## Below-threshold advisories (0)

The 2.2.2 production closure has no moderate/low findings in scope. The gate
still scans for them on every run so a future pin cannot silently reintroduce
one.

## Bun runtime hardening (RELRO / BIND_NOW)

Measured on the shipped 2.2.x candidate and on the hash-pinned Android Bun
1.4.4 runtime it is built from:

| Property | Result |
|---|---|
| ELF type | `ET_DYN` (PIE), AArch64 |
| `PT_GNU_RELRO` | absent |
| `DT_FLAGS` / `DT_FLAGS_1` BIND_NOW | not set |
| `PT_GNU_STACK` | `RW` (NX stack, correct) |

`bun build --compile` produces the final binary from the Bun executable, so the
compiled `opencode` inherits these program headers; both the shipped 2.2.x
candidate and the Bun 1.4.4 runtime were measured to lack RELRO and BIND_NOW.
Without them the GOT/PLT stays writable after relocation, which makes a
hypothetical memory-corruption bug cheaper to exploit.

This is hardening, not a known vulnerability, and it is deferred because:

- fixing it requires rebuilding Bun with `-Wl,-z,relro,-z,now` and re-validating
  the Android transplant, which is a toolchain change, not a source patch;
- the build consumes a hash-pinned Bun release (`tools/supply-chain-lock.json`),
  so a local relink would break the pin and the reproducibility contract;
- post-link edits to program headers are unsafe: adding a RELRO segment without
  rewriting the dynamic section and relocations can corrupt the binary and would
  make its digest unreproducible.

Upstream ask: ship Android AArch64 Bun release binaries linked with full RELRO
and BIND_NOW (NX stack is already correct). Once a pinned Bun release carries
them, the `opencode` binary inherits the property with no fork-side change.

Check locally with any ELF reader, for example:

```sh
readelf -lW opencode | grep -E 'GNU_RELRO|GNU_STACK'
readelf -dW opencode | grep -E 'BIND_NOW|FLAGS'
```

## Out of scope

- **`@opencode/app` (desktop/web).** Not shipped in the Termux CLI package. Its
  closure now carries `dompurify@3.4.17` and `katex@0.18.11`; it still needs its
  own gate. Tracking it here would mask findings that cannot affect the CLI.
- **Install-time npm tooling.** `@npmcli/arborist` is bundled and runs during
  plugin/package installation and updates; `node-gyp` is spawned only when a
  native dependency is built. Neither runs at startup. Their findings are the
  install-path rows above, which are suppressed only where the advisory is
  critical/high and cannot be fixed in the pinned graph.
- **Bun's embedded third-party code.** The Android Bun runtime contains its own
  `thirdparty/undici` (resolved for bare `undici` imports) and other vendored
  libraries. OSV sees the npm graph, not the runtime binary, so this code is not
  represented in the findings above; its version and fixes belong to Bun
  upstream. Under Bun, bare `undici` imports resolve to the builtin, so the npm
  copies in the closure only matter if the same code runs under Node.
- **Termux system packages** installed via `pkg`/`apt`, which OSV does not scan
  here.
