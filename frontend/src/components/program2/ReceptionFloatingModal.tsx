import { AlertTriangle, CheckCircle2, ClipboardCheck, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { DateInput } from "../DateInput";
import type { PatientJourneyDetail } from "../../types/program2";

type ReceptionStep = "identity" | "red_flags";
type PatientDraft = {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  oib: string;
  phone: string;
  email: string;
  notes: string;
};
type RedFlagKey =
  | "laboratory_results"
  | "anesthesia_questionnaire"
  | "informed_consent"
  | "fasting_6h"
  | "bowel_preparation_clear"
  | "sedation_escort"
  | "pacemaker"
  | "current_medication"
  | "drug_allergies"
  | "other_medical_review";
type RedFlagDraft = Record<RedFlagKey, { active: boolean; note: string }>;

const redFlagItems: Array<{ key: RedFlagKey; label: string; hint: string; defaultNote: string }> = [
  { key: "laboratory_results", label: "Nedostaju potrebni laboratorijski nalazi", hint: "Ako nalaz nije dostupan, liječnik ga može pregledati ili odlučiti bez njega.", defaultNote: "Potrebni laboratorijski nalazi nisu dostupni u prijemu." },
  { key: "anesthesia_questionnaire", label: "Anesteziološki upitnik nije spreman", hint: "Vrijedi samo kada je upitnik potreban za planiranu pretragu.", defaultNote: "Anesteziološki upitnik nije potvrđen u prijemu." },
  { key: "informed_consent", label: "Privola ili informirani pristanak nije potvrđen", hint: "Recepcija bilježi činjenicu; konačnu odluku donosi ovlaštena osoba.", defaultNote: "Privola ili informirani pristanak nije potvrđen u prijemu." },
  { key: "fasting_6h", label: "Post 6 sati nije potvrđen", hint: "Upišite kada je pacijent zadnji put jeo ili pio.", defaultNote: "Post od 6 sati nije potvrđen." },
  { key: "bowel_preparation_clear", label: "Priprema crijeva nije uredna", hint: "Za kolonoskopiju: npr. stolica nije bistra.", defaultNote: "Priprema crijeva nije potvrđena kao uredna." },
  { key: "sedation_escort", label: "Nema pratnju nakon sedacije", hint: "Ako je sedacija planirana, ovo se prenosi liječniku/anesteziologu.", defaultNote: "Pratnja nakon sedacije nije potvrđena." },
  { key: "pacemaker", label: "Pacijent navodi elektrostimulator ili implantat", hint: "Označiti samo kada pacijent navodi elektrostimulator/implantat.", defaultNote: "Pacijent navodi elektrostimulator ili implantat." },
  { key: "current_medication", label: "Terapija zahtijeva medicinsku provjeru", hint: "Upišite lijekove koje pacijent navodi.", defaultNote: "Pacijent navodi terapiju koja zahtijeva medicinsku provjeru." },
  { key: "drug_allergies", label: "Pacijent navodi alergiju na lijekove", hint: "Upišite alergiju koju pacijent navodi.", defaultNote: "Pacijent navodi alergiju na lijekove." },
  { key: "other_medical_review", label: "Druga napomena za liječnika/anesteziologa", hint: "Koristiti samo za činjenicu koja nije pokrivena gornjim stavkama.", defaultNote: "Druga prijemna napomena za liječničku provjeru." },
];

function emptyFlags(): RedFlagDraft {
  return Object.fromEntries(redFlagItems.map((item) => [item.key, { active: false, note: item.defaultNote }])) as RedFlagDraft;
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

export function ReceptionFloatingModal({ journeyId, open, onClose, onCompleted }: { journeyId: number | null; open: boolean; onClose: () => void; onCompleted: () => void | Promise<void> }) {
  const [journey, setJourney] = useState<PatientJourneyDetail | null>(null);
  const [draft, setDraft] = useState<PatientDraft | null>(null);
  const [flags, setFlags] = useState<RedFlagDraft>(() => emptyFlags());
  const [step, setStep] = useState<ReceptionStep>("identity");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedFlags = useMemo(() => redFlagItems.filter((item) => flags[item.key]?.active), [flags]);

  useEffect(() => {
    if (!open || journeyId == null) return;
    let alive = true;
    setLoading(true);
    setError(null);
    setStep("identity");
    setFlags(emptyFlags());
    api<PatientJourneyDetail>(`/api/patient-journeys/${journeyId}`, { suppressErrorToast: true })
      .then((result) => {
        if (!alive) return;
        setJourney(result);
        setDraft(patientDraftFromJourney(result));
      })
      .catch((err) => alive && setError(err.message))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [open, journeyId]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !saving) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose, saving]);

  if (!open || journeyId == null) return null;

  async function confirmIdentity() {
    if (!journey || !draft) return;
    setSaving(true);
    setError(null);
    try {
      await api(`/api/patients/${journey.patient_id}`, {
        method: "PATCH",
        body: JSON.stringify({
          first_name: draft.first_name,
          last_name: draft.last_name,
          date_of_birth: draft.date_of_birth || null,
          oib: draft.oib || null,
          phone: draft.phone || null,
          email: draft.email || null,
          notes: draft.notes || null,
        }),
      });
      await api(`/api/patient-journeys/${journeyId}/check-in`, { method: "POST" });
      setStep("red_flags");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prijem nije spremljen.");
    } finally {
      setSaving(false);
    }
  }

  async function completeReception() {
    setSaving(true);
    setError(null);
    try {
      await api(`/api/patient-journeys/${journeyId}/check-in/complete-reception`, {
        method: "POST",
        body: JSON.stringify({
          items: selectedFlags.map((item) => ({ item_key: item.key, note: flags[item.key].note || item.defaultNote })),
        }),
      });
      await onCompleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prijem nije dovršen.");
    } finally {
      setSaving(false);
    }
  }

  function updateDraft(key: keyof PatientDraft, value: string) {
    setDraft((current) => current ? { ...current, [key]: value } : current);
  }

  function toggleFlag(key: RedFlagKey, active: boolean) {
    setFlags((current) => ({ ...current, [key]: { ...current[key], active } }));
  }

  function updateFlagNote(key: RedFlagKey, note: string) {
    setFlags((current) => ({ ...current, [key]: { ...current[key], note } }));
  }

  return <div className="modal-backdrop reception-native-backdrop" role="presentation">
    <section className="modal-panel reception-modal reception-native-modal" role="dialog" aria-modal="true" aria-labelledby="reception-native-title">
      <header className="reception-native-header">
        <div>
          <span className="eyebrow">Prijem pacijenta</span>
          <h2 id="reception-native-title">{step === "identity" ? "Opći podaci pacijenta" : "Kratka prijemna provjera"}</h2>
          <p>{step === "identity" ? "Provjerite osnovne podatke. Nakon potvrde otvara se kratka lista red flagova." : "Označite samo odstupanja. Ako je sve u redu, ne treba ništa klikati."}</p>
        </div>
        <button type="button" className="modal-close-button" onClick={onClose} disabled={saving} aria-label="Zatvori prijem"><X size={18}/></button>
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
        <label className="span-2">Napomene<input value={draft.notes} onChange={(event) => updateDraft("notes", event.target.value)}/></label>
      </div>}
      {!loading && step === "red_flags" && <div className="reception-native-flags">
        <div className={selectedFlags.length ? "reception-red-summary active" : "reception-red-summary"}>
          {selectedFlags.length ? <AlertTriangle size={18}/> : <CheckCircle2 size={18}/>}
          <span>{selectedFlags.length ? "Postoji crvena napomena. Pacijent se upućuje liječniku/anesteziologu na odluku." : "Nema označenih red flagova. Pacijent može čekati pregled/pretragu."}</span>
        </div>
        {redFlagItems.map((item) => {
          const state = flags[item.key];
          return <article key={item.key} className={state.active ? "reception-flag-card active" : "reception-flag-card"}>
            <label>
              <input type="checkbox" checked={state.active} onChange={(event) => toggleFlag(item.key, event.target.checked)}/>
              <span><strong>{item.label}</strong><small>{item.hint}</small></span>
            </label>
            {state.active && <textarea aria-label={`${item.label} - napomena`} value={state.note} onChange={(event) => updateFlagNote(item.key, event.target.value)} />}
          </article>;
        })}
      </div>}
      <footer className="reception-native-footer">
        <button type="button" onClick={onClose} disabled={saving}>Odustani</button>
        {step === "identity" ? <button type="button" onClick={confirmIdentity} disabled={saving || loading || !draft}><ClipboardCheck size={16}/>{saving ? "Spremam…" : "Podaci su točni"}</button> : <button type="button" onClick={completeReception} disabled={saving || loading}><ClipboardCheck size={16}/>{saving ? "Spremam…" : "Provjereno"}</button>}
      </footer>
    </section>
  </div>;
}
