import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

export type JourneyContextTab = "summary" | "timeline" | "documents" | "laboratory" | "therapies";
const tabs: Array<{ key: JourneyContextTab; label: string }> = [
  { key: "summary", label: "Sažetak" }, { key: "timeline", label: "Vremenska crta" }, { key: "documents", label: "Dokumenti" },
  { key: "laboratory", label: "Laboratorij" }, { key: "therapies", label: "Terapije" },
];

type JourneyClinicalContextProps = {
  summary: ReactNode;
  timeline: ReactNode;
  documents: ReactNode;
  onOpenChange?: (open: boolean) => void;
  onTabChange?: (tab: JourneyContextTab) => void;
};

export function JourneyClinicalContext({ summary, timeline, documents, onOpenChange, onTabChange }: JourneyClinicalContextProps) {
  const [active, setActive] = useState<JourneyContextTab>("summary");

  function selectTab(tab: JourneyContextTab) {
    setActive(tab);
    onTabChange?.(tab);
  }

  return (
    <details className="journey-clinical-context" onToggle={(event) => onOpenChange?.(event.currentTarget.open)}>
      <summary>Klinički kontekst</summary>
      <div className="journey-context-tabs" role="tablist" aria-label="Klinički kontekst">
        {tabs.map(item => <button type="button" role="tab" aria-selected={active === item.key} key={item.key} onClick={() => selectTab(item.key)}>{item.label}</button>)}
      </div>
      <div role="tabpanel" tabIndex={0}>
        {active === "summary" && summary}
        {active === "timeline" && timeline}
        {active === "documents" && documents}
        {active === "laboratory" && <p className="journey-context-link">Laboratorijski modul ostaje dostupan bez dupliciranja sadržaja. <Link to="/laboratory">Otvori laboratorij</Link></p>}
        {active === "therapies" && <p className="journey-context-link">Terapije ostaju u longitudinalnom zapisu. <Link to="/therapies">Otvori terapije</Link></p>}
      </div>
    </details>
  );
}
