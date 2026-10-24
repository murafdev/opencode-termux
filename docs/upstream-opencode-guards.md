# Upstreaming the OpenCode config-parsing guards

Status: **prepared, not filed.** These guards ship in the Termux build from
`tools/patch-opencode-config-guards.py`; the patches under `patches/opencode/`
are the same diff exported for upstream review.

Target: `github.com/anomalyco/opencode`, default branch `dev`, based on commit
`68bc26b7da1990ce10ffecfbc1e09eb13aa5d824` (OpenCode 2.1.4).

| Path | Advisory | Severity |
|---|---|---|
| `packages/core/src/config/markdown.ts` | GHSA-2883-xcg3-v3hh / CVE-2026-84375 | HIGH |
| `packages/core/src/config/plugin/instruction.ts` | GHSA-6j4f-fj2g-mc7p / CVE-2026-102276 | HIGH |
| `packages/core/src/config/plugin/instruction.ts` | GHSA-q2hr-2g5m-vwhr / CVE-2026-102277 | MODERATE |
| `packages/core/src/config/plugin/instruction.ts` | GHSA-qhr7-859c-m2p7 / CVE-2026-102278 | HIGH |

## Threat model

`opencode` parses project-controlled configuration during startup, before the
user types anything:

- `**/*.md` frontmatter for project agents, commands, and skills, parsed by
  `gray-matter` -> `js-yaml`;
- the `instructions` list from project config, expanded through
  `minimatch` -> `brace-expansion`.

Cloning an untrusted repository and running `opencode` inside it therefore hands
the repository author two CPU-exhaustion primitives. Impact is denial of
service: startup hangs or burns CPU proportional to crafted input, not code
execution or data exfiltration. It is still a routine "clone and run" path,
which is why it is worth bounding in the parser call sites.

## What the patch does

Both guards are additive, bounded far above real-world configs, and sit at the
call site so they keep working if the dependency is patched, re-vendored, or
replaced.

### Frontmatter budget (`markdown.ts`)

`parse()` calls `frontmatterBudget(content)` before `matter(content, ...)`:

| Limit | Value | Rationale |
|---|---|---|
| Frontmatter size | 64 KiB | Larger than any real agent/command/skill header by orders of magnitude |
| `<<` merge keys | 32 | Amplification vector in CVE-2026-84375 |

Violations throw `Error("frontmatter exceeds ...")`. A file whose frontmatter
is hostile is unusable as an agent/command/skill definition anyway, so failing
that one file loudly is preferable to silently ignoring it.

### Instruction-glob budget (`instruction.ts`)

The `match()` helper calls `unsafeInstructionPattern()` before glob expansion:

| Limit | Value |
|---|---|
| Pattern length | 1024 chars |
| Brace nesting depth | 8 |
| Brace groups | 32 |
| Commas inside braces | 32 |
| Cartesian expansion product | 256 |
| Numeric-range span | 4096 |

A rejected pattern is skipped and logged at debug level (`reason:
"expansion-budget"`) with a 64-character prefix and its length; the remaining
instruction sources still load. That asymmetry is deliberate: one bad entry in a
list should not discard the whole list, whereas a bad frontmatter block belongs
to exactly one file.

Absolute paths (including `~/...`) are scanned by basename with the directory as
`cwd`, so the guard checks the same segment that is globbed there.

## Reproduction

Before the patch, in a scratch repository:

```sh
mkdir -p .opencode/agent

# 1) Frontmatter amplification: repeated empty merge sources.
python3 - <<'PY'
lines = ["---"] + ["<<: {}"] * 200_000 + ["---", "body"]
open(".opencode/agent/merge.md", "w").write("\n".join(lines))
PY

# 2) Glob amplification: exponential brace groups.
printf '{"instructions": ["%s"]}\n' \
  "$(python3 -c 'print("{a,b}" * 16)')" > opencode.json
```

`opencode` then stalls during config load. After the patch, (1) fails fast with
a frontmatter budget error and (2) logs the skipped pattern and starts normally.

## Verification performed

- `python3 tools/patch-opencode-config-guards.py --selftest` exercises both
  guards with Node: normal frontmatter and globs pass; 33 merge keys, an
  oversized block, deep nesting, expansion flood, oversized patterns, and huge
  numeric ranges are rejected.
- Applied against the real pinned 2.1.4 source: +20 lines in `markdown.ts`,
  +58 lines in `instruction.ts`; `node --check` (after type stripping) passes.
- Real-world inputs (agent/command/skill frontmatter and instruction globs,
  including nested and numeric-range globs) parse byte-identically before and
  after the guard.
- `tests/unit/config-guards.bats` covers idempotent application, anchor drift,
  and patch export.

## Ready-to-paste PR

Start from the pinned commit in a fork, apply the generated patches, and push a
branch:

```sh
git clone https://github.com/<you>/opencode && cd opencode
git checkout -b fix/config-parsing-budgets 68bc26b7da1990ce10ffecfbc1e09eb13aa5d824
git apply /path/to/patches/opencode/opencode-frontmatter-budget.patch \
          /path/to/patches/opencode/opencode-instruction-budget.patch
git commit -am "fix(config): bound project-controlled frontmatter and instruction globs"
git push origin fix/config-parsing-budgets
```

Then open against `dev`, saving the fenced block below as
`/tmp/opencode-config-guards.md` first:

```sh
gh pr create --repo anomalyco/opencode --base dev \
  --title "fix(config): bound project-controlled frontmatter and instruction globs" \
  --body-file /tmp/opencode-config-guards.md
```

````markdown
## Summary

Bounds two project-controlled parsing paths that can exhaust CPU during startup:

- markdown frontmatter (`gray-matter` -> `js-yaml`), GHSA-2883-xcg3-v3hh / CVE-2026-84375;
- the `instructions` glob list (`minimatch` -> `brace-expansion`),
  GHSA-6j4f-fj2g-mc7p / CVE-2026-102276, GHSA-q2hr-2g5m-vwhr / CVE-2026-102277,
  GHSA-qhr7-859c-m2p7 / CVE-2026-102278.

Opening an untrusted checkout currently lets the repository author hang startup.
The guards bound that work at the call sites, so they remain effective even
after the underlying packages are upgraded.

## What changed

- `packages/core/src/config/markdown.ts`: reject frontmatter larger than 64 KiB
  or with more than 32 `<<` merge keys before calling `gray-matter`.
- `packages/core/src/config/plugin/instruction.ts`: skip an instruction pattern
  that exceeds 1024 chars, 8 brace levels, 32 groups, 32 in-brace commas, an
  expansion product of 256, or a numeric-range span of 4096. The skip is logged
  at debug level and other patterns still load.

Both limits are far above real configurations. No config format, API, or output
of well-formed input changes.

## Tests

- `--selftest` in the patch generation script (Node) covers accept/reject cases
  for both guards, including 33 merge keys, oversized frontmatter, deep nesting,
  expansion floods, and `{1..1000000}`.
- Applied to 2.1.4: normal agent/command/skill frontmatter and instruction
  globs parse identically before and after.
- `node --check` passes on both patched files.

## Notes

These are defense-in-depth bounds, not a replacement for dependency upgrades.
`gray-matter` already allows `js-yaml@^3.13.1` (3.15.2 fixes CVE-2026-84375), and
the installed `minimatch@8.0.7` / `minimatch@10.2.5` already allow fixed
`brace-expansion` releases (`^2.0.1` / `^5.0.5`), so a lockfile refresh clears
those advisories. Keeping the input budget means a future parser regression
cannot reintroduce the same denial of service.
````

## Dependency-bump asks

These are separate, smaller PRs upstream. Ranges marked "in range" only need a
`bun.lock` refresh; the rest need a version range change.

| Package | Pinned | Fixed | Constraint | Action |
|---|---|---|---|---|
| `js-yaml` | 3.15.1 | 3.15.2 | `gray-matter@4.0.3`: `^3.13.1` | in range: `bun update js-yaml` |
| `brace-expansion` | 2.1.4 | 2.1.7 | `minimatch@8.0.7`: `^2.0.1` | in range: lockfile refresh |
| `brace-expansion` | 5.0.9 | 5.0.12 | `minimatch@10.2.5`: `^5.0.5` | in range: lockfile refresh |
| `seroval` | 1.5.6 | 1.6.3 | `solid-js@1.9.15`: `~1.5.4` | needs a `solid-js` release |
| `undici` | 6.28.0 | 6.29.1 | `node-gyp@12.4.0`: `^6.25.0` | in range: lockfile refresh (install-time only) |
| `undici` | 8.11.2 | 8.12.2 | `@effect/platform-node@4.0.1`: `^8.11.2` | in range: lockfile refresh (npm copy unused under Bun) |
| `zod` | 3.25.76 | 4.6.6 | `gitlab-ai-provider@6.19.0`: `^3.25.76` | out of the provider's range |
| `zod` | 4.1.8 / 4.4.3 | 4.6.6 | workspace `catalog:`, `@modelcontextprotocol/client@2.3.1`: `^4.2.0` | in range: catalog + lockfile refresh |
| `http-cache-semantics` | 4.2.0 | none | `@npmcli/arborist` (plugin install) | wait for upstream |

The first three rows remove five of the fourteen gated advisories in the Termux
gate without any code change. The remaining rows are tracked in
`security/osv-baseline.json` with an expiry of `2027-01-31`; see
`security/README.md` for the policy.

## Why not pin dependencies in the Termux build

The native build installs with `--frozen-lockfile` against the pinned upstream
commit. Adding a `bun.lock` override or a post-install `node_modules` patch
would replace the reviewed dependency graph with a live resolution, so the
guard is applied to source instead. The same reasoning is documented at the top
of `tools/patch-opencode-config-guards.py`.

## Maintenance

The patcher requires each anchor to match exactly once. If upstream refactors
either call site, the build fails with a drift message instead of silently
shipping unguarded code. After changing a guard:

```sh
python3 tools/patch-opencode-config-guards.py --selftest
python3 tools/patch-opencode-config-guards.py /path/to/opencode-checkout \
  --export-patches patches/opencode
git -C /path/to/opencode-checkout apply --check \
  "$PWD"/patches/opencode/*.patch
```

Then update this document and resubmit.
