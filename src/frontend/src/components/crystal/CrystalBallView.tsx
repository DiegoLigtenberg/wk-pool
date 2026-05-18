import type { Group } from "../../types";
import { TeamLabel } from "../cards/TeamLabel";
import "./CrystalBallView.css";

type CrystalBallViewProps = {
  groups: Group[];
};

export function CrystalBallView({ groups }: CrystalBallViewProps) {
  return (
    <section className="panel" id="crystal-ball">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Crystal Ball</p>
          <h2>Toernooi-voorspellingen</h2>
        </div>
      </div>
      <div className="crystal-layout">
        <div>
          <div className="section-label">Groepswinnaars</div>
          <div className="winner-grid">
            {groups.map((group) => (
              <article className="winner-card" key={group.name}>
                <span>Poule {group.name}</span>
                <strong>{group.standings[0] ? <TeamLabel team={group.standings[0].team} /> : "Nog onbekend"}</strong>
              </article>
            ))}
          </div>
        </div>
        <div>
          <div className="section-label">Bonusvragen</div>
          <div className="bonus-grid">
            <BonusCard label="Gele kaarten" value="221" helper="Indirect rood telt als 2 gele kaarten." />
            <BonusCard label="Direct rood" value="8" helper="Alleen directe rode kaarten tellen mee." />
            <BonusCard label="Wereldkampioen" value="Frankrijk" helper="De AI ziet Frankrijk als meest complete ploeg." />
            <BonusCard label="Topscorer" value="Kylian Mbappé" helper="Meeste verwachte goals in de knock-outfase." />
          </div>
        </div>
      </div>
    </section>
  );
}

function BonusCard({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <article className="bonus-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </article>
  );
}
