import { AlertTriangle, CheckCircle2, ClipboardCheck, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { DateInput } from "../DateInput";
import type { PatientJourneyDetail } from "../../types/program2";

type ReceptionStep = "identity" | "red_flags";
type PatientDraft = { first_name: string; last_name: string; date_of_birth: string; oib: string; phone: string; email: string; notes: string };
type RedFlagKey = "laboratory_results" | "anesthesia_questionnaire" | "informed_consent" | "fasting_6h" | "bowel_preparation_clear" | "sedation_escort" | "pacemaker" | "current_medication" | "drug_allergies" | "other_medical_review";
type RedFlagDraft = Record<RedFlagKey, { active: boolean; note: string; details: Record<string, string>; activityIds: number[] }>;

const redFlagItems: Array<{ key: RedFlagKey; label: string; hint: string; defaultNote: string; scope: "shared" | "activity" }> = [
  { key: "laboratory_results", label: "Nedostaju nalazi koje treba vidjeti prije postupka", hint: "Nalazi koje pacijent donosi pregledavaju se kod liječnika; označiti samo ako nedostaje baš preduvjet.", defaultNote: "Potrebni nalazi nisu dostupni u prijemu.", scope: "activity" },
  { key: "anesthesia_questionnaire", label: "Anesteziološki upitnik nije spreman", hint: "Odnosi se na postupke sa sedacijom/anestezijom.", defaultNote: "Anesteziološki upitnik nije potvrđen u prijemu.", scope: "activity" },
  { key: "informed_consent", label: "Privola ili informirani pristanak nije potvrđen", hint: "Recepcija bilježi činjenicu; odluka ostaje medicinska/organizacijska.", defaultNote: "Privola ili informirani pristanak nije potvrđen u prijemu.", scope: "activity" },
  { key: "fasting_6h", label: "Problem s postom", hint: "Zabilježite kada i što je pacijent zadnje uzeo.", defaultNote: "Post od 6 sati nije potvrđen.", scope: "activity" },
  { key: "bowel_preparation_clear", label: "Priprema crijeva nije uredna", hint: "Za kolonoskopiju: npr. stolica nije bistra.", defaultNote: "Priprema crijeva nije potvrđena kao uredna.", scope: "activity" },
  { key: "sedation_escort", label: "Nema pratnju nakon sedacije", hint: "Označiti kada je sedacija planirana, a pratnja nije potvrđena.", defaultNote: "Pratnja nakon sedacije nije potvrđena.", scope: "activity" },
  { key: "pacemaker", label: "Pacijent navodi elektrostimulator ili implantat", hint: "Označiti samo kada pacijent to navodi.", defaultNote: "Pacijent navodi elektrostimulator ili implantat.", scope: "shared" },
  { key: "current_medication", label: "Terapija zahtijeva medicinsku provjeru", hint: "Kratko upišite terapiju koju pacijent navodi.", defaultNote: "Pacijent navodi terapiju koja zahtijeva medicinsku provjeru.", scope: "shared" },
  { key: "drug_allergies", label: "Pacijent navodi alergiju na lijekove", hint: "Kratko upišite lijek ili reakciju.", defaultNote: "Pacijent navodi alergiju na lijekove.", scope: "shared" },
  { key: "other_medical_review", label: "Druga napomena za liječnika/anesteziologa", hint: "Za činjenicu koja nije pokrivena gornjim stavkama.", defaultNote: "Druga prijemna napomena za liječničku provjeru.", scope: "shared" },
];

function emptyFlags(): RedFlagDraft {
  return Object.fromEntries(redFlagItems.map((item) => [item.key, { active: false, note: item.defaultNote, details: {}, activityIds: [] }])) as unknown as RedFlagDraft;
}

function patientDraftFromJourney(journey: PatientJourneyDetail): PatientDraft {
  return {
    first_name: journey.patient.first_name ?? "",
    last_name: journey.patient.last_name ?? "",
    date_of_birth: journey.patient.date_of_birth ?? "",
    oib: journey.patient.oib ?? "",
    phone: journey.patient.phone ?? "",
    email: journey.patient.email ?? "",
    notes: journey.patient.notes ?? "",
  };
}

function detailLine(key: RedFlagKey, details: Record<string, string>) {
  if (key === "fasting_6h") return [details.last_intake_timing, details.intake_type].filter(Boolean).join(" · ");
  if (key === "bowel_preparation_clear") return details.stool_clarity || "";
  if (key === "sedation_escort") return details.escort_status || "";
  if (key === "pacemaker") return details.device_type || "";
  return "";
}

export function ReceptionFloatingModal({ journeyId, open, onClose, onCompleted }: { journeyId: number | null; open: boolean; onClose: () => void; onCompleted: () => void | Promise<void> }) {
  const [journey, setJourney] = useState<PatientJourneyDetail | null>(null);
  const [draft, setDraft] = useState<PatientDraft | null>(null);
  const [initialDraft, setInitialDraft] = useState<PatientDraft | null>(null);
  const [flags, setFlags] = useState<RedFlagDraft>(() => emptyFlags());
  const [step, setStep] = useState<ReceptionStep>("identity");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmClose, setConfirmClose] = useState(false);
  const [completionIdempotencyKey, setCompletionIdempotencyKey] = useState("");
  const selectedFlags = useMemo(() => redFlagItems.filter((item) => flags[item.key]?.active), [flags]);
  const dirty = useMemo(() => {
    if (!open) return false;
    const identityDirty = Boolean(draft && initialDraft && JSON.stringify(draft) !== JSON.stringify(initialDraft));
    const flagDirty = selectedFlags.length > 0 || step === "red_flags";
    return identityDirty || flagDirty;
  }, [draft, initialDraft, open, selectedFlags.length, step]);

  useEffect(() => {
    if (!open || journeyId == null) return;
    let alive = true;
    setLoading(true); setError(null); setStep("identity"); setFlags(emptyFlags()); setConfirmClose(false);
    setCompletionIdempotencyKey(`reception-${journeyId}-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    api<PatientJourneyDetail>(`/api/patient-journeys/${journeyId}`, { suppressErrorToast: true })
      .then((result) => {
        if (!alive) return;
        const nextDraft = patientDraftFromJourney(result);
        setJourney(result); setDraft(nextDraft); setInitialDraft(nextDraft);
      })
      .catch((err) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [open, journeyId]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === "Escape" && !saving) requestClose(); };
    const onBeforeUnload = (event: BeforeUnloadEvent) => { if (!dirty) return; event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => { window.removeEventListener("keydown", onKeyDown); window.removeEventListener("beforeunload", onBeforeUnload); };
  }, [dirty, open, saving]);

  if (!open || journeyId == null) return null;

  function requestClose() {
    if (dirty) setConfirmClose(true);
    else onClose();
  }

  async function savePatient() {
    if (!journey || !draft) return;
    const payload: Partial<PatientDraft> = {};
    for (const key of ["first_name", "last_name", "date_of_birth", "oib", "phone", "email", "notes"] as const) {
      if (!initialDraft || draft[key] !== initialDraft[key]) payload[key] = draft[key] || "";
    }
    if (Object.keys(payload).length) {
      await api(`/api/patients/${journey.patient_id}`, {
        method: "PATCH",
        body: JSON.stringify({
          ...payload,
          date_of_birth: payload.date_of_birth === "" ? null : payload.date_of_birth,
          oib: payload.oib === "" ? null : payload.oib,
          phone: payload.phone === "" ? null : payload.phone,
          email: payload.email === "" ? null : payload.email,
          notes: payload.notes === "" ? null : payload.notes,
        }),
      });
    }
    setInitialDraft(draft);
  }

  async function confirmIdentity() {
    if (!journey || !draft) return;
    setSaving(true); setError(null);
    try {
      await savePatient();
      await api(`/api/patient-journeys/${journeyId}/check-in`, { method: "POST" });
      setStep("red_flags");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prijem nije spremljen.");
    } finally {
      setSaving(false);
    }
  }

  async function completeReception(closeAfter = false) {
    setSaving(true); setError(null);
    try {
      await api(`/api/patient-journeys/${journeyId}/check-in/complete-reception`, {
        method: "POST",
        body: JSON.stringify({
          idempotency_key: completionIdempotencyKey,
          items: selectedFlags.map((item) => {
            const state = flags[item.key];
            const extra = detailLine(item.key, state.details);
            return { item_key: item.key, note: [state.note || item.defaultNote, extra].filter(Boolean).join(" — "), details: state.details, activity_ids: state.activityIds };
          }),
        }),
      });
      setConfirmClose(false);
      if (closeAfter) onClose();
      else await onCompleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prijem nije dovršen.");
    } finally {
      setSaving(false);
    }
  }

  async function saveAndClose() {
    setSaving(true); setError(null);
    try {
      if (step === "identity") await savePatient();
      else await completeReception(true);
      if (step === "identity") onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Promjene nisu spremljene.");
    } finally {
      setSaving(false);
    }
  }

  function updateDraft(key: keyof PatientDraft, value: string) { setDraft((current) => current ? { ...current, [key]: value } : current); }
  function toggleFlag(key: RedFlagKey, active: boolean) { setFlags((current) => ({ ...current, [key]: { ...current[key], active } })); }
  function updateFlagNote(key: RedFlagKey, note: string) { setFlags((current) => ({ ...current, [key]: { ...current[key], note } })); }
  function updateFlagDetail(key: RedFlagKey, detailKey: string, value: string) { setFlags((current) => ({ ...current, [key]: { ...current[key], details: { ...current[key].details, [detailKey]: value } } })); }
  function updateFlagActivities(key: RedFlagKey, values: string[]) { setFlags((current) => ({ ...current, [key]: { ...current[key], activityIds: values.map(Number).filter(Boolean) } })); }

  const activityOptions = journey?.activities?.map((activity) => ({
    id: activity.id,
    label: `${activity.sequence}. ${activity.activity_key}`,
  })) ?? [];

  return <div className="modal-backdrop reception-native-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && requestClose()}>
    <section className="modal-panel reception-modal reception-native-modal" role="dialog" aria-modal="true" aria-labelledby="reception-native-title">
      <header className="reception-native-header">
        <div><span className="eyebrow">Prijem pacijenta</span><h2 id="reception-native-title">{step === "identity" ? "Opći podaci pacijenta" : "Kratka prijemna provjera"}</h2><p>{step === "identity" ? "Provjerite osnovne podatke. Nakon potvrde otvara se kratka lista red flagova." : "Označite samo odstupanja. Ako je sve u redu, ne treba ništa klikati."}</p></div>
        <button type="button" className="modal-close-button" onClick={requestClose} disabled={saving} aria-label="Zatvori prijem"><X size={18}/></button>
      </header>
      {loading && <p>Učitavanje prijema…</p>}
      {error && <p className="form-error">{error}</p>}
      {!loading && draft && step === "identity" && <div className="form-grid two">
        <label>Ime<input value={draft.first_name} onChange={(event) => updateDraft("first_name", event.target.value)}/></label>
        <label>Prezime<input value={draft.last_name} onChange={(event) => updateDraft("last_name", event.target.value)}/></label>
        <label>Datum rođenja<DateInput value={draft.date_of_birth} onChange={(value) => updateDraft("date_of_birth", value)}/></label>
        <label>OIB<input value={draft.oib} onChange={(event) => updateDraft("oib", event.target.value)} placeholder="Demo OIB ili prazno"/></label>
        <label>Telefon<input value={draft.phone} onChange={(event) => updateDraft("phone", event.target.value)}/></label>
        <label>E-pošta<input value={draft.email} onChange={(event) => updateDraft("email", event.target.value)}/></label>
        <label className="span-2">Recepcijska napomena<input value={draft.notes} onChange={(event) => updateDraft("notes", event.target.value)} placeholder="Ne koristiti za kliničku odluku"/></label>
      </div>}
      {!loading && step === "red_flags" && <div className="reception-native-flags">
        <div className={selectedFlags.length ? "reception-red-summary active" : "reception-red-summary"}>{selectedFlags.length ? <AlertTriangle size={18}/> : <CheckCircle2 size={18}/>}<span>{selectedFlags.length ? "Postoji crvena napomena. Pacijent se upućuje liječniku/anesteziologu na odluku." : "Nema označenih red flagova. Pacijent može čekati pregled/pretragu."}</span></div>
        {redFlagItems.map((item) => {
          const state = flags[item.key];
          return <article key={item.key} className={state.active ? "reception-flag-card active" : "reception-flag-card"}>
            <label><input type="checkbox" checked={state.active} onChange={(event) => toggleFlag(item.key, event.target.checked)}/><span><strong>{item.label}</strong><small>{item.hint}</small></span></label>
            {state.active && <div className="reception-flag-details">
              {item.scope === "activity" && activityOptions.length > 1 && <label>Odnosi se na<select aria-label="Odnosi se na aktivnost" multiple value={state.activityIds.map(String)} onChange={(event) => updateFlagActivities(item.key, Array.from(event.target.selectedOptions).map(option => option.value))}>{activityOptions.map(activity => <option key={activity.id} value={activity.id}>{activity.label}</option>)}</select><small>Ako ne odaberete aktivnost, napomena vrijedi za cijeli dolazak.</small></label>}
              {item.key === "fasting_6h" && <><label>Zadnji unos<select value={state.details.last_intake_timing ?? ""} onChange={(event) => updateFlagDetail(item.key, "last_intake_timing", event.target.value)}><option value="">Odaberite</option><option value="manje od 2 sata">manje od 2 sata</option><option value="2–4 sata">2–4 sata</option><option value="4–6 sati">4–6 sati</option><option value="nepoznato">nepoznato</option></select></label><label>Vrsta unosa<select value={state.details.intake_type ?? ""} onChange={(event) => updateFlagDetail(item.key, "intake_type", event.target.value)}><option value="">Odaberite</option><option value="voda">voda</option><option value="kava ili čaj bez mlijeka">kava ili čaj bez mlijeka</option><option value="kava s mlijekom">kava s mlijekom</option><option value="hrana">hrana</option><option value="nepoznato">nepoznato</option></select></label></>}
              {item.key === "bowel_preparation_clear" && <label>Stolica prema navodu pacijenta<select value={state.details.stool_clarity ?? ""} onChange={(event) => updateFlagDetail(item.key, "stool_clarity", event.target.value)}><option value="">Odaberite</option><option value="bistra">bistra</option><option value="nije bistra">nije bistra</option><option value="ne može procijeniti">ne može procijeniti</option></select></label>}
              {item.key === "sedation_escort" && <label>Pratnja<select value={state.details.escort_status ?? ""} onChange={(event) => updateFlagDetail(item.key, "escort_status", event.target.value)}><option value="">Odaberite</option><option value="nije osigurana">nije osigurana</option><option value="dolazi kasnije">dolazi kasnije</option><option value="nejasno">nejasno</option></select></label>}
              {item.key === "pacemaker" && <label>Uređaj<select value={state.details.device_type ?? ""} onChange={(event) => updateFlagDetail(item.key, "device_type", event.target.value)}><option value="">Odaberite</option><option value="elektrostimulator">elektrostimulator</option><option value="ICD">ICD</option><option value="drugi implantat">drugi implantat</option><option value="nepoznato">nepoznato</option></select></label>}
              <label>Kratka napomena<textarea aria-label={`${item.label} - napomena`} value={state.note} onChange={(event) => updateFlagNote(item.key, event.target.value)} /></label>
            </div>}
          </article>;
        })}
      </div>}
      <footer className="reception-native-footer">
        <button type="button" onClick={requestClose} disabled={saving}>Odustani</button>
        {step === "identity" ? <button type="button" onClick={confirmIdentity} disabled={saving || loading || !draft}><ClipboardCheck size={16}/>{saving ? "Spremam…" : "Podaci su točni"}</button> : <button type="button" onClick={() => completeReception(false)} disabled={saving || loading}><ClipboardCheck size={16}/>{saving ? "Spremam…" : "Provjereno"}</button>}
      </footer>
    </section>
    {confirmClose && <section className="modal-panel reception-discard-dialog" role="dialog" aria-modal="true" aria-labelledby="reception-discard-title" onMouseDown={(event) => event.stopPropagation()}>
      <h2 id="reception-discard-title">Nespremljene promjene</h2>
      <p>Želite li spremiti promjene prije zatvaranja prijema?</p>
      <footer><button type="button" onClick={() => setConfirmClose(false)}>Ostani</button><button type="button" onClick={() => { setConfirmClose(false); onClose(); }}>Odbaci promjene</button><button type="button" className="primary" disabled={saving} onClick={saveAndClose}>Spremi i zatvori</button></footer>
    </section>}
  </div>;
}
