import type { Match } from "../types";

const TEAM_NAMES_NL: Record<string, string> = {
  Algeria: "Algerije",
  Argentina: "Argentinië",
  Australia: "Australië",
  Austria: "Oostenrijk",
  Belgium: "België",
  "Bosnia and Herzegovina": "Bosnië-Herzegovina",
  Brazil: "Brazilië",
  Canada: "Canada",
  "Cabo Verde": "Kaapverdië",
  Colombia: "Colombia",
  "Congo DR": "Congo",
  Croatia: "Kroatië",
  Curaçao: "Curaçao",
  Czechia: "Tsjechië",
  Ecuador: "Ecuador",
  Egypt: "Egypte",
  England: "Engeland",
  France: "Frankrijk",
  Germany: "Duitsland",
  Ghana: "Ghana",
  Haiti: "Haïti",
  "IR Iran": "Iran",
  Iraq: "Irak",
  Japan: "Japan",
  Jordan: "Jordanië",
  "Korea Republic": "Zuid-Korea",
  Mexico: "Mexico",
  Morocco: "Marokko",
  Netherlands: "Nederland",
  "New Zealand": "Nieuw-Zeeland",
  Norway: "Noorwegen",
  Panama: "Panama",
  Paraguay: "Paraguay",
  Portugal: "Portugal",
  Qatar: "Qatar",
  "Saudi Arabia": "Saoedi-Arabië",
  Scotland: "Schotland",
  Senegal: "Senegal",
  "South Africa": "Zuid-Afrika",
  Spain: "Spanje",
  Sweden: "Zweden",
  Switzerland: "Zwitserland",
  Tunisia: "Tunesië",
  Türkiye: "Turkije",
  Uruguay: "Uruguay",
  USA: "Verenigde Staten",
  Uzbekistan: "Oezbekistan",
  "Côte d'Ivoire": "Ivoorkust",
};

const TEAM_FLAG_CODES: Record<string, string> = {
  Algeria: "dz",
  Argentina: "ar",
  Australia: "au",
  Austria: "at",
  Belgium: "be",
  "Bosnia and Herzegovina": "ba",
  Brazil: "br",
  Canada: "ca",
  "Cabo Verde": "cv",
  Colombia: "co",
  "Congo DR": "cd",
  Croatia: "hr",
  Curaçao: "cw",
  Czechia: "cz",
  Ecuador: "ec",
  Egypt: "eg",
  England: "gb-eng",
  France: "fr",
  Germany: "de",
  Ghana: "gh",
  Haiti: "ht",
  "IR Iran": "ir",
  Iraq: "iq",
  Japan: "jp",
  Jordan: "jo",
  "Korea Republic": "kr",
  Mexico: "mx",
  Morocco: "ma",
  Netherlands: "nl",
  "New Zealand": "nz",
  Norway: "no",
  Panama: "pa",
  Paraguay: "py",
  Portugal: "pt",
  Qatar: "qa",
  "Saudi Arabia": "sa",
  Scotland: "gb-sct",
  Senegal: "sn",
  "South Africa": "za",
  Spain: "es",
  Sweden: "se",
  Switzerland: "ch",
  Tunisia: "tn",
  Türkiye: "tr",
  Uruguay: "uy",
  USA: "us",
  Uzbekistan: "uz",
  "Côte d'Ivoire": "ci",
};

export function teamNameNl(team: string): string {
  return TEAM_NAMES_NL[team] ?? team;
}

export function countryCodeForTeam(team: string): string | null {
  return TEAM_FLAG_CODES[team] ?? null;
}

export function isRealTeamName(team: string): boolean {
  return (
    team !== "To be announced" &&
    !/^([123])([A-L])$/.test(team) &&
    !/^3([A-L]{2,})$/.test(team)
  );
}

export function displayTeamName(team: string): string {
  return isRealTeamName(team) ? teamNameNl(team) : "Onbekend";
}

export function hasKnownTeams(match: Match): boolean {
  return isRealTeamName(match.homeTeam) && isRealTeamName(match.awayTeam);
}

export function truncateLabel(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength - 3).trimEnd()}...`;
}
