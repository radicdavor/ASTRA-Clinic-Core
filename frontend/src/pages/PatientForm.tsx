import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export function PatientForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name: "", last_name: "", date_of_birth: "", phone: "", email: "", notes: "" });
  async function submit(event: FormEvent) {
    event.preventDefault();
    await api("/api/patients", { method: "POST", body: JSON.stringify(form) });
    navigate("/patients");
  }
  return (
    <section className="page narrow">
      <h1>Novi pacijent</h1>
      <form className="form-grid" onSubmit={submit}>
        {[
          ["first_name", "Ime"],
          ["last_name", "Prezime"],
          ["date_of_birth", "Datum rođenja"],
          ["phone", "Telefon"],
          ["email", "E-pošta"],
          ["notes", "Napomene"]
        ].map(([key, label]) => <label key={key}>{label}<input type={key === "date_of_birth" ? "date" : "text"} value={(form as any)[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} /></label>)}
        <button className="primary">Spremi pacijenta</button>
      </form>
    </section>
  );
}
