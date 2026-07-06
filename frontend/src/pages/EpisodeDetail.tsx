import { FormEvent, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { AuditTimeline } from "../components/AuditTimeline";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { StatusBadge } from "../components/StatusBadge";
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader";
import { WorkspaceLayout } from "../components/workspace/WorkspaceLayout";
import { WorkspaceSection } from "../components/workspace/WorkspaceSection";
import { useApi } from "../hooks/useApi";
import { Appointment, AuditLog, ClinicalDecisionTimelineItem, ClinicalEpisode, ClinicalPlan } from "../types";
import { formatDate, formatDateTime } from "../utils/date";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";
import { episodeTypeLabel } from "./Episodes";

export function EpisodeDetail() {
  const { id } = useParams();
  const episode = useApi<ClinicalEpisode | null>(`/api/episodes/${id}`, null);
  const appointments = useApi<Appointment[]>(`/api/episodes/${id}/appointments`, []);
  const plans = useApi<ClinicalPlan[]>(`/api/episodes/${id}/clinical-plans`, []);
  const decisionTimeline = useApi<ClinicalDecisionTimelineItem[]>(`/api/episodes/${id}/clinical-timeline`, []);
  const audit = useApi<AuditLog[]>(`/api/audit-log?entity_type=ClinicalEpisode&entity_id=${id}`, []);
  const [planDraft, setPlanDraft] = useState({ appointment_id: "", procedure_type: "", findings: "", pathology_ordered: false, physician_conclusion: "", episode_goal: "" });
  const [editDraft, setEditDraft] = useState({ proposed_episode_status: "waiting", next_action: "wait_for_pathology", due_date: "", priority: "important", rationale: "", suggested_follow_up: "" });
  const [editingPlanId, setEditingPlanId] = useState<number | null>(null);

  const activePlan = useMemo(() => plans.data.find((plan) => plan.status === "active" && plan.physician_confirmed), [plans.data]);
  const pendingPlan = useMemo(() => plans.data.find((plan) => !plan.physician_confirmed && ["draft", "waiting"].includes(plan.status)), [plans.data]);

  async function refreshClinicalPlanData() {
    if (!episode.data) return;
    plans.setData(await api<ClinicalPlan[]>(`/api/episodes/${episode.data.id}/clinical-plans`));
    decisionTimeline.setData(await api<ClinicalDecisionTimelineItem[]>(`/api/episodes/${episode.data.id}/clinical-timeline`));
    audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=ClinicalEpisode&entity_id=${episode.data.id}`));
  }

  async function closeEpisode() {
    if (!episode.data) return;
    const updated = await api<ClinicalEpisode>(`/api/episodes/${episode.data.id}/close`, { method: "POST" });
    episode.setData(updated);
    audit.setData(await api<AuditLog[]>(`/api/audit-log?entity_type=ClinicalEpisode&entity_id=${episode.data.id}`));
  }

  async function generatePlan(event: FormEvent) {
    event.preventDefault();
    if (!episode.data) return;
    await api<ClinicalPlan>(`/api/episodes/${episode.data.id}/clinical-plans/generate`, {
      method: "POST",
      body: JSON.stringify({ ...planDraft, appointment_id: planDraft.appointment_id ? Number(planDraft.appointment_id) : null })
    });
    setPlanDraft({ appointment_id: "", procedure_type: "", findings: "", pathology_ordered: false, physician_conclusion: "", episode_goal: "" });
    await refreshClinicalPlanData();
  }

  function startEdit(plan: ClinicalPlan) {
    setEditingPlanId(plan.id);
    setEditDraft({
      proposed_episode_status: plan.proposed_episode_status ?? "waiting",
      next_action: plan.next_action,
      due_date: plan.due_date ?? "",
      priority: plan.priority,
      rationale: plan.rationale ?? "",
      suggested_follow_up: plan.suggested_follow_up ?? ""
    });
  }

  async function savePlanEdit(event: FormEvent) {
    event.preventDefault();
    if (!editingPlanId) return;
    await api<ClinicalPlan>(`/api/clinical-plans/${editingPlanId}`, {
      method: "PATCH",
      body: JSON.stringify({ ...editDraft, due_date: editDraft.due_date || null })
    });
    setEditingPlanId(null);
    await refreshClinicalPlanData();
  }

  async function confirmPlan(plan: ClinicalPlan) {
    await api<ClinicalPlan>(`/api/clinical-plans/${plan.id}/confirm`, { method: "POST" });
    if (episode.data) {
      episode.setData(await api<ClinicalEpisode>(`/api/episodes/${episode.data.id}`));
    }
    await refreshClinicalPlanData();
  }

  async function rejectPlan(plan: ClinicalPlan) {
    await api<ClinicalPlan>(`/api/clinical-plans/${plan.id}/reject`, { method: "POST" });
    await refreshClinicalPlanData();
  }

  if (!episode.data) return <WorkspaceLayout><p>Ucitavanje epizode...</p></WorkspaceLayout>;

  const patient = episode.data.patient;
  const canClose = !["completed", "cancelled", "archived"].includes(episode.data.status);

  return (
    <WorkspaceLayout>
      <WorkspaceHeader
        title={episode.data.title}
        subtitle={
          <>
            {patient ? <Link to={`/patients/${patient.id}`}>{formatPatientName(patient)}</Link> : `Pacijent ${episode.data.patient_id}`}
            {" / "}
            {patient ? formatPatientIdentity(patient) : "Nema detalja pacijenta"}
          </>
        }
        badge={<StatusBadge status={episode.data.status} />}
        actions={
          <>
            <Link className="primary link-button" to={`/appointments/new?patient_id=${episode.data.patient_id}&episode_id=${episode.data.id}`}>Novi termin</Link>
            <ActionButton
              variant="workflow"
              disabled={!canClose}
              onClick={closeEpisode}
              requiresConfirm
              confirmMessage="Zatvoriti klinicku epizodu kao dovrsenu?"
              helpTitle="Zatvori epizodu"
              help="Postavlja status completed i datum zavrsetka ako jos nije upisan. Ne donosi medicinsku odluku."
            >
              Zatvori epizodu
            </ActionButton>
          </>
        }
      />

      <div className="summary-strip">
        <div><span>Tip</span><strong>{episodeTypeLabel(episode.data.episode_type)}</strong></div>
        <div><span>Prioritet</span><strong>{episode.data.priority ?? "-"}</strong></div>
        <div><span>Pocetak</span><strong>{formatDate(episode.data.start_date)}</strong></div>
        <div><span>Kraj</span><strong>{formatDate(episode.data.end_date)}</strong></div>
        <div><span>Voditelj</span><strong>{episode.data.owner_provider?.full_name ?? "-"}</strong></div>
      </div>

      <WorkspaceSection
        title={
          <>
            Svrha epizode <HelpHint title="Svrha epizode">Ovo je opis price i pracenja. ASTRA ovdje ne postavlja dijagnozu i ne odlucuje umjesto lijecnika.</HelpHint>
          </>
        }
      >
        <div className="detail-list">
          <p><span>Sazetak</span><strong>{episode.data.summary ?? "-"}</strong></p>
          <p><span>Klinicke biljeske</span><strong>{episode.data.clinical_notes ?? "-"}</strong></p>
        </div>
      </WorkspaceSection>

      <WorkspaceSection
        title={
          <>
            Aktivni klinicki plan <HelpHint title="Aktivni klinicki plan">Sluzbeni plan postoji samo nakon potvrde lijecnika. AI prijedlog sam po sebi nije sluzbeni plan.</HelpHint>
          </>
        }
      >
        {activePlan ? (
          <div className="clinical-plan-card active-plan">
            <div>
              <span>ACTIVE PLAN</span>
              <strong>{activePlan.rationale ?? activePlan.next_action}</strong>
            </div>
            <p><span>Sljedeca radnja</span><strong>{activePlan.next_action}</strong></p>
            <p><span>Predlozeni status epizode</span><strong>{activePlan.proposed_episode_status ?? "-"}</strong></p>
            <p><span>Kontrola / rok</span><strong>{activePlan.suggested_follow_up ?? formatDate(activePlan.due_date)}</strong></p>
            <p><span>Potvrdio</span><strong>{activePlan.confirmed_by ? `Korisnik #${activePlan.confirmed_by}` : "Lijecnik"} / {formatDateTime(activePlan.confirmed_at)}</strong></p>
          </div>
        ) : (
          <p>Nema potvrdenog klinickog plana.</p>
        )}
      </WorkspaceSection>

      <WorkspaceSection title="AI prijedlog plana">
        {pendingPlan ? (
          <div className="clinical-plan-card ai-suggestion">
            <div>
              <span>AI prijedlog</span>
              <strong>{pendingPlan.rationale ?? pendingPlan.next_action}</strong>
            </div>
            {Number(pendingPlan.ai_confidence ?? 0) < 0.7 && <p className="form-error">Manual review recommended.</p>}
            <p><span>Predlozeni status epizode</span><strong>{pendingPlan.proposed_episode_status ?? "-"}</strong></p>
            <p><span>Sljedeca radnja</span><strong>{pendingPlan.next_action}</strong></p>
            <p><span>Kontrola / rok</span><strong>{pendingPlan.suggested_follow_up ?? formatDate(pendingPlan.due_date)}</strong></p>
            <p><span>Prioritet</span><strong>{pendingPlan.priority}</strong></p>
            <p><span>Pouzdanost</span><strong>{pendingPlan.ai_confidence ? `${Math.round(Number(pendingPlan.ai_confidence) * 100)}%` : "-"}</strong></p>
            <div className="quick-actions">
              <ActionButton variant="workflow" onClick={() => confirmPlan(pendingPlan)} requiresConfirm confirmMessage="Potvrditi klinicki plan i azurirati epizodu?" helpTitle="Potvrdi plan" help="Samo potvrda lijecnika pretvara prijedlog u aktivni klinicki plan i azurira epizodu.">
                Potvrdi
              </ActionButton>
              <ActionButton variant="update" onClick={() => startEdit(pendingPlan)} helpTitle="Uredi prijedlog" help="Uredite prijedlog prije potvrde. Uredeni plan se i dalje mora posebno potvrditi.">
                Uredi
              </ActionButton>
              <ActionButton variant="danger" onClick={() => rejectPlan(pendingPlan)} requiresConfirm confirmMessage="Odbiti AI prijedlog plana?" helpTitle="Odbij prijedlog" help="Odbija prijedlog bez promjene epizode.">
                Odbij
              </ActionButton>
            </div>
          </div>
        ) : (
          <p>Nema AI prijedloga koji ceka potvrdu.</p>
        )}

        {editingPlanId && (
          <form className="form-grid clinical-plan-edit" onSubmit={savePlanEdit}>
            <label>Status epizode<select value={editDraft.proposed_episode_status} onChange={(event) => setEditDraft({ ...editDraft, proposed_episode_status: event.target.value })}><option value="open">open</option><option value="active">active</option><option value="waiting">waiting</option><option value="completed">completed</option></select></label>
            <label>Sljedeca radnja<input value={editDraft.next_action} onChange={(event) => setEditDraft({ ...editDraft, next_action: event.target.value })} /></label>
            <label>Rok<input type="date" value={editDraft.due_date} onChange={(event) => setEditDraft({ ...editDraft, due_date: event.target.value })} /></label>
            <label>Prioritet<select value={editDraft.priority} onChange={(event) => setEditDraft({ ...editDraft, priority: event.target.value })}><option value="routine">routine</option><option value="important">important</option><option value="urgent">urgent</option></select></label>
            <label className="wide-field">Razlog<textarea value={editDraft.rationale} onChange={(event) => setEditDraft({ ...editDraft, rationale: event.target.value })} rows={3} /></label>
            <label className="wide-field">Predlozeni follow-up<textarea value={editDraft.suggested_follow_up} onChange={(event) => setEditDraft({ ...editDraft, suggested_follow_up: event.target.value })} rows={3} /></label>
            <ActionButton type="submit" className="primary" variant="update" helpTitle="Spremi izmjenu" help="Sprema uredeni prijedlog, ali ga ne potvrduje automatski.">
              Spremi izmjenu
            </ActionButton>
          </form>
        )}

        <form className="form-grid clinical-plan-generate" onSubmit={generatePlan}>
          <label>Termin<select value={planDraft.appointment_id} onChange={(event) => setPlanDraft({ ...planDraft, appointment_id: event.target.value })}><option value="">Bez termina</option>{appointments.data.map((appointment) => <option key={appointment.id} value={appointment.id}>{formatDate(appointment.date)} / {appointment.service?.name ?? appointment.service_id}</option>)}</select></label>
          <label>Postupak<input value={planDraft.procedure_type} onChange={(event) => setPlanDraft({ ...planDraft, procedure_type: event.target.value })} placeholder="npr. Gastroskopija" /></label>
          <label className="wide-field">Nalazi<textarea value={planDraft.findings} onChange={(event) => setPlanDraft({ ...planDraft, findings: event.target.value })} rows={3} /></label>
          <label className="wide-field">Zakljucak lijecnika<textarea value={planDraft.physician_conclusion} onChange={(event) => setPlanDraft({ ...planDraft, physician_conclusion: event.target.value })} rows={3} /></label>
          <label className="wide-field">Cilj epizode<textarea value={planDraft.episode_goal} onChange={(event) => setPlanDraft({ ...planDraft, episode_goal: event.target.value })} rows={2} /></label>
          <label className="confirm-row"><input type="checkbox" checked={planDraft.pathology_ordered} onChange={(event) => setPlanDraft({ ...planDraft, pathology_ordered: event.target.checked })} /> Patologija zatrazena</label>
          <ActionButton type="submit" className="primary" variant="ai" helpTitle="AI prijedlog" help="AI priprema strukturirani prijedlog. Ne mijenja epizodu i ne postaje sluzbeni plan bez potvrde lijecnika.">
            Generiraj AI prijedlog
          </ActionButton>
        </form>
      </WorkspaceSection>

      <WorkspaceSection title="Timeline odluka">
        <div className="timeline">
          {decisionTimeline.data.map((item) => (
            <article key={item.id}>
              <strong>{item.label}</strong>
              <span>{formatDateTime(item.created_at)} / {item.source ?? "-"}</span>
              <p>{item.summary ?? "-"}</p>
            </article>
          ))}
          {decisionTimeline.data.length === 0 && <p>Nema klinickih odluka u timelineu.</p>}
        </div>
      </WorkspaceSection>

      <WorkspaceSection title="Povezani termini">
        <DataTable rows={appointments.data} columns={[
          { header: "Datum", render: (row) => formatDate(row.date) },
          { header: "Vrijeme", render: (row) => `${row.start_time.slice(0, 5)} - ${row.end_time.slice(0, 5)}` },
          { header: "Usluga", render: (row) => row.service?.name ?? row.service_id },
          { header: "Status", render: (row) => <StatusBadge status={row.status} /> },
          { header: "Detalj", render: (row) => <Link to={`/appointments/${row.id}`}>Otvori</Link> }
        ]} />
      </WorkspaceSection>

      <WorkspaceSection title="Nalazi i patologija">
        <p>U ovoj verziji nalazi i patologija nisu zasebni dokumenti. AI prijedlog koristi samo tekst koji lijecnik unese u obrazac prijedloga plana.</p>
      </WorkspaceSection>

      <WorkspaceSection title="Audit timeline">
        <AuditTimeline logs={audit.data} />
      </WorkspaceSection>
    </WorkspaceLayout>
  );
}
