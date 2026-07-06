import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { HelpHint } from "../components/HelpHint";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { useApi } from "../hooks/useApi";
import { AuditLog, ClinicalDocument } from "../types";
import { formatDate, formatDateTime } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";
import { documentTypeLabel, reviewStatusLabel, sourceTypeLabel } from "./ClinicalDocuments";

export function ClinicalDocumentDetail() {
  const { id } = useParams();
  const document = useApi<ClinicalDocument | null>(`/api/clinical-documents/${id}`, null);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=ClinicalDocument&entity_id=${id}`, []);
  const [rawText, setRawText] = useState("");
  const [summaryDraft, setSummaryDraft] = useState("");
  const [findingsDraft, setFindingsDraft] = useState("");
  const [recommendationsDraft, setRecommendationsDraft] = useState("");

  useEffect(() => {
    if (!document.data) return;
    setRawText(document.data.raw_text ?? "");
    setSummaryDraft(document.data.ai_summary ?? "");
    setFindingsDraft((document.data.key_findings ?? []).join("\n"));
    setRecommendationsDraft((document.data.recommendations ?? []).join("\n"));
  }, [document.data?.id, document.data?.updated_at]);

  async function refresh(updated: ClinicalDocument) {
    document.setData(updated);
    audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=ClinicalDocument&entity_id=${id}`));
  }

  async function updateText() {
    if (!document.data) return;
    await refresh(await api<ClinicalDocument>(`/api/clinical-documents/${document.data.id}`, { method: "PATCH", body: JSON.stringify({ raw_text: rawText }) }));
  }

  async function runExtraction() {
    if (!document.data) return;
    await refresh(await api<ClinicalDocument>(`/api/clinical-documents/${document.data.id}/extract`, { method: "POST" }));
  }

  async function saveExtractionEdits() {
    if (!document.data) return;
    await refresh(await api<ClinicalDocument>(`/api/clinical-documents/${document.data.id}`, {
      method: "PATCH",
      body: JSON.stringify({
        ai_summary: summaryDraft || null,
        key_findings: findingsDraft.split("\n").map((item) => item.trim()).filter(Boolean),
        recommendations: recommendationsDraft.split("\n").map((item) => item.trim()).filter(Boolean)
      })
    }));
  }

  async function review() {
    if (!document.data) return;
    await refresh(await api<ClinicalDocument>(`/api/clinical-documents/${document.data.id}/review`, { method: "POST" }));
  }

  async function rejectSummary() {
    if (!document.data) return;
    await refresh(await api<ClinicalDocument>(`/api/clinical-documents/${document.data.id}/reject-summary`, { method: "POST" }));
  }

  if (document.loading || !document.data) return <WorkspaceLayout><p>Ucitavanje dokumenta...</p></WorkspaceLayout>;
  const current = document.data;

  return (
    <WorkspaceLayout>
      <WorkspaceHeader
        title={current.title}
        subtitle={`${documentTypeLabel(current.document_type)} / ${sourceTypeLabel(current.source_type)} / ${formatDate(current.document_date)}`}
        badge={<span className={`readiness-badge ${current.review_status === "reviewed" ? "readiness-check-ok" : "readiness-check-warning"}`}>{reviewStatusLabel(current.review_status)}</span>}
        actions={
          <>
            <ActionButton variant="ai" onClick={runExtraction} helpTitle="AI ekstrakcija" help="Pokrece placeholder ekstrakciju iz teksta. Rezultat nije sluzben dok ga lijecnik ne pregleda.">
              AI ekstrakcija
            </ActionButton>
            <ActionButton variant="update" onClick={review} helpTitle="Potvrdi pregled" help="Oznacava dokument kao lijecnicki pregledan. Tek tada njegove stavke ulaze u pacijentov sazetak znanja.">
              Potvrdi pregled
            </ActionButton>
            <ActionButton variant="danger" requiresConfirm confirmMessage="Odbiti AI sazetak dokumenta?" onClick={rejectSummary} helpTitle="Odbij sazetak" help="Uklanja AI sazetak i strukturirane stavke iz dokumenta.">
              Odbij sazetak
            </ActionButton>
          </>
        }
      />

      <WorkspaceSection title={<>Izvor <HelpHint title="Izvor dokumenta">Svaka AI tvrdnja u sazetku pacijenta mora voditi do izvornog dokumenta.</HelpHint></>}>
        <div className="detail-list">
          <p><span>Pacijent</span><strong>{current.patient ? <Link to={`/patients/${current.patient_id}`}>{formatPatientName(current.patient)}</Link> : current.patient_id}</strong></p>
          <p><span>Origin</span><strong>{current.origin ?? "-"}</strong></p>
          <p><span>Ustanova</span><strong>{current.institution ?? "-"}</strong></p>
          <p><span>Autor</span><strong>{current.author ?? "-"}</strong></p>
          <p><span>Datoteka</span><strong>{current.attachment_path ?? "Nema datoteke"}</strong></p>
          <p><span>Pregledano</span><strong>{current.reviewed_at ? formatDateTime(current.reviewed_at) : "-"}</strong></p>
        </div>
      </WorkspaceSection>

      <div className="dashboard-grid">
        <WorkspaceSection title="Strukturirano znanje">
          <div className="clinical-plan-card ai-suggestion">
            <div><span>AI prijedlog, nije sluzbeno dok lijecnik ne potvrdi</span><strong>{reviewStatusLabel(current.review_status)}</strong></div>
            <label>AI sazetak<textarea rows={4} value={summaryDraft} onChange={(event) => setSummaryDraft(event.target.value)} /></label>
            <label>Kljucni nalazi<textarea rows={5} value={findingsDraft} onChange={(event) => setFindingsDraft(event.target.value)} placeholder="Jedna stavka po retku" /></label>
            <label>Preporuke<textarea rows={5} value={recommendationsDraft} onChange={(event) => setRecommendationsDraft(event.target.value)} placeholder="Jedna stavka po retku" /></label>
            <div className="quick-actions">
              <ActionButton variant="update" onClick={saveExtractionEdits} helpTitle="Spremi AI prijedlog" help="Sprema uredjene strukturirane stavke i vraca dokument u stanje koje ceka lijecnicku potvrdu.">
                Spremi izmjene
              </ActionButton>
            </div>
          </div>
        </WorkspaceSection>
        <WorkspaceSection title="Originalni tekst">
          <textarea rows={10} value={rawText} onChange={(event) => setRawText(event.target.value)} />
          <div className="quick-actions">
            <ActionButton variant="update" onClick={updateText} helpTitle="Spremi tekst" help="Sprema OCR ili rucno uneseni tekst i vraca dokument u status koji ceka pregled.">
              Spremi tekst
            </ActionButton>
          </div>
        </WorkspaceSection>
      </div>

      <WorkspaceSection title="Audit">
        <AuditTimeline logs={audit.data} />
      </WorkspaceSection>
    </WorkspaceLayout>
  );
}
