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

## Gated advisories under suppression (10 entries, 14 advisories)

These are the entries in `security/osv-baseline.json`. All are critical/high.

| Package | Advisory | Fix | Holder | Why deferred |
|---|---|---|---|---|
| `seroval@1.5.6` | GHSA-p6vx-979v-rg4c (CRITICAL), GHSA-jp82-f5mq-hwhp (HIGH) | 1.6.2 / 1.6.3 | `solid-js@1.9.15`: `~1.5.4` | Out of range. Bundle extraction of the shipped CLI found no seroval module: it is the SSR/hydration serializer, and the CLI/TUI uses solid's reactivity without SSR. Needs a `solid-js` release. |
| `brace-expansion@2.1.4` | GHSA-6j4f-fj2g-mc7p, GHSA-qhr7-859c-m2p7 (HIGH) | 2.1.7 | `minimatch@8.0.7`: `^2.0.1` | In range. Reached through build/install-time glob expansion (`babel-plugin-module-resolver` -> `glob@9.3.5`); the runtime instruction guard rejects amplified patterns before expansion regardless of which copy minimatch uses. |
| `brace-expansion@5.0.9` | GHSA-6j4f-fj2g-mc7p, GHSA-qhr7-859c-m2p7 (HIGH) | 5.0.12 | `minimatch@10.2.5`: `^5.0.5` | In range. This copy does expand project `instructions` globs at startup, which is why the call-site guard in `instruction.ts` ships; the dependency refresh is still the durable fix. |
| `http-cache-semantics@4.2.0` | GHSA-ch52-4w7c-c8xp (HIGH) | none published | `@npmcli/arborist@9.4.0` -> `make-fetch-happen` | Bundled npm registry cache used during plugin/package installation (not startup). No fixed release exists; wait for arborist. |
| `js-yaml@3.15.1` | GHSA-2883-xcg3-v3hh (HIGH) | 3.15.2 | `gray-matter@4.0.3`: `^3.13.1` | In range. This copy parses project frontmatter at startup, which is why the 64 KiB / 32-merge-key guard ships. The upstream fix only limits the parser; the budget remains the backstop. |
| `undici@6.28.0` | GHSA-rfgv-xxqx-mfg5, GHSA-xjj6-f33q-929c (HIGH) | 6.29.1 | `node-gyp@12.4.0`: `^6.25.0` | In range. `node-gyp` runs only when installing a native dependency; under Bun its `undici` import resolves to the builtin, not this npm copy. |
| `undici@8.11.2` | GHSA-xjj6-f33q-929c (HIGH) | 8.12.2 | `@effect/platform-node@4.0.1`: `^8.11.2` | In range. The npm copy is not loaded at runtime: Bun resolves the bare `undici` specifier to its own builtin implementation, so the compiled CLI never imports this package. It only matters when the same code runs on Node. |
| `zod@3.25.76` | GHSA-mrhx-c7xc-m3w5 (HIGH) | 4.6.6 | `gitlab-ai-provider@6.19.0`: `^3.25.76` | Major-version gap: the provider does not accept zod 4 yet. Reachable in principle by schema validation of an oversized constrained collection; no such input path is known. |
| `zod@4.1.8` | GHSA-mrhx-c7xc-m3w5 (HIGH) | 4.6.6 | workspace `catalog:` | In range. This is the reachable runtime copy; a catalog bump clears it. |
| `zod@4.4.3` | GHSA-mrhx-c7xc-m3w5 (HIGH) | 4.6.6 | `@modelcontextprotocol/client@2.3.1`: `^4.2.0` | In range. Reached through MCP client message validation; refresh upstream. |

The Fix column is the release that removes the advisory. Where the row says
"in range", the upstream constraint already allows it, so a lockfile refresh is
sufficient; no source change is required.

## Below-threshold advisories (16)

Moderate/low findings in the shipped closure. They do not fail the gate; they
are listed so the inventory is complete.

| Package | Advisory | Severity | Reached through | Note |
|---|---|---|---|---|
| `@ai-sdk/provider-utils@4.0.21` | GHSA-866g-f22w-33x8 | LOW | `@ai-sdk/cohere@3.0.27` (exact pin) | Uncontrolled resource consumption; fixed 4.0.33 needs a provider bump. |
| `@ai-sdk/provider-utils@4.0.23` | GHSA-866g-f22w-33x8 | LOW | workspace `@opencode/core` (exact pin) | Same advisory; another exact pin to move. |
| `brace-expansion@2.1.4` | GHSA-q2hr-2g5m-vwhr | MODERATE | build/install globs | The quadratic `{a},b}` shape is rejected by the instruction guard as well. |
| `brace-expansion@5.0.9` | GHSA-q2hr-2g5m-vwhr | MODERATE | project `instructions` globs | Covered by the call-site guard until the dependency refresh. |
| `ip-address@10.5.0` | GHSA-2vr4-cq9g-pvrc, GHSA-h3mg-xc3c-68pw, GHSA-j6r3-76f7-8jcv, GHSA-rpw4-54j3-4h4q, GHSA-rxp7-6hxx-x8q5 | MODERATE | `socks@2.8.9` (`^10.1.1`) | In range (fixed 10.7.4). Proxy path inside arborist's npm client; only reached when a proxy is configured during plugin install. |
| `postcss-selector-parser@7.1.5` | GHSA-rj75-hqrm-r3gf | MODERATE | `@npmcli/query@5.0.0` (`^7.0.0`) | In range (fixed 7.1.6). Arborist query API; the plugin installer calls `reify`, not `query`. |
| `undici@6.28.0` | GHSA-3wwx-pv8p-q78v, GHSA-4qv8-2p9j-2685 (MODERATE), GHSA-r53p-7pc4-xj5r (LOW) | MODERATE / LOW | `node-gyp` install path | Install-time only; the npm copy is not the runtime HTTP client under Bun. |
| `undici@8.11.2` | GHSA-4qv8-2p9j-2685, GHSA-f72v-6w45-q472 (MODERATE) | MODERATE | `@effect/platform-node` | npm copy only; the compiled CLI resolves `undici` to Bun's builtin (see "Not covered"). |
| `katex@0.16.47` | GHSA-238p-pmpm-9mq7 | LOW | `@opencode/ui` (exact pin) | Requires an existing prototype-pollution primitive to bypass trust restrictions; fixed 0.18.2 needs a UI change. |

## Bun runtime hardening (RELRO / BIND_NOW)

Measured on the shipped 2.1.4 candidate and on the hash-pinned Android Bun
1.4.4 runtime it is built from:

| Property | Result |
|---|---|
| ELF type | `ET_DYN` (PIE), AArch64 |
| `PT_GNU_RELRO` | absent |
| `DT_FLAGS` / `DT_FLAGS_1` BIND_NOW | not set |
| `PT_GNU_STACK` | `RW` (NX stack, correct) |

`bun build --compile` produces the final binary from the Bun executable, so the
compiled `opencode` inherits these program headers; both the shipped 2.1.4
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
  closure currently carries `dompurify@3.4.14` (CRITICAL,
  GHSA-cg2g-xh64-v4q7, fixed 3.4.16/3.4.17) and its own `katex` copy. A release
  of that artifact needs its own gate; tracking it here would mask findings that
  cannot affect the CLI.
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
