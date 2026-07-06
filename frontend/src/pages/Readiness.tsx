import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { Readiness as ReadinessType, ReadinessCheck } from "../types";

const statusLabels: Record<ReadinessCheck["status"], string> = {
  ok: "U redu",
  warning: "Provjeriti",
  critical: "Blokirano"
};

const overallLabels: Record<ReadinessType["status"], string> = {
  ready_for_demo: "Spremno za demo",
  attention_needed: "Potrebna provjera",
  blocked: "Blokirano"
};

export function Readiness() {
  const readiness = useApi<ReadinessType | null>("/api/readiness", null);
  const data = readiness.data;
  const checkRows = data?.checks.map((check, index) => ({ ...check, id: index + 1 })) ?? [];

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1>
            Spremnost <HelpHint title="Spremnost">Pregled demo sigurnosti, osnovnih podataka, audita, fiskalizacije, zalihe i otvorenih operativnih stavki.</HelpHint>
          </h1>
          <p>Jedan pregled koji pomaze prije pilot prolaza. Ne mijenja podatke.</p>
        </div>
        {data && <span className={`readiness-pill readiness-${data.status}`}>{overallLabels[data.status]}</span>}
      </div>

      {readiness.error && <p className="form-error">{readiness.error}</p>}
      {readiness.loading && <p>Ucitavanje spremnosti...</p>}

      {data && (
        <>
          <div className="metrics">
            <div><span>U redu</span><strong>{data.summary.ok}</strong></div>
            <div><span>Provjeriti</span><strong>{data.summary.warning}</strong></div>
            <div><span>Blokirano</span><strong>{data.summary.critical}</strong></div>
            <div><span>Fiskalizacija</span><strong>{data.fiscalization_mode}</strong></div>
          </div>

          <section className="workflow-panel">
            <h2>Sigurnosni kontekst</h2>
            <div className="detail-list">
              <p><span>Demo nacin</span><strong>{data.demo_mode ? "Da" : "Ne"}</strong></p>
              <p><span>Stvarni podaci dopusteni</span><strong>{data.real_data_allowed ? "Da" : "Ne"}</strong></p>
              <p><span>Ukupni status</span><strong>{overallLabels[data.status]}</strong></p>
            </div>
          </section>

          <section className="workflow-panel">
            <h2>Provjere</h2>
            <DataTable rows={checkRows} columns={[
              { header: "Podrucje", render: (row) => row.label },
              { header: "Status", render: (row) => <span className={`readiness-badge readiness-check-${row.status}`}>{statusLabels[row.status]}</span> },
              { header: "Broj", render: (row) => row.count ?? "-" },
              { header: "Poruka", render: (row) => row.message },
              { header: "Sljedeci korak", render: (row) => row.action ?? "-" }
            ]} />
          </section>
        </>
      )}
    </section>
  );
}
