#!/usr/bin/env python3
"""Patch pinned OpenCode source for the verified Android/Bionic release.

The source is fetched at the commit recorded in the supply-chain lock before
this script runs. Each replacement must match exactly once so upstream changes
fail the build instead of silently dropping a safety patch.
"""

import json
import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"expected one build anchor in {path}, found {count}: {old!r}")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch-opencode-source-bun140.py SOURCE_ROOT")
    root = Path(sys.argv[1])
    package = root / "package.json"
    metadata = json.loads(package.read_text(encoding="utf-8"))
    if metadata.get("packageManager") != "bun@1.4.2":
        raise SystemExit(f"unexpected packageManager: {metadata.get('packageManager')!r}")
    replace_once(package, '"packageManager": "bun@1.4.2"', '"packageManager": "bun@1.4.0"')

    process = root / "packages/cli/src/util/process.ts"
    replace_once(
        process,
        'import path from "node:path"\n',
        'import { realpathSync } from "node:fs"\n'
        'import path from "node:path"\n',
    )
    replace_once(
        process,
        "export function selfCommand() {\n"
        '  const runtime = path.basename(process.execPath, path.extname(process.execPath)).toLowerCase()\n'
        '  if (runtime !== "bun" && runtime !== "node" && runtime !== "nodejs") return [process.execPath]\n'
        '  if (!entrypoint) throw new Error("Failed to resolve CLI entrypoint")\n'
        '  if (runtime === "node" || runtime === "nodejs") return [process.execPath, ...nodeFlags(), entrypoint]\n'
        "  return [process.execPath, entrypoint]\n"
        "}\n",
        "// Play Store Termux intercepts execve() and runs app-data ELFs through the bionic\n"
        "// linker (the Android 10+ W^X workaround). In that mode /proc/self/exe is the\n"
        "// linker while bionic shifts the arguments so argv[0] is the real binary.\n"
        "function bionicLinker(executable: string) {\n"
        "  const name = path.basename(executable).toLowerCase()\n"
        '  return name === "linker" || name === "linker64" || name === "ld-android.so"\n'
        "}\n"
        "\n"
        "export function selfExecutable() {\n"
        "  const executable = process.execPath\n"
        "  if (executable && !bionicLinker(executable)) return executable\n"
        "  const argv0 = process.argv[0]\n"
        "  if (!argv0 || bionicLinker(argv0)) return executable\n"
        "  const candidates = path.isAbsolute(argv0)\n"
        "    ? [argv0]\n"
        '    : (process.env.PATH ?? "").split(path.delimiter).map((directory) => path.resolve(directory || ".", argv0))\n'
        "  for (const candidate of candidates) {\n"
        "    try {\n"
        "      const resolved = realpathSync(candidate)\n"
        "      if (!bionicLinker(resolved)) return resolved\n"
        "    } catch {}\n"
        "  }\n"
        "  return executable\n"
        "}\n"
        "\n"
        "export function selfCommand() {\n"
        "  const executable = selfExecutable()\n"
        "  const runtime = path.basename(executable, path.extname(executable)).toLowerCase()\n"
        '  if (runtime !== "bun" && runtime !== "node" && runtime !== "nodejs") return spawnable([executable])\n'
        '  if (!entrypoint) throw new Error("Failed to resolve CLI entrypoint")\n'
        '  if (runtime === "node" || runtime === "nodejs") return spawnable([executable, ...nodeFlags(), entrypoint])\n'
        "  return spawnable([executable, entrypoint])\n"
        "}\n"
        "\n"
        "// Bun calls execve() from its spawn helper; on Play Store Termux a direct execve\n"
        "// of an app-data binary can be blocked. The system shell is always executable and\n"
        "// its libc execve() goes through termux-exec's linker rewrite.\n"
        "function spawnable(command: string[]) {\n"
        "  if (!bionicLinker(process.execPath)) return command\n"
        '  return ["/system/bin/sh", "-c", \'exec "$@"\', "sh", ...command]\n'
        "}\n",
    )

    build = root / "packages/cli/script/build.ts"
    replace_once(
        build,
        "async function compileExecutable(item: (typeof allTargets)[number]) {\n",
        "async function compileExecutable(item: (typeof allTargets)[number]) {\n"
        ' const pinned = process.env.BUN_SOURCE_TARGET_ELF\n'
        ' if (pinned) {\n'
        '   if (item.os !== "linux" || item.arch !== "arm64" || item.abi) throw new Error("unexpected source-build target")\n'
        '   if (!(await Bun.file(pinned).exists())) throw new Error("pinned Bun target missing")\n'
        '   return pinned\n'
        ' }\n',
    )

    upgrade = root / "packages/cli/src/commands/handlers/upgrade.ts"
    replace_once(
        upgrade,
        'import { stripVTControlCharacters } from "node:util"\n',
        'import { stripVTControlCharacters } from "node:util"\n'
        'import { Global } from "@opencode/util/global"\n'
        'import path from "node:path"\n'
        'import { selfExecutable } from "../../util/process"\n',
    )
    replace_once(
        upgrade,
        '      intro("Upgrade")\n      const updater = yield* Updater.Service\n',
        '      intro("Upgrade")\n'
        '      const global = yield* Global.Service\n'
        '      if (selfExecutable() === path.join(global.home, ".local", "bin", "opencode")) {\n'
        '        return yield* Effect.fail(new Error(\n'
        '          "This native Termux build must be upgraded with its verified release installer: " +\n'
        '          "curl -fsSL https://github.com/murafdev/opencode-termux/raw/v2.1.2/install.sh | sh"\n'
        '        ))\n'
        '      }\n'
        '      const updater = yield* Updater.Service\n',
    )

    uninstall = root / "packages/cli/src/commands/handlers/uninstall.ts"
    replace_once(
        uninstall,
        'import { errorMessage } from "../../util/error"\n',
        'import { errorMessage } from "../../util/error"\n'
        'import { selfExecutable } from "../../util/process"\n',
    )
    replace_once(
        uninstall,
        '    const method = yield* updater.method()\n',
        '    const executable = selfExecutable()\n'
        '    const nativeBinary = executable === path.join(global.home, ".local", "bin", "opencode")\n'
        '    const method = yield* updater.method()\n',
    )
    replace_once(
        uninstall,
        '    if (removal) log.info(`  Package: ${removal.command.join(" ")}`)\n'
        '    if (method === "curl") log.info(`  Binary (manual removal): ${process.execPath}`)\n'
        '    if (!method) log.warn("Could not detect the installation method. Remove the installation manually after cleanup.")\n',
        '    if (removal) log.info(`  Package: ${removal.command.join(" ")}`)\n'
        '    if (nativeBinary) log.info(`  Binary: ${executable}`)\n'
        '    else if (method === "curl") log.info(`  Binary (manual removal): ${executable}`)\n'
        '    if (!method && !nativeBinary) log.warn("Could not detect the installation method. Remove the installation manually after cleanup.")\n',
    )
    replace_once(
        uninstall,
        '    if (method === "curl") {\n      log.message("To finish removing the binary, run:")\n',
        '    if (nativeBinary) {\n'
        '      yield* fs.remove(executable).pipe(\n'
        '        Effect.catch((error) => Effect.sync(() => errors.push(`Binary: ${errorMessage(error)}`))),\n'
        '      )\n'
        '    }\n'
        '    if (method === "curl") {\n      log.message("To finish removing the binary, run:")\n',
    )


if __name__ == "__main__":
    main()
