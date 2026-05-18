import type { AppView } from "../../types";
import "./HeroNav.css";

type HeroNavProps = {
  activeView: AppView;
  onChange: (view: AppView) => void;
};

const NAV_ITEMS: Array<{ view: AppView; label: string }> = [
  { view: "matches", label: "Wedstrijden" },
  { view: "groups", label: "Poules" },
  { view: "knockout", label: "Knock-out" },
  { view: "crystal", label: "Crystal Ball" },
];

export function HeroNav({ activeView, onChange }: HeroNavProps) {
  return (
    <section className="hero">
      <div>
        <p className="eyebrow">Tony&apos;s Toto 2026</p>
        <h1>WK 2026 AI Toto</h1>
        <p className="lede">Overzicht van alle wedstrijden, poulestanden, knock-outschema en AI-voorspellingen.</p>
        <nav className="top-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.view}
              type="button"
              className={`top-nav-button${activeView === item.view ? " is-active" : ""}`}
              onClick={() => onChange(item.view)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </div>
    </section>
  );
}
