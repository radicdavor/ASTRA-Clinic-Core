import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useApi } from "../hooks/useApi";
import { Patient, Provider, Room, Service } from "../types";

export function AppointmentForm() {
  const navigate = useNavigate();
  const patients = useApi<Patient[]>("/api/patients", []);
  const services = useApi<Service[]>("/api/services", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const [form, setForm] = useState({ patient_id: "", service_id: "", provider_id: "", room_id: "", date: new Date().toISOString().slice(0, 10), start_time: "09:00", end_time: "09:30", duration_minutes: 30, status: "scheduled", source: "manual", notes: "" });
  async function submit(event: FormEvent) {
    event.preventDefault();
    await api("/api/appointments", { method: "POST", body: JSON.stringify({ ...form, patient_id: Number(form.patient_id), service_id: Number(form.service_id), provider_id: Number(form.provider_id), room_id: Number(form.room_id) }) });
    navigate("/appointments");
  }
  return (
    <section className="page narrow">
      <h1>Novi termin</h1>
      <form className="form-grid" onSubmit={submit}>
        <label>Pacijent<select required value={form.patient_id} onChange={(e) => setForm({ ...form, patient_id: e.target.value })}><option value="">Odaberi</option>{patients.data.map((p) => <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>)}</select></label>
        <label>Usluga<select required value={form.service_id} onChange={(e) => setForm({ ...form, service_id: e.target.value })}><option value="">Odaberi</option>{services.data.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
        <label>Liječnik<select required value={form.provider_id} onChange={(e) => setForm({ ...form, provider_id: e.target.value })}><option value="">Odaberi</option>{providers.data.map((p) => <option key={p.id} value={p.id}>{p.full_name}</option>)}</select></label>
        <label>Soba<select required value={form.room_id} onChange={(e) => setForm({ ...form, room_id: e.target.value })}><option value="">Odaberi</option>{rooms.data.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select></label>
        <label>Datum<input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} /></label>
        <label>Početak<input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} /></label>
        <label>Kraj<input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></label>
        <label>Trajanje<input type="number" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })} /></label>
        <button className="primary">Spremi termin</button>
      </form>
    </section>
  );
}
