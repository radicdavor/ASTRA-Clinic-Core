import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

type ContextTab = "summary" | "timeline" | "documents" | "laboratory" | "therapies";
const tabs: Array<{ key: ContextTab; label: string }> = [
  { key: "summary", label: "Sažetak" }, { key: "timeline", label: "Vremenska crta" }, { key: "documents", label: "Dokumenti" },
  { key: "laboratory", label: "Laboratorij" }, { key: "therapies", label: "Terapije" },
];

export function JourneyClinicalContext({ summary, timeline, documents }: { summary: ReactNode; timeline: ReactNode; documents: ReactNode }) {
  const [active, setActive] = useState<ContextTab>("summary");
  return <details className="journey-clinical-context"><summary>Klinički kontekst</summary><div className="journey-context-tabs" role="tablist" aria-label="Klinički kontekst">{tabs.map(item => <button type="button" role="tab" aria-selected={active === item.key} key={item.key} onClick={() => setActive(item.key)}>{item.label}</button>)}</div><div role="tabpanel" tabIndex={0}>{active === "summary" && summary}{active === "timeline" && timeline}{active === "documents" && documents}{active === "laboratory" && <p className="journey-context-link">Laboratorijski modul ostaje dostupan bez dupliciranja sadržaja. <Link to="/laboratory">Otvori laboratorij</Link></p>}{active === "therapies" && <p className="journey-context-link">Terapije ostaju u longitudinalnom zapisu. <Link to="/therapies">Otvori terapije</Link></p>}</div></details>;
}
