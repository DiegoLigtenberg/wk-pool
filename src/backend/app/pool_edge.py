"""Pool-edge: uitlegbare bijsturing op wedstrijdscore voor pick, kansen en uitslag."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.data.teams.team_loader import get_team_bundle
from app.data.teams.tournament_context_loader import head_to_head_vs
from app.data.teams.tournament_context_schema import MomentumLabel, PlayedMatch
from app.data.teams.team_loader import get_team_bundle
from app.group_form import GroupFormStats
from app.knockout_form import KnockoutRoundStats
from app.teams import display_team_name

PickCode = Literal["1", "2", "3"]
AdjustmentKind = Literal["live_form", "momentum", "standings", "h2h", "upset", "knockout_form"]

_MOMENTUM_DELTA: dict[MomentumLabel, int] = {
    "rising": 2,
    "stable": 0,
    "falling": -2,
}

_POOL_DIFF_CAP = 6
_POOL_DIFF_CAP_KNOCKOUT = 9
# Poule vs papier: alleen grote verrassingen, lichte bijsturing (situatieafhankelijk).
_GROUP_EXPECTATION_SURPRISE_MIN = 3
_GROUP_EXPECTATION_DELTA = 1

_KO_UPSET_POWER_GAP_MIN = 6
_KO_UPSET_DELTA = 3
_KO_WIN_DELTA = 1
_KO_WIN_DELTA_MAX = 2
_KO_ATTACK_GOALS_MIN = 5
_KO_ATTACK_DELTA = 1
_KO_FAVORITE_TRIM_MIN_DIFF = 12
_KO_FAVORITE_TRIM_CAP = 7
_KO_DEFENSIVE_DRAW_DELTA = 2


def expected_group_points_from_power(power: int) -> int:
    """Ruwe verwachting poulepunten op basis van basissterkte (3 duels)."""
    if power >= 82:
        return 7
    if power >= 74:
        return 5
    if power >= 68:
        return 4
    return 2


@dataclass(frozen=True, slots=True)
class PickAdjustment:
    """`delta` > 0 = voordeel thuis op de pool-wedstrijdscore."""

    id: str
    kind: AdjustmentKind
    label: str
    delta: int
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "delta": self.delta,
            "reason": self.reason,
        }


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


def _factor_delta_sum(factors: list[dict[str, object]], factor_id: str) -> int:
    return sum(int(f["delta"]) for f in factors if str(f.get("id")) == factor_id)


def _played_form_delta(played: tuple[PlayedMatch, ...]) -> tuple[int, str | None]:
    if not played:
        return 0, None
    pts = sum(3 if m.result == "W" else 1 if m.result == "D" else 0 for m in played)
    if pts >= 6:
        delta = 2
    elif pts >= 4:
        delta = 1
    elif pts <= 1:
        delta = -1
    else:
        return 0, None
    summary = ", ".join(m.result or "?" for m in played[:3])
    return (
        delta,
        f"Gespeelde wedstrijden in YAML ({summary}) → {'+' if delta > 0 else ''}{delta} vorm.",
    )


def _momentum_yaml_delta(
    label: MomentumLabel | None, notes: str | None, team_nl: str
) -> tuple[int, str | None]:
    if not label:
        return 0, None
    delta = _MOMENTUM_DELTA[label]
    if delta == 0:
        return 0, None
    note = f": {notes.strip()}" if notes and notes.strip() else ""
    direction = {"rising": "oplopend", "falling": "afnemend"}[label]
    return (
        delta,
        f"{team_nl}: momentum {direction} in tornooi-YAML{note} → {'+' if delta > 0 else ''}{delta}.",
    )


def _standings_delta(points: int, played: int, team_nl: str) -> tuple[int, str | None]:
    if played < 2:
        return 0, None
    ppg = points / played
    if ppg >= 2.0:
        return 1, f"{team_nl}: {points} pt uit {played} wedstrijd(en) in stand → +1."
    if ppg < 0.75:
        return -1, f"{team_nl}: {points} pt uit {played} wedstrijd(en) in stand → −1."
    return 0, None


def _side_yaml_adjustments(team_fifa: str, *, is_home: bool) -> list[PickAdjustment]:
    bundle = get_team_bundle(team_fifa)
    phase = bundle.tournament_context.phases.get("group")
    if phase is None:
        return []

    team_nl = display_team_name(team_fifa)
    sign = 1 if is_home else -1
    out: list[PickAdjustment] = []

    played_delta, played_reason = _played_form_delta(phase.played_matches)
    if played_delta and played_reason:
        d = played_delta * sign
        out.append(
            PickAdjustment(
                id=f"{'home' if is_home else 'away'}_played_form",
                kind="momentum",
                label="Vorm (gespeeld)",
                delta=d,
                reason=played_reason.replace("→", f"→ {'thuis' if is_home else 'uit'}"),
            )
        )

    mom_delta, mom_reason = _momentum_yaml_delta(
        phase.momentum.label if phase.momentum else None,
        phase.momentum.notes if phase.momentum else None,
        team_nl,
    )
    if mom_delta and mom_reason:
        out.append(
            PickAdjustment(
                id=f"{'home' if is_home else 'away'}_momentum",
                kind="momentum",
                label="Momentum",
                delta=mom_delta * sign,
                reason=mom_reason,
            )
        )

    if phase.standings:
        st_delta, st_reason = _standings_delta(
            phase.standings.points, phase.standings.played, team_nl
        )
        if st_delta and st_reason:
            out.append(
                PickAdjustment(
                    id=f"{'home' if is_home else 'away'}_standings",
                    kind="standings",
                    label="Stand",
                    delta=st_delta * sign,
                    reason=st_reason,
                )
            )
    return out


def _h2h_adjustment(home_key: str, away_key: str) -> PickAdjustment | None:
    home_bundle = get_team_bundle(home_key)
    rec = head_to_head_vs(home_bundle.tournament_context, away_key)
    if rec is None or (rec.wins + rec.draws + rec.losses) == 0:
        return None
    net = rec.wins - rec.losses
    if net == 0:
        return None
    delta = _clamp(net, -2, 2)
    return PickAdjustment(
        id="head_to_head",
        kind="h2h",
        label="Onderlinge historie",
        delta=delta,
        reason=(
            f"H2H {display_team_name(home_key)}–{display_team_name(away_key)}: "
            f"{rec.wins}W-{rec.draws}G-{rec.losses}V → {'+' if delta > 0 else ''}{delta} thuis."
        ),
    )


def _upset_adjustment(
    *,
    home_key: str,
    away_key: str,
    home_power: int,
    away_power: int,
    home_factors: list[dict[str, object]],
    away_factors: list[dict[str, object]],
) -> PickAdjustment | None:
    gap = home_power - away_power
    if abs(gap) < 6:
        return None

    favorite_home = gap > 0
    fav_factors = home_factors if favorite_home else away_factors
    dog_factors = away_factors if favorite_home else home_factors
    fav_key = home_key if favorite_home else away_key
    dog_key = away_key if favorite_home else home_key

    dog_upset = _factor_delta_sum(dog_factors, "upset_path") > 0
    fav_choke = _factor_delta_sum(fav_factors, "choke_risk") < 0

    signal = 0
    if dog_upset:
        signal += 2
    if fav_choke:
        signal += 2
    if _factor_delta_sum(dog_factors, "matchup_edge") > 0:
        signal += 1
    if _factor_delta_sum(fav_factors, "matchup_risk") < 0:
        signal += 1
    if _factor_delta_sum(dog_factors, "tactical_strength") > 0:
        signal += 1
    if _factor_delta_sum(fav_factors, "tactical_weakness") < 0:
        signal += 1

    min_signal = 1 if (dog_upset or fav_choke) else 2
    if signal < min_signal:
        return None

    if dog_upset or fav_choke:
        shift = 4 if abs(gap) >= 10 else 3
    else:
        shift = 3 if abs(gap) >= 10 else 2
    delta = -shift if favorite_home else shift
    detail = []
    if dog_upset:
        detail.append("underdog-upsetpad")
    if fav_choke:
        detail.append("choke-risico favoriet")
    detail_txt = " + ".join(detail) if detail else "duel-onderdelen"
    return PickAdjustment(
        id="tactical_upset",
        kind="upset",
        label="Tactische upset",
        delta=delta,
        reason=(
            f"{display_team_name(dog_key)} countert {display_team_name(fav_key)} op papier "
            f"(basisverschil {abs(gap)}): {detail_txt} → "
            f"{'+' if delta > 0 else ''}{delta} richting underdog."
        ),
    )


def _points_from_played_matches(played: tuple[PlayedMatch, ...]) -> tuple[int, int]:
    pts = 0
    played_count = 0
    for m in played:
        if m.result is None:
            continue
        played_count += 1
        if m.result == "W":
            pts += 3
        elif m.result == "D":
            pts += 1
    return pts, played_count


def live_form_from_group_played_yaml(
    home_fifa: str, away_fifa: str,
) -> tuple[int, int, int, int] | None:
    """Groepsfase-uitslagen uit team-YAML (`played_matches`). Leeg vóór het WK."""
    home_phase = get_team_bundle(home_fifa).tournament_context.phases.get("group")
    away_phase = get_team_bundle(away_fifa).tournament_context.phases.get("group")
    home_played = home_phase.played_matches if home_phase else ()
    away_played = away_phase.played_matches if away_phase else ()
    hp, hpl = _points_from_played_matches(home_played)
    ap, apl = _points_from_played_matches(away_played)
    if hpl == 0 and apl == 0:
        return None
    return hp, hpl, ap, apl


def live_form_from_results(
  *,
    home_fifa: str,
    away_fifa: str,
    home_points: int,
    away_points: int,
    home_played: int,
    away_played: int,
) -> list[PickAdjustment]:
    """Vorm uit ingevulde groepsuitslagen (YAML), alleen voor knock-out na de groep."""
    out: list[PickAdjustment] = []
    if home_played > 0:
        hp_delta = 2 if home_points >= home_played * 2 else 1 if home_points >= home_played else -1 if home_points == 0 else 0
        if hp_delta:
            out.append(
                PickAdjustment(
                    id="home_live_form",
                    kind="live_form",
                    label="Live vorm thuis",
                    delta=hp_delta,
                    reason=(
                        f"{display_team_name(home_fifa)}: {home_points} pt uit {home_played} "
                        f"groepswedstrijd(en) in team-YAML → +{hp_delta} thuis."
                    ),
                )
            )
    if away_played > 0:
        ap_delta = 2 if away_points >= away_played * 2 else 1 if away_points >= away_played else -1 if away_points == 0 else 0
        if ap_delta:
            out.append(
                PickAdjustment(
                    id="away_live_form",
                    kind="live_form",
                    label="Live vorm uit",
                    delta=-ap_delta,
                    reason=(
                        f"{display_team_name(away_fifa)}: {away_points} pt uit {away_played} "
                        f"groepswedstrijd(en) in team-YAML → +{ap_delta} uit "
                        f"(−{ap_delta} op diff)."
                    ),
                )
            )
    return out


def group_momentum_adjustments(
    home: GroupFormStats | None,
    away: GroupFormStats | None,
) -> list[PickAdjustment]:
    """Poulefase: rang, punten, doelsaldo en goals als momentum na de groep."""
    if home is None or away is None or home.played == 0 or away.played == 0:
        return []

    out: list[PickAdjustment] = []

    rank_gap = away.rank - home.rank
    if rank_gap > 0:
        delta = 2 if rank_gap >= 2 else 1
        out.append(
            PickAdjustment(
                id="home_group_rank",
                kind="standings",
                label="Poulerang thuis",
                delta=delta,
                reason=(
                    f"{display_team_name(home.fifa_team)} eindigde #{home.rank} in groep {home.group}, "
                    f"{display_team_name(away.fifa_team)} #{away.rank} in groep {away.group} "
                    f"→ +{delta} thuis."
                ),
            )
        )
    elif rank_gap < 0:
        delta = 2 if rank_gap <= -2 else 1
        out.append(
            PickAdjustment(
                id="away_group_rank",
                kind="standings",
                label="Poulerang uit",
                delta=-delta,
                reason=(
                    f"{display_team_name(away.fifa_team)} eindigde #{away.rank} in groep {away.group}, "
                    f"{display_team_name(home.fifa_team)} #{home.rank} in groep {home.group} "
                    f"→ +{delta} uit (−{delta} op diff)."
                ),
            )
        )

    if home.wins >= 3:
        out.append(
            PickAdjustment(
                id="home_group_wins",
                kind="momentum",
                label="Poule-winstreeks thuis",
                delta=1,
                reason=f"{display_team_name(home.fifa_team)} won alle {home.wins} groepsduels → +1 thuis.",
            )
        )
    if away.wins >= 3:
        out.append(
            PickAdjustment(
                id="away_group_wins",
                kind="momentum",
                label="Poule-winstreeks uit",
                delta=-1,
                reason=(
                    f"{display_team_name(away.fifa_team)} won alle {away.wins} groepsduels "
                    f"→ +1 uit (−1 op diff)."
                ),
            )
        )

    if home.goal_difference >= 4:
        out.append(
            PickAdjustment(
                id="home_group_gd",
                kind="momentum",
                label="Sterk doelsaldo thuis",
                delta=1,
                reason=(
                    f"{display_team_name(home.fifa_team)} doelsaldo +{home.goal_difference} in de poule → +1 thuis."
                ),
            )
        )
    elif home.goal_difference <= -3:
        out.append(
            PickAdjustment(
                id="home_group_gd_weak",
                kind="momentum",
                label="Zwak doelsaldo thuis",
                delta=-1,
                reason=(
                    f"{display_team_name(home.fifa_team)} doelsaldo {home.goal_difference} in de poule → −1 thuis."
                ),
            )
        )

    if away.goal_difference >= 4:
        out.append(
            PickAdjustment(
                id="away_group_gd",
                kind="momentum",
                label="Sterk doelsaldo uit",
                delta=-1,
                reason=(
                    f"{display_team_name(away.fifa_team)} doelsaldo +{away.goal_difference} in de poule "
                    f"→ +1 uit (−1 op diff)."
                ),
            )
        )
    elif away.goal_difference <= -3:
        out.append(
            PickAdjustment(
                id="away_group_gd_weak",
                kind="momentum",
                label="Zwak doelsaldo uit",
                delta=1,
                reason=(
                    f"{display_team_name(away.fifa_team)} doelsaldo {away.goal_difference} in de poule "
                    f"→ +1 thuis."
                ),
            )
        )

    if home.goals_for >= 7:
        out.append(
            PickAdjustment(
                id="home_group_goals",
                kind="momentum",
                label="Aanvallende poule thuis",
                delta=1,
                reason=(
                    f"{display_team_name(home.fifa_team)} scoorde {home.goals_for}x in de poule → +1 thuis."
                ),
            )
        )
    if away.goals_for >= 7:
        out.append(
            PickAdjustment(
                id="away_group_goals",
                kind="momentum",
                label="Aanvallende poule uit",
                delta=-1,
                reason=(
                    f"{display_team_name(away.fifa_team)} scoorde {away.goals_for}x in de poule "
                    f"→ +1 uit (−1 op diff)."
                ),
            )
        )

    return out


def group_scoring_trend_adjustments(
    home: GroupFormStats | None,
    away: GroupFormStats | None,
) -> list[PickAdjustment]:
    """Doelpunten per wedstrijd en recente scorelijn uit de poule."""
    if home is None or away is None or home.played == 0 or away.played == 0:
        return []

    out: list[PickAdjustment] = []

    if home.scoring_trend > 0:
        out.append(
            PickAdjustment(
                id="home_scoring_trend",
                kind="momentum",
                label="Stijgende scorelijn thuis",
                delta=1,
                reason=(
                    f"{display_team_name(home.fifa_team)} scoorde in het laatste pouleduel sterker "
                    f"dan eerder (log {list(home.goal_log)}) → +1 thuis."
                ),
            )
        )
    elif home.scoring_trend < 0:
        out.append(
            PickAdjustment(
                id="home_scoring_trend_down",
                kind="momentum",
                label="Dalende scorelijn thuis",
                delta=-1,
                reason=(
                    f"{display_team_name(home.fifa_team)} scoorde minder in het laatste pouleduel "
                    f"→ −1 thuis."
                ),
            )
        )

    if away.scoring_trend > 0:
        out.append(
            PickAdjustment(
                id="away_scoring_trend",
                kind="momentum",
                label="Stijgende scorelijn uit",
                delta=-1,
                reason=(
                    f"{display_team_name(away.fifa_team)} scoorde in het laatste pouleduel sterker "
                    f"→ +1 uit (−1 op diff)."
                ),
            )
        )
    elif away.scoring_trend < 0:
        out.append(
            PickAdjustment(
                id="away_scoring_trend_down",
                kind="momentum",
                label="Dalende scorelijn uit",
                delta=1,
                reason=(
                    f"{display_team_name(away.fifa_team)} scoorde minder in het laatste pouleduel "
                    f"→ +1 thuis."
                ),
            )
        )

    gpg_gap = home.goals_per_game - away.goals_per_game
    if gpg_gap >= 1.0:
        out.append(
            PickAdjustment(
                id="home_goals_per_game",
                kind="momentum",
                label="Meer goals per pouleduel thuis",
                delta=1,
                reason=(
                    f"{display_team_name(home.fifa_team)} scoorde gemiddeld {home.goals_per_game:.1f}x per duel, "
                    f"{display_team_name(away.fifa_team)} {away.goals_per_game:.1f}x → +1 thuis."
                ),
            )
        )
    elif gpg_gap <= -1.0:
        out.append(
            PickAdjustment(
                id="away_goals_per_game",
                kind="momentum",
                label="Meer goals per pouleduel uit",
                delta=-1,
                reason=(
                    f"{display_team_name(away.fifa_team)} scoorde gemiddeld {away.goals_per_game:.1f}x per duel, "
                    f"{display_team_name(home.fifa_team)} {home.goals_per_game:.1f}x "
                    f"→ +1 uit (−1 op diff)."
                ),
            )
        )

    return out


def group_expectation_adjustments(
    home: GroupFormStats | None,
    away: GroupFormStats | None,
    *,
    home_power: int,
    away_power: int,
) -> list[PickAdjustment]:
    """Poule-uitslag vs papier: max ±1 per team, alleen bij grote verrassing (≥3 punten)."""
    out: list[PickAdjustment] = []

    if home is not None and home.played >= 3:
        surprise = home.points - expected_group_points_from_power(home_power)
        if surprise >= _GROUP_EXPECTATION_SURPRISE_MIN:
            out.append(
                PickAdjustment(
                    id="home_group_expectation_over",
                    kind="momentum",
                    label="Poule boven verwachting thuis",
                    delta=_GROUP_EXPECTATION_DELTA,
                    reason=(
                        f"{display_team_name(home.fifa_team)} haalde {home.points} punten in de poule "
                        f"(op papier ~{expected_group_points_from_power(home_power)}) "
                        f"→ lichte +{_GROUP_EXPECTATION_DELTA} thuis; kan situatiegebonden zijn."
                    ),
                )
            )
        elif surprise <= -_GROUP_EXPECTATION_SURPRISE_MIN:
            out.append(
                PickAdjustment(
                    id="home_group_expectation_under",
                    kind="momentum",
                    label="Poule onder verwachting thuis",
                    delta=-_GROUP_EXPECTATION_DELTA,
                    reason=(
                        f"{display_team_name(home.fifa_team)} haalde {home.points} punten in de poule "
                        f"(op papier ~{expected_group_points_from_power(home_power)}) "
                        f"→ lichte −{_GROUP_EXPECTATION_DELTA} thuis; kan situatiegebonden zijn."
                    ),
                )
            )

    if away is not None and away.played >= 3:
        surprise = away.points - expected_group_points_from_power(away_power)
        if surprise >= _GROUP_EXPECTATION_SURPRISE_MIN:
            out.append(
                PickAdjustment(
                    id="away_group_expectation_over",
                    kind="momentum",
                    label="Poule boven verwachting uit",
                    delta=-_GROUP_EXPECTATION_DELTA,
                    reason=(
                        f"{display_team_name(away.fifa_team)} haalde {away.points} punten in de poule "
                        f"(op papier ~{expected_group_points_from_power(away_power)}) "
                        f"→ lichte +{_GROUP_EXPECTATION_DELTA} uit (−{_GROUP_EXPECTATION_DELTA} op diff); "
                        f"kan situatiegebonden zijn."
                    ),
                )
            )
        elif surprise <= -_GROUP_EXPECTATION_SURPRISE_MIN:
            out.append(
                PickAdjustment(
                    id="away_group_expectation_under",
                    kind="momentum",
                    label="Poule onder verwachting uit",
                    delta=_GROUP_EXPECTATION_DELTA,
                    reason=(
                        f"{display_team_name(away.fifa_team)} haalde {away.points} punten in de poule "
                        f"(op papier ~{expected_group_points_from_power(away_power)}) "
                        f"→ lichte +{_GROUP_EXPECTATION_DELTA} thuis; kan situatiegebonden zijn."
                    ),
                )
            )

    return out


def _knockout_side_adjustments(
    ko: KnockoutRoundStats | None,
    *,
    fifa: str,
    is_home: bool,
) -> list[PickAdjustment]:
    """90-min KO-vorm vóór deze ronde; delta > 0 = voordeel thuis."""
    if ko is None or ko.played == 0:
        return []

    team_nl = display_team_name(fifa)
    sign = 1 if is_home else -1
    out: list[PickAdjustment] = []

    win_delta = min(_KO_WIN_DELTA_MAX, ko.wins * _KO_WIN_DELTA)
    if win_delta:
        side = "thuis" if is_home else "uit"
        out.append(
            PickAdjustment(
                id=f"{'home' if is_home else 'away'}_ko_wins",
                kind="knockout_form",
                label=f"KO-winsten {side}",
                delta=sign * win_delta,
                reason=(
                    f"{team_nl}: {ko.wins}× gewonnen na 90 min in knock-out "
                    f"→ {'+' if sign > 0 else '−'}{win_delta}."
                ),
            )
        )

    if ko.upset_wins >= 1 and ko.max_upset_power_gap >= _KO_UPSET_POWER_GAP_MIN:
        out.append(
            PickAdjustment(
                id=f"{'home' if is_home else 'away'}_ko_upset",
                kind="knockout_form",
                label=f"KO-stunt {team_nl}",
                delta=sign * _KO_UPSET_DELTA,
                reason=(
                    f"{team_nl} versloeg sterkere tegenstander in knock-out "
                    f"(papierverschil tot {ko.max_upset_power_gap}) → {'+' if sign > 0 else '−'}{_KO_UPSET_DELTA}."
                ),
            )
        )

    if ko.wins >= 1 and ko.goals_for >= _KO_ATTACK_GOALS_MIN:
        out.append(
            PickAdjustment(
                id=f"{'home' if is_home else 'away'}_ko_attack",
                kind="knockout_form",
                label=f"KO-aanval {team_nl}",
                delta=sign * _KO_ATTACK_DELTA,
                reason=(
                    f"{team_nl}: {ko.goals_for} goals in {ko.played} knock-outduel(s) "
                    f"→ {'+' if sign > 0 else '−'}{_KO_ATTACK_DELTA}."
                ),
            )
        )

    return [a for a in out if a.delta != 0]


def _knockout_favorite_trim(
    home_ko: KnockoutRoundStats | None,
    away_ko: KnockoutRoundStats | None,
    *,
    base_diff: int,
) -> list[PickAdjustment]:
    """Papierfavoriet temperen als underdog al een KO-stunt leverde (Noorwegen/Brazilië)."""
    if abs(base_diff) < _KO_FAVORITE_TRIM_MIN_DIFF:
        return []

    if base_diff < 0 and home_ko and home_ko.upset_wins >= 1:
        trim = min(_KO_FAVORITE_TRIM_CAP, abs(base_diff) // 2)
        return [
            PickAdjustment(
                id="home_ko_favorite_trim",
                kind="knockout_form",
                label="KO-momentum thuis vs papier",
                delta=trim,
                reason=(
                    f"Thuisploeg met knock-out-stunt; papierverschil {base_diff} "
                    f"→ +{trim} richting thuis/gelijk na 90 min."
                ),
            )
        ]

    if base_diff > 0 and away_ko and away_ko.upset_wins >= 1:
        trim = min(_KO_FAVORITE_TRIM_CAP, abs(base_diff) // 2)
        return [
            PickAdjustment(
                id="away_ko_favorite_trim",
                kind="knockout_form",
                label="KO-momentum uit vs papier",
                delta=-trim,
                reason=(
                    f"Uitploeg met knock-out-stunt; papierverschil {base_diff:+d} "
                    f"→ −{trim} richting uit/gelijk na 90 min."
                ),
            )
        ]

    return []


def _knockout_defensive_draw_nudge(
    home_ko: KnockoutRoundStats | None,
    away_ko: KnockoutRoundStats | None,
    *,
    base_diff: int,
) -> list[PickAdjustment]:
    """Beide teams defensief in KO, of underdog met 0-0-karakter vs favoriet."""

    def _defensive(ko: KnockoutRoundStats | None) -> bool:
        if ko is None or ko.played == 0:
            return False
        if ko.draws >= 1:
            return True
        return ko.goals_against == 0

    home_def = _defensive(home_ko)
    away_def = _defensive(away_ko)

    if home_def and away_def and abs(base_diff) > 3:
        delta = -_KO_DEFENSIVE_DRAW_DELTA if base_diff > 0 else _KO_DEFENSIVE_DRAW_DELTA
        return [
            PickAdjustment(
                id="ko_defensive_draw_nudge",
                kind="knockout_form",
                label="KO-defensief duel",
                delta=delta,
                reason=(
                    "Beide ploegen toonden defensieve knock-outvorm "
                    f"→ {delta:+d} richting gelijk na 90 min."
                ),
            )
        ]

    if away_def and base_diff >= 8:
        return [
            PickAdjustment(
                id="ko_defensive_underdog_away",
                kind="knockout_form",
                label="KO-defensie uit",
                delta=-_KO_DEFENSIVE_DRAW_DELTA,
                reason=(
                    "Uitploeg hield knock-out strak (0-0 of weinig tegengoals); favoriet op papier "
                    "→ −2 richting gelijk na 90 min."
                ),
            )
        ]

    if home_def and base_diff <= -8:
        return [
            PickAdjustment(
                id="ko_defensive_underdog_home",
                kind="knockout_form",
                label="KO-defensie thuis",
                delta=_KO_DEFENSIVE_DRAW_DELTA,
                reason=(
                    "Thuisploeg hield knock-out strak (0-0 of weinig tegengoals); favoriet op papier "
                    "→ +2 richting gelijk na 90 min."
                ),
            )
        ]

    return []


def knockout_momentum_adjustments(
    home_ko: KnockoutRoundStats | None,
    away_ko: KnockoutRoundStats | None,
    *,
    home_key: str,
    away_key: str,
    base_diff: int,
) -> list[PickAdjustment]:
    """Knock-out vóór deze ronde: winst, stunt, aanval en defensieve gelijk-neiging."""
    out: list[PickAdjustment] = []
    out.extend(_knockout_side_adjustments(home_ko, fifa=home_key, is_home=True))
    out.extend(_knockout_side_adjustments(away_ko, fifa=away_key, is_home=False))
    out.extend(_knockout_favorite_trim(home_ko, away_ko, base_diff=base_diff))
    out.extend(_knockout_defensive_draw_nudge(home_ko, away_ko, base_diff=base_diff))
    return out


def collect_pick_adjustments(
    *,
    home_key: str,
    away_key: str,
    home_power: int,
    away_power: int,
    home_factors: list[dict[str, object]],
    away_factors: list[dict[str, object]],
    live_form: tuple[int, int, int, int] | None = None,
    include_live_form: bool = False,
    home_form: GroupFormStats | None = None,
    away_form: GroupFormStats | None = None,
    home_ko: KnockoutRoundStats | None = None,
    away_ko: KnockoutRoundStats | None = None,
    base_diff: int = 0,
    include_knockout_form: bool = False,
) -> list[PickAdjustment]:
    """Pool-stappen. `live_form` / `home_form` alleen bij knock-out na de groep."""
    adjustments: list[PickAdjustment] = []
    adjustments.extend(_side_yaml_adjustments(home_key, is_home=True))
    adjustments.extend(_side_yaml_adjustments(away_key, is_home=False))

    h2h = _h2h_adjustment(home_key, away_key)
    if h2h:
        adjustments.append(h2h)

    upset = _upset_adjustment(
        home_key=home_key,
        away_key=away_key,
        home_power=home_power,
        away_power=away_power,
        home_factors=home_factors,
        away_factors=away_factors,
    )
    if upset:
        adjustments.append(upset)

    if include_live_form and live_form:
        hp, hpl, ap, apl = live_form
        adjustments.extend(
            live_form_from_results(
                home_fifa=home_key,
                away_fifa=away_key,
                home_points=hp,
                away_points=ap,
                home_played=hpl,
                away_played=apl,
            )
        )

    if include_live_form:
        adjustments.extend(group_momentum_adjustments(home_form, away_form))
        adjustments.extend(group_scoring_trend_adjustments(home_form, away_form))
        adjustments.extend(
            group_expectation_adjustments(
                home_form,
                away_form,
                home_power=home_power,
                away_power=away_power,
            )
        )

    if include_knockout_form:
        adjustments.extend(
            knockout_momentum_adjustments(
                home_ko,
                away_ko,
                home_key=home_key,
                away_key=away_key,
                base_diff=base_diff,
            )
        )

    cap = _POOL_DIFF_CAP_KNOCKOUT if include_knockout_form else _POOL_DIFF_CAP
    total = sum(a.delta for a in adjustments)
    if abs(total) > cap:
        scale = cap / abs(total)
        adjustments = [
            PickAdjustment(
                id=a.id,
                kind=a.kind,
                label=a.label,
                delta=round(a.delta * scale) or (1 if a.delta > 0 else -1),
                reason=a.reason + f" (begrensd tot ±{cap} totaal)",
            )
            for a in adjustments
            if a.delta != 0
        ]
    return [a for a in adjustments if a.delta != 0]


def apply_adjustments(base_diff: int, adjustments: list[PickAdjustment]) -> int:
    total = sum(a.delta for a in adjustments)
    return base_diff + _clamp(total, -_POOL_DIFF_CAP, _POOL_DIFF_CAP)


