"""Per groepsduel: beide teamdossiers naast elkaar → context-factoren."""

from __future__ import annotations

import re

from app.data.teams.context_scoring_schema import ContextFactor
from app.data.teams.team_bundle import TeamBundle
from app.display_text import clip_research_excerpt, humanize_factor_reason
from app.teams import fifa_team_key

_STYLE_NEEDLES: dict[str, tuple[str, ...]] = {
    "press": ("press", "pressing", "hoog druk", "high press", "moriyasu"),
    "possession": ("possession", "balbezit", "tik-tak", "dominant possession", "controle"),
    "counter": ("counter", "omschakeling", "transitie", "transition", "transitions"),
    "compact": ("compact", "blok", "low block", "mid-block", "gesloten"),
    "physical": ("fysiek", "duel", "kracht", "atletiek", "intens"),
    "aerial": ("lucht", "hoogte", "standaard"),
}


def _mentions_opponent(line: str, opponent_nl: str, opponent_fifa: str) -> bool:
    low = line.lower()
    return opponent_nl.lower() in low or opponent_fifa.lower() in low


def _is_self_weakness_note(line: str) -> bool:
    """Eigen zwakte in het dossier van de tegenstander, geen exploiteerbare fout voor ons."""
    t = line.strip()
    if re.match(r"^\s*zwakwer\b", t, flags=re.I):
        return True
    if re.match(r"^\s*zwakker\s+vs\b", t, flags=re.I):
        return True
    return False


def _style_tags(*chunks: str) -> set[str]:
    blob = " ".join(c for c in chunks if c).lower()
    return {tag for tag, needles in _STYLE_NEEDLES.items() if any(n in blob for n in needles)}


def _fixture_vs(bundle: TeamBundle, opponent_fifa: str):
    for fx in bundle.group_stage.fixtures:
        if fx.opponent_fifa == opponent_fifa:
            return fx
    return None


def _opener_opponent_fifa(bundle: TeamBundle) -> str | None:
    if not bundle.group_stage.fixtures:
        return None
    return min(bundle.group_stage.fixtures, key=lambda f: f.match_number).opponent_fifa


def _spark_is_opener_altitude(notes: str) -> bool:
    low = notes.lower()
    return any(w in low for w in ("opener", "2240", "hoogte", "azteca", "acclimatisatie"))


def build_pairwise_factors(self: TeamBundle, opponent: TeamBundle) -> list[ContextFactor]:
    """Factoren voor `self` in duel tegen `opponent` (uit volledige research-YAML)."""
    opp_nl = opponent.team_name_nl
    opp_fifa = opponent.fifa_team_key
    factors: list[ContextFactor] = []

    strong, weak = self.phase_preferences
    opp_strong, opp_weak = opponent.phase_preferences

    if _mentions_opponent(weak, opp_nl, opp_fifa):
        factors.append(
            ContextFactor(
                id="tactical_weakness",
                delta=-1,
                reason=humanize_factor_reason(
                    weak[:140],
                    factor_id="tactical_weakness",
                    subject_team=self.team_name_nl,
                    opponent_team=opp_nl,
                ),
            )
        )
    if _mentions_opponent(strong, opp_nl, opp_fifa):
        factors.append(
            ContextFactor(
                id="tactical_strength",
                delta=1,
                reason=humanize_factor_reason(
                    strong[:140],
                    factor_id="tactical_strength",
                    subject_team=self.team_name_nl,
                    opponent_team=opp_nl,
                ),
            )
        )
    # Geen dubbele bonus: 'Zwakwer …' op tegenstander = zij hebben moeite (al -1 aan hun kant).
    if (
        _mentions_opponent(opp_weak, self.team_name_nl, self.fifa_team_key)
        and not _is_self_weakness_note(opp_weak)
    ):
        factors.append(
            ContextFactor(
                id="opponent_profile_weak",
                delta=1,
                reason=humanize_factor_reason(
                    opp_weak[:140],
                    factor_id="opponent_profile_weak",
                    subject_team=self.team_name_nl,
                    opponent_team=opp_nl,
                ),
            )
        )
    if _mentions_opponent(opp_strong, self.team_name_nl, self.fifa_team_key):
        factors.append(
            ContextFactor(
                id="opponent_profile_strong",
                delta=-1,
                reason=humanize_factor_reason(
                    opp_strong[:140],
                    factor_id="opponent_profile_strong",
                    subject_team=self.team_name_nl,
                    opponent_team=opp_nl,
                ),
            )
        )

    self_style = _style_tags(
        self.macro_style,
        self.transition_orientation_summary,
        strong,
        weak,
        " ".join(self.strengths),
    )
    opp_style = _style_tags(
        opponent.macro_style,
        opponent.transition_orientation_summary,
        opp_strong,
        opp_weak,
        " ".join(opponent.strengths),
    )

    if "counter" in self_style and "compact" in opp_style:
        factors.append(
            ContextFactor(
                id="style_matchup",
                delta=1,
                reason=f"Omschakeling/transities passen tegen compact {opp_nl}",
            )
        )
    if "counter" in opp_style and ("possession" in self_style or self.power_score - opponent.power_score >= 8):
        factors.append(
            ContextFactor(
                id="style_matchup",
                delta=-1,
                reason=f"Compacte counters van {opp_nl} tegen ons aanvalsspel",
            )
        )
    if "press" in opp_style and ("possession" in self_style or "controle" in self.macro_style.lower()):
        factors.append(
            ContextFactor(
                id="style_matchup",
                delta=-1,
                reason=f"Hoge press van {opp_nl} verstoort opbouw",
            )
        )
    if "press" in self_style and "compact" in opp_style:
        factors.append(
            ContextFactor(
                id="style_matchup",
                delta=1,
                reason=f"Eigen press kan compact blok {opp_nl} onder druk zetten",
            )
        )
    if "aerial" in self_style and "physical" not in opp_style:
        factors.append(
            ContextFactor(
                id="style_matchup",
                delta=1,
                reason=humanize_factor_reason(
                    f"Lucht/standaardprofiel t.o.v. {opp_nl}",
                    factor_id="style_matchup",
                    subject_team=self.team_name_nl,
                    opponent_team=opp_nl,
                ),
            )
        )

    for line in self.psychology_vectors:
        if _mentions_opponent(line, opp_nl, opp_fifa):
            low = line.lower()
            delta = -1 if any(w in low for w in ("moet winnen", "druk", "zonder", "uit", "kwets")) else 0
            factors.append(
                ContextFactor(
                    id="psychology", delta=delta, reason=clip_research_excerpt(line)
                )
            )

    if _mentions_opponent(self.interpretive_ceiling_vs_floor, opp_nl, opp_fifa):
        low = self.interpretive_ceiling_vs_floor.lower()
        delta = -1 if "underdog" in low else 0
        factors.append(
            ContextFactor(
                id="fixture_narrative",
                delta=delta,
                reason=clip_research_excerpt(self.interpretive_ceiling_vs_floor),
            )
        )

    fx = _fixture_vs(self, opp_fifa)
    if fx and fx.is_home and self.cohost_status:
        factors.append(
            ContextFactor(
                id="home_fixture",
                delta=1,
                reason=f"Thuis in {fx.stadium} (co-host)",
            )
        )
    elif fx and not fx.is_home and opponent.cohost_status:
        factors.append(
            ContextFactor(
                id="away_fixture",
                delta=-1,
                reason=f"Uit tegen co-host {opp_nl} ({fx.stadium})",
            )
        )

    # Opener / hoogte alleen op de echte openingswedstrijd (niet in persistent dupliceren)
    opener_opp = _opener_opponent_fifa(self)
    if (
        fx
        and opener_opp
        and fifa_team_key(opener_opp) == fifa_team_key(opp_fifa)
        and self.distinctive_spark_notes
        and _spark_is_opener_altitude(self.distinctive_spark_notes)
    ):
        low = self.distinctive_spark_notes.lower()
        factors.append(
            ContextFactor(
                id="opener_context",
                delta=-1 if "zonder acclimatisatie" in low or "test" in low else 0,
                reason=clip_research_excerpt(self.distinctive_spark_notes),
            )
        )

    return factors
