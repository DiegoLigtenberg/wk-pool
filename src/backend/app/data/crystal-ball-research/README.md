# Crystal Ball research

Bonusantwoorden voor de WK-pool (Tony's Toto-reglement), los van de 72 groepswedstrijd-toto's.

## Bestanden

| Bestand | Doel |
|---------|------|
| `tournament_2026.yaml` | Bonusvragen + onderbouwing (gele kaarten, direct rood, kampioen, topscorer) |
| `_template.yaml` | Leeg sjabloon voor volgende edities |

## Poolregels (samenvatting)

- **Gele kaarten totaal**: in de pool telt een *indirect* rood (tweede geel) als **2 gele kaarten** mee in het totaal.
- **Direct rood**: alleen rode kaarten **zonder** voorafgaand tweede geel (straight red).
- **Topscorer**: meeste doelpunten in het **hele toernooi**, niet alleen knock-out.

## Hernieuwen

1. Pas `tournament_2026.yaml` aan (`context_as_of`, `sources`, `bonus_questions`).
2. Herstart backend; `/api/tournament` → `crystalBall.bonusQuestions`.

Groepswinnaars komen **niet** uit dit bestand: die worden automatisch berekend uit alle AI 1/2/3-picks op groepswedstrijden.
