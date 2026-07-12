import { FormEvent, useMemo, useState } from "react";
import { Building2, Clock3, DoorOpen, Mail, Stethoscope } from "lucide-react";
import { api } from "../api/client";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { Clinic, Provider, Room } from "../types";

export function Clinics() {
  const clinics = useApi<Clinic[]>("/api/clinics", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const providers = useApi<Provider[]>("/api/providers", []);
  const [clinicName, setClinicName] = useState("");
  const [roomDraft, setRoomDraft] = useState({ name: "", type: "ordinacija", clinic_id: "" });
  const [providerDraft, setProviderDraft] = useState({ full_name: "", specialty: "", email: "", clinic_id: "", work_start: "07:00", work_end: "15:00" });
  const [activeForm, setActiveForm] = useState<"clinic" | "room" | "provider" | null>(null);

  const defaultClinicId = useMemo(() => String(clinics.data[0]?.id ?? ""), [clinics.data]);
  const roomClinicId = roomDraft.clinic_id || defaultClinicId;
  const providerClinicId = providerDraft.clinic_id || defaultClinicId;

  async function addClinic(event: FormEvent) {
    event.preventDefault();
    const created = await api<Clinic>("/api/clinics", { method: "POST", body: JSON.stringify({ name: clinicName }) });
    clinics.setData([...clinics.data, created].sort((a, b) => a.name.localeCompare(b.name)));
    setClinicName("");
    setActiveForm(null);
  }

  async function addRoom(event: FormEvent) {
    event.preventDefault();
    const created = await api<Room>("/api/rooms", { method: "POST", body: JSON.stringify({ ...roomDraft, clinic_id: Number(roomClinicId) }) });
    rooms.setData([...rooms.data, created].sort((a, b) => a.name.localeCompare(b.name)));
    setRoomDraft({ name: "", type: "ordinacija", clinic_id: roomClinicId });
    setActiveForm(null);
  }

  async function addProvider(event: FormEvent) {
    event.preventDefault();
    const created = await api<Provider>("/api/providers", { method: "POST", body: JSON.stringify({ ...providerDraft, clinic_id: Number(providerClinicId) }) });
    providers.setData([...providers.data, created].sort((a, b) => a.full_name.localeCompare(b.full_name)));
    setProviderDraft({ full_name: "", specialty: "", email: "", clinic_id: providerClinicId, work_start: "07:00", work_end: "15:00" });
    setActiveForm(null);
  }

  return (
    <section className="page clinic-admin-page">
      <div className="page-header">
        <div>
          <h1>Klinike i resursi <HelpHint title="Klinike i resursi">Svaka klinika ima svoje prostorije i liječnike. Raspored sprječava istodobno zauzeće liječnika ili prostorije i poštuje radno vrijeme liječnika.</HelpHint></h1>
          <p>Upravljanje organizacijom koja se koristi u prijemu i terminima.</p>
        </div>
      </div>

      <div className="clinic-create-actions" aria-label="Dodavanje resursa">
        <button type="button" className={activeForm === "clinic" ? "active" : ""} onClick={() => setActiveForm(activeForm === "clinic" ? null : "clinic")}><Building2 size={17} /> Dodaj kliniku</button>
        <button type="button" className={activeForm === "room" ? "active" : ""} onClick={() => setActiveForm(activeForm === "room" ? null : "room")}><DoorOpen size={17} /> Dodaj prostoriju</button>
        <button type="button" className={activeForm === "provider" ? "active" : ""} onClick={() => setActiveForm(activeForm === "provider" ? null : "provider")}><Stethoscope size={17} /> Dodaj liječnika</button>
      </div>

      {activeForm && <div className="clinic-admin-forms">
        {activeForm === "clinic" && <form className="clinic-admin-form" onSubmit={addClinic}>
          <div className="clinic-form-title"><Building2 size={19} /><div><strong>Nova klinika</strong><span>Organizacijska cjelina</span></div></div>
          <label>Naziv<input required minLength={2} value={clinicName} onChange={(event) => setClinicName(event.target.value)} placeholder="npr. Gastroenterologija" /></label>
          <button className="primary">Dodaj kliniku</button>
        </form>}

        {activeForm === "room" && <form className="clinic-admin-form" onSubmit={addRoom}>
          <div className="clinic-form-title"><DoorOpen size={19} /><div><strong>Nova prostorija</strong><span>Pripada jednoj klinici</span></div></div>
          <label>Klinika<select required value={roomClinicId} onChange={(event) => setRoomDraft({ ...roomDraft, clinic_id: event.target.value })}><option value="">Odaberi</option>{clinics.data.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}</select></label>
          <label>Naziv<input required value={roomDraft.name} onChange={(event) => setRoomDraft({ ...roomDraft, name: event.target.value })} placeholder="npr. Ordinacija 2" /></label>
          <label>Vrsta<input value={roomDraft.type} onChange={(event) => setRoomDraft({ ...roomDraft, type: event.target.value })} /></label>
          <button className="primary" disabled={!roomClinicId}>Dodaj prostoriju</button>
        </form>}

        {activeForm === "provider" && <form className="clinic-admin-form provider-form" onSubmit={addProvider}>
          <div className="clinic-form-title"><Stethoscope size={19} /><div><strong>Novi liječnik</strong><span>Specijalnost, kontakt i radno vrijeme</span></div></div>
          <label>Klinika<select required value={providerClinicId} onChange={(event) => setProviderDraft({ ...providerDraft, clinic_id: event.target.value })}><option value="">Odaberi</option>{clinics.data.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}</select></label>
          <label>Ime i prezime<input required value={providerDraft.full_name} onChange={(event) => setProviderDraft({ ...providerDraft, full_name: event.target.value })} placeholder="dr. Ime Prezime" /></label>
          <label>Specijalnost<input required value={providerDraft.specialty} onChange={(event) => setProviderDraft({ ...providerDraft, specialty: event.target.value })} placeholder="npr. gastroenterologija" /></label>
          <label>E-mail<input required type="email" value={providerDraft.email} onChange={(event) => setProviderDraft({ ...providerDraft, email: event.target.value })} placeholder="lijecnik@klinika.hr" /></label>
          <div className="working-hours-fields">
            <label>Radi od<input required type="time" value={providerDraft.work_start} onChange={(event) => setProviderDraft({ ...providerDraft, work_start: event.target.value })} /></label>
            <label>Radi do<input required type="time" min={providerDraft.work_start} value={providerDraft.work_end} onChange={(event) => setProviderDraft({ ...providerDraft, work_end: event.target.value })} /></label>
          </div>
          <button className="primary" disabled={!providerClinicId}>Dodaj liječnika</button>
        </form>}
      </div>}

      <div className="clinic-resource-grid">
        {clinics.data.map((clinic) => {
          const clinicRooms = rooms.data.filter((room) => room.clinic_id === clinic.id);
          const clinicProviders = providers.data.filter((provider) => provider.clinic_id === clinic.id);
          return (
            <article className="clinic-resource-card" key={clinic.id}>
              <header><div><Building2 size={18} /><strong>{clinic.name}</strong></div><span>{clinicRooms.length} prostorija · {clinicProviders.length} liječnika</span></header>
              <div className="clinic-resource-columns">
                <section><h2><DoorOpen size={16} /> Prostorije</h2>{clinicRooms.map((room) => <div className="resource-line" key={room.id}><strong>{room.name}</strong><span>{room.type || "Prostorija"}</span></div>)}{clinicRooms.length === 0 && <p>Nema prostorija.</p>}</section>
                <section><h2><Stethoscope size={16} /> Liječnici</h2>{clinicProviders.map((provider) => <div className="resource-line provider-line" key={provider.id}><strong>{provider.full_name}</strong><span>{provider.specialty}</span><small><Mail size={13} /> {provider.email || "E-mail nije upisan"}</small><small><Clock3 size={13} /> {provider.work_start.slice(0, 5)}–{provider.work_end.slice(0, 5)}</small></div>)}{clinicProviders.length === 0 && <p>Nema liječnika.</p>}</section>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
