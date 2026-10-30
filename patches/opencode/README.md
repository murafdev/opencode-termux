# Upstream OpenCode config-guard patches

These files are **generated artifacts** for proposing the config guards
to upstream OpenCode. They are not applied by the Termux build; the build runs
`tools/patch-opencode-config-guards.py` directly (see
`docs/upstream-opencode-guards.md`).

Generated from `github.com/anomalyco/opencode` at commit
`098aa7fd6e02b03d6fc410f0b052038c7d4c5e81` (OpenCode 2.2.2). The anchors are
unchanged from `1097e2668b1e08ad63bdf0b1c4860b9bc01e420c` (2.2.0) and
`68bc26b7da1990ce10ffecfbc1e09eb13aa5d824` (2.1.4), so the same patcher covers
all three releases; these exported diffs target 2.2.2 and are byte-identical to
the 2.2.0 exports.

| Patch | Target | Advisory |
|---|---|---|
| `opencode-frontmatter-budget.patch` | `packages/core/src/config/markdown.ts` | GHSA-2883-xcg3-v3hh / CVE-2026-84375 |
| `opencode-instruction-budget.patch` | `packages/core/src/config/plugin/instruction.ts` | GHSA-6j4f-fj2g-mc7p / CVE-2026-102276, GHSA-q2hr-2g5m-vwhr / CVE-2026-102277, GHSA-qhr7-859c-m2p7 / CVE-2026-102278 |
| `opencode-config-normalize-guard.patch` | `packages/core/src/config.ts` | upstream #59684 (startup crash) |

## Regenerate

Always regenerate from the patcher so the patches and the build-time guards
cannot drift apart. Use an unpatched checkout of the pinned commit:

```sh
python3 tools/patch-opencode-config-guards.py /path/to/opencode-checkout \
  --export-patches patches/opencode
```

`--export-patches` refuses to run against a tree that already contains a guard,
and fails if an anchor no longer matches exactly once.

## Verify

```sh
git -C /path/to/opencode-checkout apply --check \
  "$PWD/patches/opencode/opencode-frontmatter-budget.patch" \
  "$PWD/patches/opencode/opencode-instruction-budget.patch" \
  "$PWD/patches/opencode/opencode-config-normalize-guard.patch"
```

All three patches are context-limited to the call sites they change, so they
apply independently. Do not hand-edit them: change the patcher and regenerate.

## Status

Prepared for upstream submission; not yet filed. The PR description, threat
model, and dependency-bump asks live in `docs/upstream-opencode-guards.md`.
