"""Inventory the pinned Fourier proof's repository-local import closure."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

PIN = "3344da59991ed94f9ba711217b29c1d760badfa6"
SOLUTION = "OAI.LinearAlgebra.FiniteFourier.Main"
CHALLENGE = "ComparatorChallenges.ExactFourier"
IMPORT = re.compile(r"(?m)^[ \t]*(?:(?:public|private|meta|all) )*import +([^\n]+)")
MARKER = re.compile(r"\b(?:sorryAx|sorry|admit)\b|(?m:^[ \t]*(?:private )?axiom[ \t]+\S+)")
TOKEN = re.compile(r'/-|-/|--|"(?:\\.|[^"\\])*"|\n', re.DOTALL)


def code_only(source):
    """Mask Lean comments and string literals while preserving line numbers."""
    result = list(source)
    block_depth = 0
    cursor = 0
    while match := TOKEN.search(source, cursor):
        token = match.group()
        lo, hi = match.span()
        if token == "/-" and not block_depth:
            comment_start = lo
        if token == "/-":
            block_depth += 1
        elif block_depth and token == "-/":
            block_depth -= 1
            if not block_depth:
                result[comment_start:hi] = mask(source[comment_start:hi])
        elif not block_depth and token == "--":
            newline = source.find("\n", hi)
            hi = len(source) if newline < 0 else newline
            result[lo:hi] = " " * (hi - lo)
        elif token.startswith('"'):
            if block_depth:
                # A quotation in a comment does not shield comment delimiters.
                hi = lo + 1
            else:
                result[lo:hi] = mask(source[lo:hi])
        cursor = hi
    if block_depth:
        raise ValueError("unterminated Lean block comment")
    return "".join(result)


def mask(text):
    return "".join("\n" if char == "\n" else " " for char in text)


def audit(root):
    def git(*args):
        return subprocess.check_output(("git", "-C", str(root), *args), text=True)

    commit = git("rev-parse", "HEAD").strip()
    if commit != PIN:
        raise ValueError(f"expected upstream commit {PIN}, got {commit}")
    if git("diff", "--name-only", "HEAD", "--", "lean"):
        raise ValueError("the upstream Lean sources or lock files have tracked changes")
    tracked = set(git("ls-files", "--", "lean").splitlines())
    lean = root / "lean"
    manifest = json.loads((lean / "lake-manifest.json").read_text(encoding="utf-8"))
    pending = [SOLUTION]
    local, external, markers = {}, Counter(), {}

    def inspect(path):
        source = code_only((root / path).read_text(encoding="utf-8"))
        imports = [module for match in IMPORT.finditer(source) for module in match[1].split()]
        hits = [
            {"line": source.count("\n", 0, match.start()) + 1, "token": match[0].strip()}
            for match in MARKER.finditer(source)
        ]
        return imports, hits

    while pending:
        module = pending.pop()
        if module in local:
            continue
        path = f"lean/{module.replace('.', '/')}.lean"
        if path not in tracked:
            if module.startswith("OAI."):
                raise ValueError(f"missing tracked source for {module}")
            external[module] += 1
            continue
        imports, hits = inspect(path)
        local[module] = imports
        if hits:
            markers[module] = hits
        pending.extend(imports)
    _, challenge_markers = inspect(f"lean/{CHALLENGE.replace('.', '/')}.lean")
    return {
        "upstream_commit": commit,
        "toolchain": (lean / "lean-toolchain").read_text(encoding="utf-8").strip(),
        "locked_packages": len(manifest["packages"]),
        "mathlib_revision": next(p["rev"] for p in manifest["packages"] if p["name"] == "mathlib"),
        "solution_module": SOLUTION,
        "solution_local_module_count": len(local),
        "solution_direct_imports": local[SOLUTION],
        "solution_local_modules_by_namespace": dict(sorted(Counter(
            ".".join(module.split(".")[:2]) for module in local
        ).items())),
        "external_module_count": len(external),
        "external_modules_by_namespace": dict(sorted(Counter(
            module.split(".")[0] for module in external
        ).items())),
        "solution_local_source_token_hits": dict(sorted(markers.items())),
        "challenge_module": CHALLENGE,
        "challenge_source_markers": challenge_markers,
        "scope": "Lexical source inventory. Token hits can be identifiers. External modules and declaration-level axioms require a separate Lean audit.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("openai_math", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.openai_math), indent=2))
