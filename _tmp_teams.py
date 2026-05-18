import csv
from pathlib import Path
p = Path(r"c:\Github\wk-pool\src\backend\app\data\fifa-world-cup-2026-UTC.csv")
teams = set()
with p.open(encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        teams.add(row["Home Team"])
        teams.add(row["Away Team"])
print("Aantal:", len(teams))
print("Italy:", "Italy" in teams)
for t in sorted(teams):
    print(t)
