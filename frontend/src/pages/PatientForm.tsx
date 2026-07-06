import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, notifyUser } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { HelpHint } from "../components/HelpHint";
import { Patient } from "../types";
import { formatPatientIdentity, formatPatientName } from "../utils/patientIdentity";

export function PatientForm() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const returnTo = params.get("return_to");
  const initialName = params.get("name") ?? "";
  const initialNameParts = useMemo(() => initialName.trim().split(/\s+/).filter(Boolean), [initialName]);
  const [form, setForm] = useState({ first_name: "", last_name: "", date_of_birth: "", oib: "", phone: "", email: "", notes: "" });
  const [error, setError] = useState("");
  const [possibleDuplicates, setPossibleDuplicates] = useState<Patient[]>([]);
  const [duplicatesConfirmed, setDuplicatesConfirmed] = useState(false);

  const duplicateQuery = useMemo(() => {
    if (!form.first_name.trim() || !form.last_name.trim()) return "";
    const params = new URLSearchParams();
    params.set("first_name", form.first_name.trim());
    params.set("last_name", form.last_name.trim());
    if (form.date_of_birth) params.set("date_of_birth", form.date_of_birth);
    if (form.phone.trim()) params.set("phone", form.phone.trim());
    if (form.email.trim()) params.set("email", form.email.trim());
    if (form.oib.trim()) params.set("oib", form.oib.trim());
    return `/api/patients/possible-duplicates?${params.toString()}`;
  }, [form.date_of_birth, form.email, form.first_name, form.last_name, form.oib, form.phone]);

  function optionalText(value: string) {
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }

  useEffect(() => {
    if (!initialName.trim()) return;
    setForm((current) => {
      if (current.first_name || current.last_name) return current;
      return {
        ...current,
        first_name: initialNameParts[0] ?? "",
        last_name: initialNameParts.slice(1).join(" ")
      };
    });
  }, [initialName, initialNameParts]);

  useEffect(() => {
    let alive = true;
    setDuplicatesConfirmed(false);
    if (!duplicateQuery) {
      setPossibleDuplicates([]);
      return;
    }
    api<Patient[]>(duplicateQuery).then((result) => alive && setPossibleDuplicates(result)).catch(() => alive && setPossibleDuplicates([]));
    return () => {
      alive = false;
    };
  }, [duplicateQuery]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (form.oib && !/^\d{11}$/.test(form.oib.trim())) {
      setError("OIB mora imati tocno 11 znamenki.");
      notifyUser("OIB mora imati tocno 11 znamenki.", "error");
      return;
    }
    if (possibleDuplicates.length > 0 && !duplicatesConfirmed) {
      setError("Pronadeni su moguci duplikati. Provjerite identitet pacijenta i potvrdite nastavak.");
      notifyUser("Pronadeni su moguci duplikati. Provjerite identitet pacijenta i potvrdite nastavak.", "error");
      return;
    }
    const patient = await api<Patient>("/api/patients", {
      method: "POST",
      body: JSON.stringify({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        date_of_birth: form.date_of_birth || null,
        oib: optionalText(form.oib),
        phone: optionalText(form.phone),
        email: optionalText(form.email),
        notes: optionalText(form.notes)
      })
    });
    navigate(returnTo === "appointment" ? `/appointments/new?patient_id=${patient.id}` : "/patients");
  }

  return (
    <section className="page narrow">
      <div className="page-header">
        <div>
          <h1>
            Novi pacijent <HelpHint title="Novi pacijent">Otvara unos novog pacijenta. U demo nacinu ne unosite stvarne osobne podatke.</HelpHint>
          </h1>
          <p>{returnTo === "appointment" ? "Nakon spremanja pacijent ce biti odabran u novom terminu." : "Unos osnovnih podataka za narucivanje i pracenje toka pacijenta."}</p>
        </div>
      </div>
      {error && <p className="form-error">{error}</p>}
      {possibleDuplicates.length > 0 && (
        <div className="duplicate-warning">
          <strong>Moguci duplikati pacijenta</strong>
          <p>Provjerite identitet prije spremanja novog pacijenta.</p>
          {possibleDuplicates.map((patient) => (
            <span key={patient.id}>
              {formatPatientName(patient)} <small>{formatPatientIdentity(patient)}</small>
            </span>
          ))}
          <label className="confirm-row">
            <input type="checkbox" checked={duplicatesConfirmed} onChange={(event) => setDuplicatesConfirmed(event.target.checked)} />
            Provjereno, nastavi sa spremanjem novog pacijenta.
          </label>
        </div>
      )}
      <form className="form-grid" onSubmit={submit}>
        {[
          ["first_name", "Ime"],
          ["last_name", "Prezime"],
          ["date_of_birth", "Datum rodenja"],
          ["oib", "OIB"],
          ["phone", "Telefon"],
          ["email", "E-posta"],
          ["notes", "Napomene"]
        ].map(([key, label]) => (
          <label key={key}>
            <span className="label-with-help">
              {label}
              {key === "oib" && <HelpHint title="OIB">OIB je dodatni jedinstveni identifikator pacijenta. U demo nacinu ostavite prazno ili koristite izmisljen broj.</HelpHint>}
            </span>
            <input type={key === "date_of_birth" ? "date" : "text"} placeholder={key === "oib" ? "Demo OIB ili prazno" : undefined} value={(form as any)[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} />
          </label>
        ))}
        <ActionButton type="submit" className="primary" variant="create" helpTitle="Spremi pacijenta" help="Sprema pacijenta u lokalnu demo bazu. Ne unosite stvarne OIB-e ili osobne podatke dok real-data readiness nije odobren.">
          Spremi pacijenta
        </ActionButton>
      </form>
    </section>
  );
}
