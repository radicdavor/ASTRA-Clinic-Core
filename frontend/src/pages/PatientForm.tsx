import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { HelpHint } from "../components/HelpHint";

export function PatientForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: "", last_name: "", date_of_birth: "", oib: "", phone: "", email: "", notes: "" });
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (form.oib && !/^\d{11}$/.test(form.oib.trim())) {
      setError("OIB mora imati tocno 11 znamenki.");
      return;
    }
    await api("/api/patients", {
      method: "POST",
      body: JSON.stringify({ ...form, date_of_birth: form.date_of_birth || null, oib: form.oib.trim() || null })
    });
    navigate("/patients");
  }

  return (
    <section className="page narrow">
      <div className="page-header">
        <div>
          <h1>
            Novi pacijent <HelpHint title="Novi pacijent">Otvara unos novog pacijenta. U demo nacinu ne unosite stvarne osobne podatke.</HelpHint>
          </h1>
          <p>Unos osnovnih podataka za narucivanje i pracenje toka pacijenta.</p>
        </div>
      </div>
      {error && <p className="form-error">{error}</p>}
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
        <button className="primary">Spremi pacijenta</button>
        <HelpHint title="Spremi pacijenta">Sprema pacijenta u lokalnu demo bazu. Ne unosite stvarne OIB-e ili osobne podatke dok real-data readiness nije odobren.</HelpHint>
      </form>
    </section>
  );
}
