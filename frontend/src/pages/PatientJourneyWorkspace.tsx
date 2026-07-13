import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import { AISummaryPanel, BillingPanel, BlockerPanel, CheckInChecklist, ConsumablesPanel, DocumentReadinessPanel, EncounterPanel, PatientTimeline, PaymentPanel, PreparationPanel, SourceDocumentViewer } from "../components/program2/Program2Panels";

export function PatientJourneyWorkspace() {
  const { id } = useParams();
  const journey = useApi<any>(`/api/patient-journeys/${id}`, null);
  const timeline = useApi<any[]>(`/api/patient-journeys/${id}/timeline`, []);
  const summary = useApi<any>(`/api/patient-journeys/${id}/summary`, null);
  const checkin = useApi<any>(`/api/patient-journeys/${id}/check-in`, null);
  const encounter = useApi<any>(`/api/patient-journeys/${id}/encounter`, null);
  const closure = useApi<any>(`/api/patient-journeys/${id}/closure`, null);
  const documents = useApi<any[]>(`/api/clinical-documents?patient_id=${journey.data?.patient_id ?? 0}`, []);
  const [draft, setDraft] = useState<any>({});
  useEffect(() => { if (encounter.data) setDraft(encounter.data); }, [encounter.data]);
  if (!journey.data) return <section className="page"><p>Učitavanje tijeka pacijenta...</p></section>;
  const j = journey.data;
  async function refresh() { journey.setData(await api(`/api/patient-journeys/${id}`)); closure.setData(await api(`/api/patient-journeys/${id}/closure`)); }
  async function open() { encounter.setData(await api(`/api/patient-journeys/${id}/encounter`, { method: "POST" })); }
  async function save() { encounter.setData(await api(`/api/patient-journeys/${id}/encounter`, { method: "PATCH", body: JSON.stringify(draft) })); }
  async function complete() { encounter.setData(await api(`/api/patient-journeys/${id}/encounter/complete`, { method: "POST" })); await refresh(); }
  async function confirmNone() { await api(`/api/patient-journeys/${id}/consumables/confirm`, { method: "POST", body: JSON.stringify({ not_applicable: true }) }); await refresh(); }
  async function prepare() { await api(`/api/patient-journeys/${id}/billing/prepare`, { method: "POST" }); await refresh(); }
  async function pay(amount: string, method: string) { await api(`/api/patient-journeys/${id}/payments`, { method: "POST", body: JSON.stringify({ amount, method }) }); await refresh(); }
  async function defer() { const reason = window.prompt("Upišite razlog odgode plaćanja"); if (reason) { await api(`/api/patient-journeys/${id}/payments/defer`, { method: "POST", body: JSON.stringify({ reason }) }); await refresh(); } }
  async function close() { await api(`/api/patient-journeys/${id}/close`, { method: "POST" }); await refresh(); }
  return <section className="page journey-workspace">
    <header className="journey-workspace-header"><div><span>TIJEK PACIJENTA · #{j.id}</span><h1>{j.patient.first_name} {j.patient.last_name}</h1><p>Rođen/a: {j.patient.date_of_birth ?? "nije upisano"} · termin {j.appointment.date} u {j.appointment.start_time.slice(0, 5)}</p></div><div><strong>{j.current_stage}</strong><Link to={`/appointments/${j.appointment_id}`}>Termin #{j.appointment_id}</Link></div></header>
    <div className="journey-safety-strip"><span>Dokumenti: {j.document_status}</span><span>Priprema: {j.preparation_status}</span><span>Check-in: {j.check_in_status}</span><span>Pregled: {j.encounter_status}</span></div>
    <div className="journey-columns"><aside><PatientTimeline items={timeline.data}/><SourceDocumentViewer documents={documents.data}/><AISummaryPanel summary={summary.data}/></aside><main><EncounterPanel draft={draft} setDraft={setDraft} status={encounter.data?.status} onOpen={open} onSave={save} onComplete={complete}/></main><aside><BlockerPanel items={j.blockers}/><CheckInChecklist data={checkin.data}/><DocumentReadinessPanel status={j.document_status}/><PreparationPanel status={j.preparation_status}/><ConsumablesPanel status={j.consumables_status} onConfirmNone={confirmNone}/><BillingPanel status={j.billing_status} invoice={closure.data?.invoice} onPrepare={prepare}/><PaymentPanel status={j.payment_status} invoice={closure.data?.invoice} onPay={pay} onDefer={defer} onClose={close}/></aside></div>
  </section>;
}
