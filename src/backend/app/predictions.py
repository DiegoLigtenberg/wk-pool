import math
import re
from dataclasses import dataclass

from app.data.teams.context_score import match_context_breakdown
from app.data.teams.team_bundle import TeamBundle
from app.data.teams.team_loader import get_team_bundle
from app.display_text import humanize_research_line, humanize_team_spark
from app.prediction_narrative import build_prediction_insight
from app.teams import display_team_name, fifa_team_key

_FIXTURE_HOOK_RE = re.compile(
    r"^Groepswedstrijd\s+(\d+)\s*\([^)]*\):\s*(thuis|uit)\s+vs\s+(.+?)\s*@\s*(.+)$",
    re.IGNORECASE,
)


PICKS = ("1", "2", "3")

# NL toernooiladder (enkelvoud per ploeg in teamvisie).
TIER_TOPFAVORIET = "Topfavoriet"
TIER_FAVORIET = "Favoriet"
TIER_SUBTOPPER = "Subtopper"
TIER_UNDERDOG = "Underdog"
TIER_VERRASSINGS_PLOEG = "Verrassingsploeg"


@dataclass(frozen=True)
class TeamProfile:
    rating: int
    tier: str
    style: str
    strengths: tuple[str, ...]
    risks: tuple[str, ...]
    niche: tuple[str, ...]


DEFAULT_PROFILE = TeamProfile(
    rating=62,
    tier=TIER_UNDERDOG,
    style="compact spelen, momenten kiezen en leunen op wedstrijdenergie",
    strengths=("organisatie", "fysieke duels", "standaardsituaties"),
    risks=("minder individuele topkwaliteit", "kan moeite hebben als het zelf het spel moet maken"),
    niche=("wedstrijdritme en groepsdynamiek wegen hier zwaar",),
)


# Alleen nog gebruikt door `sync_research_yaml` om ratings in YAML te zetten.
# Runtime voorspelling leest `teams/{slug}.yaml` via `get_team_bundle`.
TEAM_PROFILES: dict[str, TeamProfile] = {
    "Argentina": TeamProfile(91, TIER_TOPFAVORIET, "ervaren, pragmatisch en sterk in beslissende fases", ("wereldklasse in de as", "toernooi-ervaring", "wedstrijdcontrole"), ("leunt soms op kleine marges", "tempo kan zakken tegen energieke tegenstanders"), ("veel spelers kennen elkaars rollen uit meerdere eindtoernooien",)),
    "France": TeamProfile(92, TIER_TOPFAVORIET, "explosief, atletisch en diep in elke linie", ("selectiebreedte", "transitiegevaar", "knock-out ervaring"), ("kan soms slordig worden bij veel balbezit", "verwachtingsdruk"), ("veel profielen die een wedstrijd individueel kunnen kantelen",)),
    "Brazil": TeamProfile(90, TIER_TOPFAVORIET, "technisch dominant met veel aanvallende variatie", ("creativiteit", "1-tegen-1 kwaliteit", "aanvallende diepte"), ("balans bij counters", "druk rond grote toernooien"), ("kan via individuele acties door gesloten blokken heen breken",)),
    "Spain": TeamProfile(89, TIER_TOPFAVORIET, "possession, pressing en controle via middenveld", ("balcontrole", "pressing", "technische zekerheid"), ("kan kwetsbaar zijn als kansen niet snel vallen", "ruimte achter de backs"), ("synergie uit herkenbare Spaanse school en clubconnecties",)),
    "England": TeamProfile(88, TIER_TOPFAVORIET, "hoog individueel niveau met veel scorend vermogen", ("aanvalskwaliteit", "squad depth", "standaardsituaties"), ("toernooidruk", "balans tussen voorzichtigheid en initiatief"), ("veel spelers gewend aan hoge intensiteit in de Premier League",)),
    "Portugal": TeamProfile(87, TIER_FAVORIET, "technisch sterk en flexibel tussen controle en counters", ("creatieve middenvelders", "diepte in de selectie", "ervaring"), ("kan afhankelijk worden van momenten", "defensieve restverdediging"), ("mix van jonge energie en ervaren leiderschap",)),
    "Germany": TeamProfile(86, TIER_FAVORIET, "gestructureerd, fysiek en gevaarlijk in momentumfases", ("wedstrijdritme", "druk zetten", "toernooi-DNA"), ("recente wisselvalligheid", "ruimte in omschakeling"), ("Duitse teams kunnen in toernooien vaak boven vorm uitstijgen",)),
    "Netherlands": TeamProfile(85, TIER_FAVORIET, "compact, tactisch en sterk in omschakeling", ("defensieve kwaliteit", "luchtduels", "coachbare structuur"), ("creativiteit tegen lage blokken", "efficiëntie voor goal"), ("veel spelers zijn gewend aan tactisch strakke clubsystemen",)),
    "Belgium": TeamProfile(82, TIER_SUBTOPPER, "technisch, ervaren en gevaarlijk tussen de linies", ("aanvallende kwaliteit", "ervaring", "passing"), ("generatiewissel", "snelheid achterin"), ("oude automatismen en nieuwe rollen moeten samenvallen",)),
    "Croatia": TeamProfile(82, TIER_SUBTOPPER, "ervaren, geduldig en extreem comfortabel in spannende wedstrijden", ("middenveldcontrole", "toernooi-rust", "mentale hardheid"), ("leeftijd en intensiteit", "minder pure snelheid"), ("kan wedstrijden lang in leven houden en laat beslissingen laat vallen",)),
    "Uruguay": TeamProfile(82, TIER_SUBTOPPER, "agressief, direct en competitief", ("fysieke intensiteit", "aanvallende power", "duelkracht"), ("discipline", "ruimte bij hoge druk"), ("Zuid-Amerikaanse wedstrijdhardheid maakt ze lastig in knock-outachtige duels",)),
    "Morocco": TeamProfile(81, TIER_SUBTOPPER, "compact, volwassen en gevaarlijk vanuit transitie", ("organisatie", "mentale energie", "counters"), ("kan moeite hebben met favorietenrol", "kansenvolume"), ("WK 2022 liet zien dat dit team in knock-outfases boven zichzelf kan uitstijgen",)),
    "Colombia": TeamProfile(80, TIER_SUBTOPPER, "technisch, fel en aanvallend creatief", ("vormgolven", "creativiteit", "fysieke intensiteit"), ("wedstrijdcontrole", "emotionele momenten"), ("kan vanuit sfeer en momentum snel boven zichzelf uitstijgen",)),
    "Switzerland": TeamProfile(79, TIER_SUBTOPPER, "gedisciplineerd, volwassen en moeilijk kapot te spelen", ("organisatie", "ervaring", "compactheid"), ("minder explosieve aanval", "moeite met openbreken"), ("vaak sterker dan de namen op papier suggereren",)),
    "USA": TeamProfile(78, TIER_SUBTOPPER, "atletisch, direct en energiek", ("intensiteit", "thuisregio", "loopvermogen"), ("eindpass", "controle onder druk"), ("WK in eigen regio kan extra energie en ritme geven",)),
    "Mexico": TeamProfile(77, TIER_SUBTOPPER, "emotioneel geladen, intens en thuisregio-gedreven", ("publieksenergie", "ervaring", "duelkracht"), ("druk op de ploeg", "creativiteit tegen lage blokken"), ("openingswedstrijd en Mexicaanse omstandigheden kunnen veel invloed hebben",)),
    "Japan": TeamProfile(77, TIER_SUBTOPPER, "snel, technisch en tactisch volwassen", ("pressing", "teamdiscipline", "tempo"), ("fysieke duels", "afmaken van kansen"), ("sterke collectieve automatismen compenseren soms sterverschil",)),
    "Senegal": TeamProfile(77, TIER_SUBTOPPER, "fysiek sterk en gevaarlijk in omschakeling", ("atletiek", "duelkracht", "directe dreiging"), ("creatieve controle", "consistentie"), ("kan favorieten ongemakkelijk maken met tempo en duels",)),
    "Türkiye": TeamProfile(76, TIER_UNDERDOG, "emotioneel, technisch en grillig", ("creativiteit", "afstandsschoten", "wedstrijdenergie"), ("stabiliteit", "defensieve ruimtes"), ("momentum speelt bij Turkije vaak opvallend zwaar mee",)),
    "Austria": TeamProfile(76, TIER_UNDERDOG, "intens, georganiseerd en pressend", ("collectief drukzetten", "discipline", "fitheid"), ("individuele topkwaliteit", "kansen creëren tegen lage blokken"), ("coachcontinuïteit en systeemvastheid zijn belangrijke pluspunten",)),
    "Sweden": TeamProfile(75, TIER_UNDERDOG, "fysiek, direct en sterk in organisatie", ("luchtduels", "discipline", "standaardsituaties"), ("tempo in balbezit", "creativiteit"), ("kan wedstrijden vertragen en tegenstanders uit ritme halen",)),
    "Norway": TeamProfile(75, TIER_UNDERDOG, "topzwaar met veel dreiging in de voorhoede", ("elite-afwerking", "fysiek voorin", "direct spel"), ("balans in de ploeg", "toernooi-ervaring"), ("als de aanvoer naar de spitsen klopt, stijgt de win-kans snel",)),
    "Ecuador": TeamProfile(74, TIER_UNDERDOG, "fysiek, energiek en lastig in duels", ("intensiteit", "jonge kern", "transities"), ("ervaring in late fases", "controle"), ("hoog tempo en atletiek kunnen technisch sterkere teams verstoren",)),
    "Côte d'Ivoire": TeamProfile(74, TIER_UNDERDOG, "krachtig, direct en gevaarlijk in open wedstrijden", ("fysiek", "aanvallende power", "duels"), ("organisatie", "consistentie"), ("Afrikaanse toernooi-energie en fysieke profielen maken ze gevaarlijk",)),
    "Paraguay": TeamProfile(72, TIER_UNDERDOG, "hard, compact en wedstrijdslim", ("duels", "verdedigende organisatie", "standaardsituaties"), ("aanvallende variatie", "balbezit onder druk"), ("kan favorieten frustreren door tempo en ruimtes klein te maken",)),
    "Canada": TeamProfile(72, TIER_UNDERDOG, "snel, atletisch en direct", ("snelheid", "thuisregio", "omschakeling"), ("ervaring", "defensieve stabiliteit"), ("Noord-Amerikaanse omstandigheden kunnen in hun voordeel werken",)),
    "Australia": TeamProfile(71, TIER_UNDERDOG, "fysiek, compact en mentaal taai", ("discipline", "duelkracht", "teamgeest"), ("creativiteit", "kansenvolume"), ("vaak beter in toernooiwedstrijden dan in losse ratings",)),
    "Scotland": TeamProfile(71, TIER_UNDERDOG, "intens, fysiek en collectief", ("teamspirit", "duels", "standaardsituaties"), ("aanvallende verfijning", "diepte in selectie"), ("kan via chaos en energie wedstrijden openbreken",)),
    "Czechia": TeamProfile(71, TIER_UNDERDOG, "gedisciplineerd, fysiek en direct", ("organisatie", "duels", "standaardsituaties"), ("creativiteit", "tempo achterin"), ("comfortabel in wedstrijden waarin details beslissen",)),
    "Ghana": TeamProfile(70, TIER_UNDERDOG, "fysiek, explosief en onvoorspelbaar", ("atletiek", "transitie", "individuele momenten"), ("controle", "defensieve samenhang"), ("kan via tempo en duelkracht snel momentum pakken",)),
    "Algeria": TeamProfile(70, TIER_UNDERDOG, "technisch en emotioneel geladen", ("creativiteit", "ervaring", "wedstrijdenergie"), ("consistentie", "ruimte achter druk"), ("Noord-Afrikaanse flair maakt ze gevaarlijk in losse wedstrijden",)),
    "Egypt": TeamProfile(70, TIER_UNDERDOG, "ervaren en compact met individuele dreiging", ("ervaring", "discipline", "aanvallende sterkwaliteit"), ("tempo", "diepte in selectie"), ("kan lang in wedstrijden blijven en wachten op één moment",)),
    "Korea Republic": TeamProfile(70, TIER_UNDERDOG, "snel, gedisciplineerd en hard werkend", ("loopvermogen", "organisatie", "transities"), ("fysieke mismatch", "creativiteit centraal"), ("collectieve discipline maakt het verschil tegen gelijkwaardige teams",)),
    "IR Iran": TeamProfile(69, TIER_UNDERDOG, "compact, fysiek en countergericht", ("organisatie", "duels", "directe counters"), ("balbezit", "creativiteit"), ("kan wedstrijden gesloten houden en de underdogrol goed spelen",)),
    "Tunisia": TeamProfile(68, TIER_UNDERDOG, "compact, fel en defensief gedisciplineerd", ("organisatie", "duels", "teamdiscipline"), ("scorend vermogen", "risico nemen"), ("kan favorieten lang frustreren als het eerste doelpunt uitblijft",)),
    "Saudi Arabia": TeamProfile(68, TIER_UNDERDOG, "energiek, technisch en agressief in drukmomenten", ("intensiteit", "brutale momenten", "teamenergie"), ("consistentie", "ruimte achterin"), ("kan in één wedstrijd veel gevaarlijker zijn dan de rating suggereert",)),
    "Qatar": TeamProfile(66, TIER_UNDERDOG, "compact en gewend aan toernooivoetbal in korte periodes", ("organisatie", "ervaring samen", "discipline"), ("tempo", "individuele topkwaliteit"), ("veel spelers hebben vaak in vergelijkbare nationale structuur gespeeld",)),
    "South Africa": TeamProfile(66, TIER_UNDERDOG, "energiek, fysiek en opportunistisch", ("wedstrijdenergie", "duels", "counters"), ("controle", "efficiëntie"), ("kan profiteren als de tegenstander onder openingsdruk staat",)),
    "Uzbekistan": TeamProfile(65, TIER_VERRASSINGS_PLOEG, "gestructureerd, hardwerkend en compact", ("discipline", "organisatie", "teamcohesie"), ("ervaring op dit podium", "aanvallende topkwaliteit"), ("eerste WK-context kan extra energie geven, maar ook nervositeit",)),
    "Congo DR": TeamProfile(65, TIER_VERRASSINGS_PLOEG, "fysiek sterk en gevaarlijk in losse fases", ("atletiek", "duels", "directheid"), ("organisatie", "balvaste controle"), ("kan met fysieke mismatch wedstrijden kantelen",)),
    "Bosnia and Herzegovina": TeamProfile(65, TIER_VERRASSINGS_PLOEG, "technisch in fases en afhankelijk van sleutelspelers", ("ervaring", "passing", "momentenkwaliteit"), ("tempo", "diepte in selectie"), ("als de ervaren kern controle vindt, wordt het een lastige matchup",)),
    "Iraq": TeamProfile(64, TIER_VERRASSINGS_PLOEG, "compact, fel en emotioneel sterk", ("teamenergie", "duels", "organisatie"), ("kansen creëren", "ervaring tegen elite"), ("kan vanuit underdogpositie lang overleven in wedstrijden",)),
    "New Zealand": TeamProfile(62, TIER_VERRASSINGS_PLOEG, "fysiek, simpel en collectief", ("luchtduels", "discipline", "teamspirit"), ("technische controle", "tempo tegen toplanden"), ("standaardsituaties zijn relatief belangrijk voor hun kans",)),
    "Jordan": TeamProfile(62, TIER_VERRASSINGS_PLOEG, "compact, reactief en energiek", ("organisatie", "counters", "teamdiscipline"), ("balbezit onder druk", "selectiediepte"), ("kan verrassen als het lang 0-0 blijft",)),
    "Panama": TeamProfile(61, TIER_VERRASSINGS_PLOEG, "fysiek en direct", ("duels", "energie", "standaardsituaties"), ("controle", "creatieve kwaliteit"), ("regionale omstandigheden kunnen helpen tegen niet-Amerikaanse landen",)),
    "Haiti": TeamProfile(60, TIER_VERRASSINGS_PLOEG, "direct, atletisch en emotioneel", ("snelheid", "fysiek", "verrassingswaarde"), ("organisatie", "toernooi-ervaring"), ("chaotische wedstrijden vergroten hun upset-kans",)),
    "Cabo Verde": TeamProfile(60, TIER_VERRASSINGS_PLOEG, "compact en trots, met focus op omschakeling", ("teamspirit", "organisatie", "transitie"), ("selectiediepte", "ervaring"), ("kleine landen kunnen juist gevaarlijk zijn als niemand ze comfortabel vindt",)),
    "Curaçao": TeamProfile(59, TIER_VERRASSINGS_PLOEG, "technisch in momenten en afhankelijk van discipline", ("verrassingswaarde", "individuele momenten", "compactheid"), ("diepte", "ervaring tegen toplanden"), ("Nederlandse voetbalinvloeden kunnen tactisch helpen",)),
}


def is_known_team(team: str) -> bool:
    if team == "To be announced" or team[:1].isdigit():
        return False
    try:
        get_team_bundle(team)
        return True
    except KeyError:
        return False


def profile_for(team: str) -> TeamProfile:
    try:
        bundle = get_team_bundle(team)
    except KeyError:
        return DEFAULT_PROFILE
    return TeamProfile(
        rating=bundle.power_score,
        tier=bundle.tier,
        style=bundle.macro_style,
        strengths=bundle.strengths,
        risks=bundle.risks,
        niche=(),
    )


def team_insight(team: str) -> dict[str, object] | None:
    if not is_known_team(team):
        return None

    bundle = get_team_bundle(team)
    profile = profile_for(team)
    return {
        "team": bundle.team_name_nl,
        "tier": bundle.tier,
        "style": bundle.macro_style,
        "powerScore": bundle.power_score,
        "strengths": list(bundle.strengths),
        "risks": list(bundle.risks),
        "group": bundle.group_stage.group,
        "opponents": list(bundle.group_stage.opponents_nl),
        "distinctiveSpark": humanize_team_spark(bundle.distinctive_spark_notes, bundle.team_name_nl)
        if bundle.distinctive_spark_notes
        else None,
        "groupContext": _group_context_lines(bundle),
        "summary": _team_summary(team, profile),
    }


def _group_context_lines(bundle: TeamBundle) -> list[str]:
    lines: list[str] = []
    group_label = f"groep {bundle.group_stage.group.lower()}:"

    for hook in bundle.group_stage.fixture_hooks:
        text = hook.strip().strip("'\"")
        if not text or text.lower().startswith(group_label):
            continue
        lines.append(_humanize_fixture_hook(text, bundle.team_name_nl))

    if not lines:
        for fx in bundle.group_stage.fixtures:
            side = "thuis" if fx.is_home else "uit"
            lines.append(f"Wedstrijd {fx.match_number}: {side} tegen {fx.opponent_nl}")

    return lines[:4]


def _humanize_fixture_hook(hook: str, team_nl: str) -> str:
    match = _FIXTURE_HOOK_RE.match(hook.strip())
    if match:
        number, side, opponent, stadium = match.groups()
        return (
            f"Wedstrijd {number}: {side.lower()} tegen {opponent.strip()} "
            f"({stadium.strip()})"
        )
    return humanize_research_line(hook, team_nl=team_nl)


def predict_match(home_team: str, away_team: str, stage: str, round_name: str, group: str | None) -> dict[str, object]:
    if not is_known_team(home_team) or not is_known_team(away_team):
        return {
            "pick": "3",
            "confidence": 0,
            "explanation": "De AI wacht met inhoudelijke voorspelling tot beide landen bekend zijn.",
            "homeWinProbability": None,
            "drawProbability": None,
            "awayWinProbability": None,
        }

    home_key = fifa_team_key(home_team)
    away_key = fifa_team_key(away_team)
    breakdown = match_context_breakdown(home_key, away_key)
    diff = int(breakdown["diff"])
    can_draw = stage == "group"

    probabilities = _probabilities(diff, can_draw)
    pick = _pick_from_probabilities(probabilities, can_draw)
    confidence = _confidence_from_probabilities(pick, probabilities)
    insight = build_prediction_insight(
        home_team=home_key,
        away_team=away_key,
        pick=pick,
        breakdown=breakdown,
        diff=int(breakdown["diff"]),
        stage=stage,
        round_name=round_name,
    )

    return {
        "pick": pick,
        "confidence": confidence,
        "explanation": str(insight["verdict"]),
        "insight": insight,
        "homeWinProbability": probabilities["home"],
        "drawProbability": probabilities["draw"] if can_draw else None,
        "awayWinProbability": probabilities["away"],
    }


def _team_summary(team: str, profile: TeamProfile) -> str:
    name = display_team_name(team)
    text = f"{name} wordt gezien als {profile.tier.lower()}."
    if profile.risks:
        text += f" Belangrijkste risico: {profile.risks[0]}."
    return text


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# Groep: diff=0 → ~36% thuis; diff=8 → ~58% thuis (marginaal, incl. gelijk).
_GROUP_HOME_LOGIT_K = 0.112
_GROUP_HOME_LOGIT_B = math.log(0.36 / 0.64)

# Knock-out: steilere curve, geen gelijk.
_KNOCKOUT_HOME_LOGIT_K = 0.155


def _probabilities(diff: int, can_draw: bool) -> dict[str, int]:
    if can_draw:
        return _group_probabilities(diff)
    return _knockout_probabilities(diff)


def _group_probabilities(diff: int) -> dict[str, int]:
    draw_pct = int(round(max(16, min(32, 29 - 1.1 * abs(diff)))))
    p_draw = draw_pct / 100.0
    p_home = _sigmoid(diff * _GROUP_HOME_LOGIT_K + _GROUP_HOME_LOGIT_B)
    p_away = max(0.08, 1.0 - p_home - p_draw)
    p_home = max(0.08, 1.0 - p_away - p_draw)
    total = p_home + p_draw + p_away
    home = int(round(100 * p_home / total))
    draw = int(round(100 * p_draw / total))
    away = 100 - home - draw

    # Gelijkwaardige duels: gelijk strikt hoogste kans (pick = gelijk).
    if abs(diff) <= 2 and draw <= max(home, away):
        draw = max(home, away) + 1
        away = max(8, 100 - home - draw)
        if home + draw + away != 100:
            away = 100 - home - draw

    return {"home": home, "draw": draw, "away": away}


def _knockout_probabilities(diff: int) -> dict[str, int]:
    p_home = _sigmoid(diff * _KNOCKOUT_HOME_LOGIT_K)
    home = int(round(100 * p_home))
    home = max(15, min(88, home))
    return {"home": home, "draw": 0, "away": 100 - home}


def _pick_from_probabilities(probabilities: dict[str, int], can_draw: bool) -> str:
    home = int(probabilities["home"])
    away = int(probabilities["away"])
    draw = int(probabilities.get("draw") or 0)
    if can_draw and draw >= home and draw >= away:
        return "3"
    return "1" if home >= away else "2"


def _confidence_from_probabilities(pick: str, probabilities: dict[str, int]) -> int:
    if pick == "1":
        return probabilities["home"]
    if pick == "2":
        return probabilities["away"]
    return probabilities["draw"]
