"""Controleer of factor-delta en reason-tekst hetzelfde teken hebben (per team in versus)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _audit_bootstrap as _audit_bootstrap  # noqa: E402

_audit_bootstrap.configure_audit_stdio()

import yaml

ROOT = Path(__file__).resolve().parents[1] / "app" / "data" / "teams" / "research"

_POSITIVE_FOR_TEAM = re.compile(
    r"\b(profiteert|profiteren|voordeel|sterker|beter|gunstig|wint hier|domineert|"
    r"benutten|inspelen|favoriet|openbreken|toslaan|vindt ruimte)\b",
    re.I,
)
_NEGATIVE_FOR_TEAM = re.compile(
    r"\b(lastig|dreiging|risico|kwetsbaar|onder druk|zwaar|lastiger|verstoort)\b",
    re.I,
)


def _load_versus() -> list[tuple[str, str, dict]]:
    rows: list[tuple[str, str, dict]] = []
    for path in sorted(ROOT.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        team = str(data.get("team_id") or path.stem)
        versus = (data.get("context_scoring") or {}).get("versus") or {}
        for opp, factors in versus.items():
            if not isinstance(factors, list):
                continue
            for factor in factors:
                if isinstance(factor, dict):
                    rows.append((team, str(opp), factor))
    return rows


def _mismatch(team: str, opp: str, factor: dict) -> str | None:
    delta = int(factor.get("delta") or 0)
    if delta == 0:
        return None
    reason = str(factor.get("reason") or "").strip()
    if not reason:
        return None
    fid = str(factor.get("id") or "")
    pos = bool(_POSITIVE_FOR_TEAM.search(reason))
    neg = bool(_NEGATIVE_FOR_TEAM.search(reason))
    if delta > 0 and pos and not neg:
        return None
    if delta < 0 and neg and not pos:
        return None
    if delta > 0 and "profiteert" in reason.lower():
        return None
    if delta < 0 and "profiteert" in reason.lower():
        return (
            f"{team} vs {opp} [{fid}] delta={delta:+d}: "
            f"negatieve score maar positieve tekst, {reason[:100]}"
        )
    if delta > 0 and neg and not pos:
        return (
            f"{team} vs {opp} [{fid}] delta={delta:+d}: "
            f"positieve score maar dreigingstekst, {reason[:100]}"
        )
    return None


def main() -> int:
    mismatches = [
        m
        for team, opp, factor in _load_versus()
        if (m := _mismatch(team, opp, factor))
    ]
    if mismatches:
        print(f"Sign mismatches ({len(mismatches)}):\n")
        for line in mismatches[:80]:
            print(f"  {line}")
        if len(mismatches) > 80:
            print(f"  ... en {len(mismatches) - 80} meer")
        return 1
    print("OK: geen duidelijke teken-tegenstrijdigheden in versus-factoren.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
