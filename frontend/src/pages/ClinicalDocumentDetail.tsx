import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { ClinicalDocumentAddendumOut } from "../api/generated-openapi";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { ClinicalDerivedDataNotice } from "../components/ClinicalDerivedDataNotice";
import { HelpHint } from "../components/HelpHint";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { useApi } from "../hooks/useApi";
import { AuditLog, ClinicalDocument, ClinicalEvidenceTimelineItem } from "../types";
import { formatDate, formatDateTime } from "../utils/date";
import { formatPatientName } from "../utils/patientIdentity";
import { aiExtractionStatusLabel, documentTypeLabel, recordClassificationLabel, reviewStatusLabel, sourceTypeLabel } from "./ClinicalDocuments";

function documentContributionText(document: ClinicalDocument) {
  if (document.review_status === "reviewed" && document.physician_reviewed) {
    return "Dokument je liječnički pregledan i može doprinositi pregledanom kliničkom znanju pacijenta.";
  }
  if (document.review_status === "rejected" || document.review_status === "superseded") {
    return "Dokument ne doprinosi pregledanom kliničkom znanju pacijenta.";
  }
  return "Dokument još ne doprinosi pregledanom kliničkom znanju pacijenta.";
}

function documentContributionClass(document: ClinicalDocument) {
  if (document.review_status === "reviewed" && document.physician_reviewed) return "readiness-check-ok";
  return "readiness-check-warning";
}

function knowledgeImpactLabel(value: ClinicalEvidenceTimelineItem["knowledge_impact"]) {
  const labels: Record<string, string> = {
    no_official_knowledge_impact: "Ne utječe na pregledano kliničko znanje",
    may_enable_official_knowledge: "Može doprinijeti kliničkom znanju nakon pregleda",
    removed_from_official_knowledge: "Uklonjeno iz pregledanog kliničkog znanja",
    summary_view_only: "Samo prikaz sažetka"
  };
  return labels[value] ?? value;
}

function evidenceActorLabel(item: ClinicalEvidenceTimelineItem) {
  if (item.actor_type === "api_key") return `API kljuc${item.actor_api_key_id ? ` #${item.actor_api_key_id}` : ""}`;
  if (item.actor_user_id) return `Korisnik #${item.actor_user_id}`;
  return item.actor_type ?? "Sustav";
}

export function ClinicalDocumentDetail() {
  const { id } = useParams();
  const document = useApi<ClinicalDocument | null>(`/api/clinical-documents/${id}`, null);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=ClinicalDocument&entity_id=${id}`, []);
  const evidenceTimeline = useApi<ClinicalEvidenceTimelineItem[]>(`/api/clinical-documents/${id}/evidence-timeline`, []);
  const addenda = useApi<ClinicalDocumentAddendumOut[]>(`/api/clinical-documents/${id}/addenda`, []);
  const [rawText, setRawText] = useState("");
  const [summaryDraft, setSummaryDraft] = useState("");
  const [findingsDraft, setFindingsDraft] = useState("");
  const [recommendationsDraft, setRecommendationsDraft] = useState("");
  const [addendumReason, setAddendumReason] = useState("");
  const [addendumContent, setAddendumContent] = useState("");
  const [addendumMessage, setAddendumMessage] = useState("");

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
    evidenceTimeline.setData(await api<ClinicalEvidenceTimelineItem[]>(`/api/clinical-documents/${id}/evidence-timeline`));
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

  async function createAddendum() {
    if (!document.data) return;
    const created = await api<ClinicalDocumentAddendumOut>(`/api/clinical-documents/${document.data.id}/addenda`, {
      method: "POST",
      body: JSON.stringify({ reason: addendumReason, content: addendumContent })
    });
    addenda.setData([...addenda.data, created]);
    setAddendumReason("");
    setAddendumContent("");
    setAddendumMessage("Dopuna je spremljena kao odvojeni potpisani zapis. Originalni dokument nije promijenjen.");
    audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=ClinicalDocument&entity_id=${id}`));
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
            {current.can_review && <>
              <ActionButton variant="ai" onClick={runExtraction} helpTitle="Pokreni AI ekstrakciju" help="Pokrece placeholder ekstrakciju iz teksta. Rezultat je samo prijedlog i nije sluzben dok ga lijecnik ne pregleda.">
                Pokreni AI ekstrakciju
              </ActionButton>
              <ActionButton variant="update" onClick={review} helpTitle="Potvrdi lijecnicki pregled" help="Oznacava dokument kao lijecnicki pregledan. Tek tada dokument moze postati izvor za Patient Clinical Knowledge.">
                Potvrdi lijecnicki pregled
              </ActionButton>
              <ActionButton variant="danger" requiresConfirm confirmMessage="Odbiti samo AI prijedlog dokumenta?" onClick={rejectSummary} helpTitle="Odbij AI prijedlog" help="Uklanja AI sazetak i strukturirane stavke. Izvorni dokument ostaje vidljiv i moze se rucno pregledati.">
                Odbij AI prijedlog
              </ActionButton>
            </>}
          </>
        }
      />

      <WorkspaceSection title={<>Izvorni dokument <HelpHint title="Izvorni dokument">Svaka AI tvrdnja u sazetku pacijenta mora voditi do izvornog dokumenta. Izvor ostaje vidljiv i kada se AI prijedlog odbije.</HelpHint></>}>
        <div className="detail-list">
          <p><span>Pacijent</span><strong>{current.patient ? <Link to={`/patients/${current.patient_id}`}>{formatPatientName(current.patient)}</Link> : current.patient_id}</strong></p>
          <p><span>Tip dokumenta</span><strong>{documentTypeLabel(current.document_type)}</strong></p>
          <p><span>Vrsta izvora</span><strong>{sourceTypeLabel(current.source_type)}</strong></p>
          <p><span>Datum dokumenta</span><strong>{formatDate(current.document_date)}</strong></p>
          <p><span>Origin</span><strong>{current.origin ?? "-"}</strong></p>
          <p><span>Ustanova</span><strong>{current.institution ?? "-"}</strong></p>
          <p><span>Autor</span><strong>{current.author ?? "-"}</strong></p>
          <p><span>Datoteka</span><strong>{current.attachment_path ?? "Nema datoteke"}</strong></p>
          <p><span>Pregledano</span><strong>{current.reviewed_at ? formatDateTime(current.reviewed_at) : "-"}</strong></p>
          <p><span>Status pregleda</span><strong>{reviewStatusLabel(current.review_status)}</strong></p>
          <p><span>Klasifikacija</span><strong>{recordClassificationLabel(current.record_classification)}</strong></p>
          <p><span>Klinički karton</span><strong>{current.is_clinical_record === false ? "Ne" : "Da"}</strong></p>
          <p><span>Status AI ekstrakcije</span><strong>{aiExtractionStatusLabel(current.ai_extraction_status)}</strong></p>
        </div>
      </WorkspaceSection>

      <WorkspaceSection title={<>Liječnički pregled <HelpHint title="Liječnički pregled">Pregled označava da izvor može doprinositi pregledanom kliničkom znanju. Ne donosi medicinsku odluku automatski.</HelpHint></>}>
        <div className={`clinical-plan-card ${documentContributionClass(current)}`}>
          <div>
            <span>Doprinos pregledanom kliničkom znanju</span>
            <strong>{documentContributionText(current)}</strong>
          </div>
          <p><span>Status pregleda</span><strong>{reviewStatusLabel(current.review_status)}</strong></p>
          <p><span>Pregledao</span><strong>{current.reviewed_by ?? "-"}</strong></p>
          <p><span>Vrijeme pregleda</span><strong>{current.reviewed_at ? formatDateTime(current.reviewed_at) : "-"}</strong></p>
          <p><span>Pravilo</span><strong>Izvor istine ostaje pregledani izvorni klinički dokument.</strong></p>
        </div>
      </WorkspaceSection>

      {(addenda.loading || addenda.data.length > 0 || current.can_add_addendum) && (
        <WorkspaceSection title={<>Dopuna dokumenta <HelpHint title="Dopuna dokumenta">Potpisani ili završni dokument se ne mijenja. Dopuna se sprema kao odvojeni zapis s razlogom i autorom.</HelpHint></>}>
          <div className="clinical-plan-card">
            <p><span>Pravilo</span><strong>Original ostaje nepromjenjiv; dopuna je odvojeni auditirani zapis.</strong></p>
            <div aria-label="Postojeće dopune dokumenta" className="timeline">
              {addenda.data.map((addendum) => (
                <article key={addendum.id}>
                  <strong>{addendum.reason}</strong>
                  <span>{formatDateTime(addendum.signed_at ?? addendum.created_at)} / autor #{addendum.author_user_id}</span>
                  <p>{addendum.content}</p>
                </article>
              ))}
              {!addenda.loading && addenda.data.length === 0 && <p>Nema dopuna dokumenta.</p>}
            </div>
            {current.can_add_addendum && <>
              {addendumMessage && <p className="success-text">{addendumMessage}</p>}
              <label>Razlog dopune<input value={addendumReason} onChange={(event) => setAddendumReason(event.target.value)} placeholder="Npr. administrativna ispravka ili dodatno pojašnjenje" /></label>
              <label>Sadržaj dopune<textarea rows={4} value={addendumContent} onChange={(event) => setAddendumContent(event.target.value)} /></label>
              <div className="quick-actions">
                <ActionButton variant="update" onClick={createAddendum} disabled={addendumReason.trim().length < 2 || addendumContent.trim().length < 2} helpTitle="Spremi dopunu" help="Sprema dopunu bez izmjene originalnog kliničkog dokumenta.">
                  Spremi dopunu
                </ActionButton>
              </div>
            </>}
          </div>
        </WorkspaceSection>
      )}

      <div className="dashboard-grid">
        <WorkspaceSection title={<>AI prijedlog ekstrakcije <HelpHint title="AI prijedlog ekstrakcije">Ovo je prijedlog za strukturiranje dokumenta. Nije sluzbena klinicka cinjenica dok lijecnik ne pregleda dokument.</HelpHint></>}>
          <div className="clinical-plan-card ai-suggestion">
            <ClinicalDerivedDataNotice level="context" title="AI prijedlog ekstrakcije" />
            <div><span>AI prijedlog ekstrakcije</span><strong>{aiExtractionStatusLabel(current.ai_extraction_status)}</strong></div>
            {current.ai_extraction_status === "rejected" && <p><span>Napomena</span><strong>AI prijedlog je odbijen. Izvorni dokument ostaje dostupan za rucni pregled.</strong></p>}
            <div><span>Lijecnicki pregled dokumenta</span><strong>{reviewStatusLabel(current.review_status)}</strong></div>
            <div><span>Zadnja AI izmjena</span><strong>{current.ai_extraction_updated_at ? formatDateTime(current.ai_extraction_updated_at) : "-"}</strong></div>
            <label>AI sazetak<textarea rows={4} readOnly={!current.can_edit} value={summaryDraft} onChange={(event) => setSummaryDraft(event.target.value)} /></label>
            <label>Kljucni nalazi<textarea rows={5} readOnly={!current.can_edit} value={findingsDraft} onChange={(event) => setFindingsDraft(event.target.value)} placeholder="Jedna stavka po retku" /></label>
            <label>Preporuke<textarea rows={5} readOnly={!current.can_edit} value={recommendationsDraft} onChange={(event) => setRecommendationsDraft(event.target.value)} placeholder="Jedna stavka po retku" /></label>
            {current.can_edit && <div className="quick-actions">
              <ActionButton variant="update" onClick={saveExtractionEdits} helpTitle="Spremi AI prijedlog" help="Sprema uredjene strukturirane stavke i vraca dokument u stanje koje ceka lijecnicku potvrdu.">
                Spremi izmjene
              </ActionButton>
            </div>}
          </div>
        </WorkspaceSection>
        <WorkspaceSection title={<>Izvorni tekst <HelpHint title="Izvorni tekst">Ovdje je OCR placeholder ili rucno uneseni tekst izvora. Spremanje teksta vraca dokument na pregled.</HelpHint></>}>
          <textarea aria-label="Izvorni tekst dokumenta" rows={10} readOnly={!current.can_edit} value={rawText} onChange={(event) => setRawText(event.target.value)} placeholder="Nema tekstualnog sadrzaja. Datoteka/OCR spremanje je jos placeholder." />
          {current.can_edit && <div className="quick-actions">
            <ActionButton variant="update" onClick={updateText} helpTitle="Spremi tekst" help="Sprema OCR ili rucno uneseni tekst i vraca dokument u status koji ceka pregled.">
              Spremi tekst
            </ActionButton>
          </div>}
        </WorkspaceSection>
      </div>

      <WorkspaceSection title={<>Klinicki evidence timeline <HelpHint title="Klinicki evidence timeline">Ovo je citljiv prikaz audit dogadjaja vezanih uz ovaj dokument. Ne stvara nove klinicke cinjenice.</HelpHint></>}>
        <div className="timeline">
          {evidenceTimeline.data.map((item) => (
            <article key={item.id}>
              <strong>{item.clinical_event_label}</strong>
              <span>{formatDateTime(item.created_at)} / {evidenceActorLabel(item)}</span>
              <p>{item.message ?? "-"}</p>
              <p><span>Knowledge ucinak</span><strong>{knowledgeImpactLabel(item.knowledge_impact)}</strong></p>
            </article>
          ))}
          {evidenceTimeline.data.length === 0 && <p>Nema audit dogadjaja za ovaj dokument.</p>}
        </div>
        <p><Link to="/audit-log">Otvori sirovi Audit Log</Link></p>
      </WorkspaceSection>

      <WorkspaceSection title="Audit">
        <AuditTimeline logs={audit.data} />
      </WorkspaceSection>
    </WorkspaceLayout>
  );
}
