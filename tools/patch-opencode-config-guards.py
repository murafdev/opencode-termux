#!/usr/bin/env python3
"""Bound workspace-controlled config parsing in the pinned OpenCode source.

Two upstream code paths let a cloned repository burn CPU during startup:

  * gray-matter -> js-yaml parses ``---`` frontmatter from project agent,
    command, and skill markdown. Repeated ``<<`` merge keys amplify CPU use
    (CVE-2026-84375).
  * the ``instructions`` glob list reaches minimatch -> brace-expansion, whose
    recursive and quadratic expansion can exhaust the stack
    (CVE-2026-102276 / CVE-2026-102277 / CVE-2026-102278).

Both are bounded at the call site instead of by rewriting ``bun.lock``: the
build installs with ``--frozen-lockfile``, so an override would replace the
pinned dependency graph with a live resolution. The limits below are far above
anything a real config uses, so normal projects are unaffected.

Every anchor must match exactly once. An upstream refactor therefore fails the
build instead of silently dropping the guard. Re-running is a no-op.
"""

import argparse
import difflib
import shutil
import subprocess
import tempfile
from pathlib import Path

FRONTMATTER_REGION = """// #region opencode-termux:frontmatter-budget
// Project markdown frontmatter is attacker-controlled when a checkout is
// opened from an untrusted source. Cap the work handed to js-yaml: a very
// large block or many `<<` merge keys amplifies CPU use (CVE-2026-84375).
const MAX_FRONTMATTER_CHARS = 64 * 1024
const MAX_MERGE_KEYS = 32

function frontmatterBudget(content: string): void {
  const block = content.match(/^---\\r?\\n([\\s\\S]*?)\\r?\\n---/)
  if (!block) return
  const frontmatter = block[1] ?? ""
  if (frontmatter.length > MAX_FRONTMATTER_CHARS)
    throw new Error(`frontmatter exceeds ${MAX_FRONTMATTER_CHARS} characters`)
  const merges = frontmatter.match(/^\\s*(?:-\\s*)?<<\\s*:/gm)
  if (merges && merges.length > MAX_MERGE_KEYS)
    throw new Error(`frontmatter exceeds ${MAX_MERGE_KEYS} merge keys`)
}
// #endregion opencode-termux:frontmatter-budget
"""

INSTRUCTION_REGION = """// #region opencode-termux:instruction-budget
// Instruction globs come from project config. Without a budget, brace
// expansion can recurse without bound or produce a combinatorial number of
// alternatives during startup (CVE-2026-102276 / 102277 / 102278).
const INSTRUCTION_PATTERN_LIMIT = 1024
const INSTRUCTION_DEPTH_LIMIT = 8
const INSTRUCTION_GROUP_LIMIT = 32
const INSTRUCTION_COMMA_LIMIT = 32
const INSTRUCTION_EXPANSION_LIMIT = 256
const INSTRUCTION_RANGE_LIMIT = 4096

function unsafeInstructionPattern(pattern: string): boolean {
  if (pattern.length > INSTRUCTION_PATTERN_LIMIT) return true
  // `{1..1000000}` is short but expands to a million entries.
  for (const range of pattern.match(/\\{(-?\\d+)\\.\\.(-?\\d+)(?:\\.\\.(-?\\d+))?\\}/g) ?? []) {
    const parts = range.match(/\\{(-?\\d+)\\.\\.(-?\\d+)(?:\\.\\.(-?\\d+))?\\}/)
    if (!parts) continue
    const span = Math.abs(Number(parts[2]) - Number(parts[1]))
    const stride = Math.abs(Number(parts[3])) || 1
    if (span / stride > INSTRUCTION_RANGE_LIMIT) return true
  }
  let depth = 0
  let groups = 0
  let commas = 0
  let expansions = 1
  let alternatives = 1
  for (const char of pattern) {
    if (char === "{") {
      depth += 1
      groups += 1
      if (depth > INSTRUCTION_DEPTH_LIMIT || groups > INSTRUCTION_GROUP_LIMIT) return true
      alternatives = 1
    } else if (char === ",") {
      commas += 1
      if (commas > INSTRUCTION_COMMA_LIMIT) return true
      if (depth > 0) alternatives += 1
    } else if (char === "}") {
      // A stray or unclosed brace is literal for minimatch; only count groups.
      if (depth === 0) continue
      depth -= 1
      expansions *= alternatives
      if (expansions > INSTRUCTION_EXPANSION_LIMIT) return true
      alternatives = 1
    }
  }
  return false
}
// #endregion opencode-termux:instruction-budget
"""

MARKDOWN_ANCHOR = "export function parse(content: string) {\n  // Passing options bypasses"

MARKDOWN_REPLACEMENT = (
    FRONTMATTER_REGION
    + "\nexport function parse(content: string) {\n  frontmatterBudget(content)\n  // Passing options bypasses"
)

INSTRUCTION_HELPER_ANCHOR = (
    'export const Plugin = define({\n  id: "opencode.config.instruction",'
)

INSTRUCTION_HELPER_REPLACEMENT = INSTRUCTION_REGION + "\n" + INSTRUCTION_HELPER_ANCHOR

INSTRUCTION_CALL_ANCHOR = (
    '        const expanded = source.startsWith("~/") ? path.join(global.home, source.slice(2)) : source\n'
    '        const options = { absolute: true, include: "file", dot: true } as const\n'
)

INSTRUCTION_CALL_REPLACEMENT = (
    INSTRUCTION_CALL_ANCHOR
    + "        // opencode-termux:instruction-budget-call\n"
    + "        if (unsafeInstructionPattern(path.isAbsolute(expanded) ? path.basename(expanded) : expanded)) {\n"
    + '          yield* Effect.logDebug("instruction pattern skipped", {\n'
    + "            pattern: source.slice(0, 64),\n"
    + "            length: source.length,\n"
    + '            reason: "expansion-budget",\n'
    + "          })\n"
    + "          return []\n"
    + "        }\n"
)

STEPS = (
    (
        "packages/core/src/config/markdown.ts",
        "opencode-termux:frontmatter-budget",
        MARKDOWN_ANCHOR,
        MARKDOWN_REPLACEMENT,
    ),
    (
        "packages/core/src/config/plugin/instruction.ts",
        "opencode-termux:instruction-budget",
        INSTRUCTION_HELPER_ANCHOR,
        INSTRUCTION_HELPER_REPLACEMENT,
    ),
    (
        "packages/core/src/config/plugin/instruction.ts",
        "opencode-termux:instruction-budget-call",
        INSTRUCTION_CALL_ANCHOR,
        INSTRUCTION_CALL_REPLACEMENT,
    ),
)


def status(path: Path, marker: str, anchor: str) -> str:
    if not path.is_file():
        return "missing"
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return "applied"
    return "ready" if text.count(anchor) == 1 else "drift"


def apply_step(root: Path, path: str, marker: str, anchor: str, replacement: str) -> str:
    target = root / path
    state = status(target, marker, anchor)
    if state == "applied":
        return "skipped"
    if state == "drift":
        count = target.read_text(encoding="utf-8").count(anchor)
        raise SystemExit(
            f"config-guard drift in {path}: expected one anchor for {marker!r}, found {count}. "
            "Inspect the pinned upstream file before re-enabling the guard."
        )
    source = target.read_text(encoding="utf-8")
    # Pin LF: the build runs on Linux, and a CRLF checkout would make the
    # anchors (and the inserted code) differ from the pinned source.
    target.write_text(source.replace(anchor, replacement, 1), encoding="utf-8", newline="\n")
    return "applied"


def region(text: str, name: str) -> str:
    begin = f"// #region opencode-termux:{name}\n"
    end = f"// #endregion opencode-termux:{name}\n"
    return text[text.index(begin) + len(begin) : text.index(end)]


# Minimal trees that contain each anchor, so tests can exercise apply,
# idempotency, and drift detection without fetching upstream source.
FIXTURES = {
    "package.json": "{}\n",
    "packages/core/src/config/markdown.ts": (
        "export function parse(content: string) {\n"
        "  // Passing options bypasses\n"
        "  return undefined\n"
        "}\n"
    ),
    "packages/core/src/config/plugin/instruction.ts": (
        "export const Plugin = define({\n"
        '  id: "opencode.config.instruction",\n'
        "})\n"
        "\n"
        'const match = Effect.fn("ConfigInstructionPlugin.match")(function* (source: string) {\n'
        '        const expanded = source.startsWith("~/") ? path.join(global.home, source.slice(2)) : source\n'
        '        const options = { absolute: true, include: "file", dot: true } as const\n'
        "        return []\n"
        "})\n"
    ),
}


def write_fixtures(root: Path) -> None:
    for name, body in FIXTURES.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8", newline="\n")


PATCH_NAMES = {
    "packages/core/src/config/markdown.ts": "opencode-frontmatter-budget.patch",
    "packages/core/src/config/plugin/instruction.ts": "opencode-instruction-budget.patch",
}


def export_patches(root: Path, out_dir: Path) -> None:
    """Write upstream-ready unified diffs without modifying the checkout."""
    working = {}
    for path, marker, anchor, replacement in STEPS:
        target = root / path
        if not target.is_file():
            raise SystemExit(f"missing upstream file: {path}")
        if path not in working:
            working[path] = target.read_text(encoding="utf-8")
        text = working[path]
        if marker in text:
            raise SystemExit(f"{path} already contains {marker}; export from an unpatched checkout")
        count = text.count(anchor)
        if count != 1:
            raise SystemExit(
                f"config-guard drift in {path}: expected one anchor for {marker!r}, found {count}"
            )
        working[path] = text.replace(anchor, replacement, 1)

    out_dir.mkdir(parents=True, exist_ok=True)
    for path, updated in working.items():
        original = (root / path).read_text(encoding="utf-8")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
        destination = out_dir / PATCH_NAMES[path]
        destination.write_text("".join(diff), encoding="utf-8", newline="\n")
        print(f"wrote {destination}")


SELFTEST_JS = """import { frontmatterBudget } from "./frontmatter.mts"
import { unsafeInstructionPattern } from "./glob.mts"

let failed = 0
function fail(label, detail) {
  failed += 1
  console.error(`FAIL ${label}: ${detail}`)
}
// frontmatterBudget signals rejection by throwing; the glob guard returns true.
function frontmatterPasses(label, input) {
  try {
    frontmatterBudget(input)
  } catch {
    fail(label, "unexpected rejection")
  }
}
function frontmatterRejects(label, input) {
  try {
    frontmatterBudget(input)
    fail(label, "expected rejection")
  } catch {}
}
function globAllowed(label, input) {
  if (unsafeInstructionPattern(input) !== false) fail(label, "expected a usable pattern")
}
function globRejected(label, input) {
  if (unsafeInstructionPattern(input) !== true) fail(label, "expected a rejected pattern")
}

const merges = (n) => "---\\n" + "<<: {}\\n".repeat(n) + "---\\nbody\\n"

frontmatterPasses("normal frontmatter", "---\\ntitle: x\\n<<: {a: 1}\\n---\\nbody")
frontmatterPasses("no frontmatter", "just a body with << inside")
frontmatterPasses("merge key outside frontmatter", "---\\ntitle: x\\n---\\n<<: {}\\n")
frontmatterPasses("32 merge keys", merges(32))
frontmatterRejects("33 merge keys", merges(33))
frontmatterPasses("frontmatter at the size limit", "---\\n" + "x".repeat(65536) + "\\n---\\n")
frontmatterRejects("oversized frontmatter", "---\\n" + "x".repeat(65537) + "\\n---\\n")

globAllowed("simple glob", "**/*.{ts,tsx}")
globAllowed("nested directories", "**/{src,test}/**/*.{ts,tsx,md}")
globAllowed("absolute path", "/home/user/notes.md")
globAllowed("stray close brace", "foo}.md")
globAllowed("unclosed brace", "{unclosed")
globRejected("group explosion", "{a,b}".repeat(16))
globRejected("deep nesting", "{".repeat(40) + "a" + "}".repeat(40))
globRejected("long pattern", "a".repeat(1025))
globRejected("comma flood", "{a},b}".repeat(40))
globAllowed("small numeric range", "logs/app-{1..12}.log")
globAllowed("padded numeric range", "chapter-{01..12}.md")
globAllowed("bounded year range", "**/{2020..2026}/**/*.md")
globRejected("huge numeric range", "logs/app-{1..1000000}.log")
globRejected("huge stepped range", "logs/app-{1..1000000000..1}.log")
globRejected("descending range", "logs/app-{1000000..1..-1}.log")

if (failed > 0) {
  console.error(`${failed} guard self-test failure(s)`)
  process.exit(1)
}
console.log("config-guard self-test: ok")
"""


def selftest() -> None:
    node = shutil.which("node")
    if not node:
        raise SystemExit("config-guard self-test requires node on PATH")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        frontmatter = region(FRONTMATTER_REGION, "frontmatter-budget")
        instruction = region(INSTRUCTION_REGION, "instruction-budget")
        (work / "frontmatter.mts").write_text(
            frontmatter + "\nexport { frontmatterBudget }\n", encoding="utf-8"
        )
        (work / "glob.mts").write_text(
            instruction + "\nexport { unsafeInstructionPattern }\n", encoding="utf-8"
        )
        (work / "selftest.mjs").write_text(SELFTEST_JS, encoding="utf-8")
        subprocess.run(
            [node, "--experimental-strip-types", str(work / "selftest.mjs")],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_root", nargs="?", help="checkout of the pinned OpenCode source")
    parser.add_argument("--check", action="store_true", help="report guard status without writing")
    parser.add_argument("--selftest", action="store_true", help="exercise the inserted guards with node")
    parser.add_argument(
        "--write-fixtures",
        metavar="DIR",
        help="write a minimal anchor tree for the unit tests, then exit",
    )
    parser.add_argument(
        "--export-patches",
        metavar="DIR",
        help="write upstream-ready unified diffs for an unpatched checkout, then exit",
    )
    args = parser.parse_args()

    if args.check and args.export_patches:
        parser.error("--check and --export-patches are mutually exclusive")

    if args.selftest:
        selftest()
        return

    if args.write_fixtures:
        write_fixtures(Path(args.write_fixtures))
        return

    if not args.source_root:
        parser.error("source_root is required unless --selftest or --write-fixtures are used")

    root = Path(args.source_root)
    if not (root / "package.json").is_file():
        raise SystemExit(f"not an OpenCode checkout: {root}")

    if args.export_patches:
        export_patches(root, Path(args.export_patches))
        return

    if args.check:
        drifted = False
        for path, marker, anchor, _ in STEPS:
            state = status(root / path, marker, anchor)
            print(f"{state:8} {path} [{marker}]")
            drifted = drifted or state in ("drift", "missing")
        if drifted:
            raise SystemExit("config-guard check failed")
        return

    for path, marker, anchor, replacement in STEPS:
        print(f"{apply_step(root, path, marker, anchor, replacement):8} {path} [{marker}]")


if __name__ == "__main__":
    main()
