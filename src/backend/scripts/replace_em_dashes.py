"""Vervang em-dash en en-dash in bronbestanden door komma's of gewone koppeltekens."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXTENSIONS = {".py", ".ts", ".tsx", ".yaml", ".yml", ".md", ".css", ".json"}
SKIP_DIRS = {"node_modules", ".venv", "__pycache__", "dist", ".git", ".pytest_cache"}


def replace_dashes(text: str) -> str:
    # Bereiken: 3-7, jan-mrt, De Paul-Enzo
    text = re.sub(r"(\w)\u2013(\w)", r"\1-\2", text)
    # Em-dash
    text = text.replace("\u2014", ", ")
    # En-dash met spaties (wedstrijdtitels)
    text = text.replace(" \u2013 ", " - ")
    text = text.replace("\u2013", "-")
    text = re.sub(r",\s*,", ", ", text)
    text = re.sub(r"\s+,", ",", text)
    return text


def main() -> int:
    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in EXTENSIONS:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if "\u2014" not in text and "\u2013" not in text:
            continue
        new = replace_dashes(text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1
            print(path.relative_to(ROOT))
    print(f"Updated {changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
