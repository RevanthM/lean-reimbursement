#!/usr/bin/env python3
"""Reject proof holes and trust-expanding declarations in authored Lean files."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
files = sorted(p for p in root.rglob("*.lean") if ".lake" not in p.parts)
for path in files:
    text = path.read_text()
    forbidden = re.findall(r"\b(?:sorry|admit|axiom|unsafe)\b", text)
    if forbidden:
        raise SystemExit(f"Forbidden proof/trust declaration in {path.relative_to(root)}: {forbidden}")
count = sum(len(re.findall(r"^theorem ", p.read_text(), re.M)) for p in files)
print(f"Checked {len(files)} authored Lean files; {count} named theorems; no proof holes or custom axioms.")
