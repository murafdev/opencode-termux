# Upstream OpenCode config-guard patches

These files are **generated artifacts** for proposing the config-parsing guards
to upstream OpenCode. They are not applied by the Termux build; the build runs
`tools/patch-opencode-config-guards.py` directly (see
`docs/upstream-opencode-guards.md`).

Generated from `github.com/anomalyco/opencode` at commit
`68bc26b7da1990ce10ffecfbc1e09eb13aa5d824` (OpenCode 2.1.4).

| Patch | Target | Advisory |
|---|---|---|
| `opencode-frontmatter-budget.patch` | `packages/core/src/config/markdown.ts` | GHSA-2883-xcg3-v3hh / CVE-2026-84375 |
| `opencode-instruction-budget.patch` | `packages/core/src/config/plugin/instruction.ts` | GHSA-6j4f-fj2g-mc7p / CVE-2026-102276, GHSA-q2hr-2g5m-vwhr / CVE-2026-102277, GHSA-qhr7-859c-m2p7 / CVE-2026-102278 |

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
  "$PWD/patches/opencode/opencode-instruction-budget.patch"
```

Both patches are context-limited to the call sites they change, so they apply
independently. Do not hand-edit them: change the patcher and regenerate.

## Status

Prepared for upstream submission; not yet filed. The PR description, threat
model, and dependency-bump asks live in `docs/upstream-opencode-guards.md`.
