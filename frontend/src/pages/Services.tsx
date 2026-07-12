import { FormEvent, useMemo, useState } from "react";
import { Eye, EyeOff, MapPin, Pencil, Plus, Save, Search, Trash2, X } from "lucide-react";
import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { HelpHint } from "../components/HelpHint";
import { useApi } from "../hooks/useApi";
import { Clinic, Room, Service } from "../types";

const euro = new Intl.NumberFormat("hr-HR", { style: "currency", currency: "EUR" });

export function Services() {
  const services = useApi<Service[]>("/api/services?include_hidden=true", []);
  const clinics = useApi<Clinic[]>("/api/clinics", []);
  const rooms = useApi<Room[]>("/api/rooms", []);
  const [clinicId, setClinicId] = useState("");
  const [query, setQuery] = useState("");
  const [name, setName] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState({ duration_minutes: 30, price: "0", clinic_id: "", room_ids: [] as number[] });
  const visibleServices = useMemo(() => { const normalizedQuery = query.trim().toLocaleLowerCase("hr"); return services.data.filter((service) => (!clinicId || service.clinic_ids?.includes(Number(clinicId))) && (!normalizedQuery || service.name.toLocaleLowerCase("hr").includes(normalizedQuery))); }, [services.data, clinicId, query]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const created = await api<Service>("/api/services", { method: "POST", body: JSON.stringify({ name, duration_minutes: 30, price: 0 }) });
    services.setData([...services.data, created].sort((a, b) => a.name.localeCompare(b.name)));
    setName("");
  }

  async function remove(service: Service) {
    if (!window.confirm(`Jeste li sigurni da želite obrisati uslugu „${service.name}“? Usluga će biti deaktivirana, a postojeći termini i računi ostat će sačuvani.`)) return;
    await api<Service>(`/api/services/${service.id}`, { method: "DELETE" });
    services.setData(services.data.filter((item) => item.id !== service.id));
  }

  async function toggleVisibility(service: Service) {
    const updated = await api<Service>(`/api/services/${service.id}/visibility`, { method: "POST" });
    services.setData(services.data.map((item) => item.id === updated.id ? updated : item));
  }

  function startEditing(service: Service) {
    setEditingId(service.id);
    const activeRoomIds = (service.room_ids ?? []).filter((id) => rooms.data.some((room) => room.id === id));
    const selectedClinicId = rooms.data.find((room) => activeRoomIds.includes(room.id))?.clinic_id ?? service.clinic_ids?.find((id) => clinics.data.some((clinic) => clinic.id === id));
    const selectedClinicRoomIds = activeRoomIds.filter((id) => rooms.data.find((room) => room.id === id)?.clinic_id === selectedClinicId);
    setEditDraft({ duration_minutes: service.duration_minutes, price: String(service.price), clinic_id: String(selectedClinicId ?? ""), room_ids: selectedClinicRoomIds });
  }

  async function saveEditing(service: Service) {
    const activeRoomIds = editDraft.room_ids.filter((id) => String(rooms.data.find((room) => room.id === id)?.clinic_id ?? "") === editDraft.clinic_id);
    const updated = await api<Service>(`/api/services/${service.id}`, { method: "PATCH", body: JSON.stringify({ duration_minutes: editDraft.duration_minutes, price: Number(editDraft.price), room_ids: activeRoomIds }) });
    services.setData(services.data.map((item) => item.id === updated.id ? updated : item));
    setEditingId(null);
  }

  return (
    <section className="page services-page">
      <div className="page-header"><div><h1>Usluge</h1><p>Katalog usluga prema klinici, trajanju i cijeni.</p></div></div>
      <section className="service-filter-panel" aria-labelledby="service-filter-title"><header><div><span className="eyebrow">Pretraživanje</span><h2 id="service-filter-title">Pronađi uslugu</h2></div><strong>{visibleServices.length} usluga</strong></header><div className="services-toolbar"><div className="services-filter-group"><label>Prikaži usluge klinike<select value={clinicId} onChange={(event) => setClinicId(event.target.value)}><option value="">Sve klinike</option>{clinics.data.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}</select><small>Ovaj izbor samo filtrira popis.</small></label><label>Pretraži po nazivu<span className="services-search"><Search size={17} /><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Upišite naziv usluge" /></span><small>Rezultati se prikazuju odmah.</small></label></div></div></section>
      <section className="service-create-panel" aria-labelledby="service-create-title"><div><span className="service-create-icon"><Plus size={20} /></span><span><h2 id="service-create-title">Dodaj novu uslugu</h2><p>Ovdje stvarate novu stavku kataloga. Kliniku i prostoriju odabrat ćete nakon dodavanja.</p></span></div><form onSubmit={submit}><input required value={name} onChange={(e) => setName(e.target.value)} aria-label="Naziv nove usluge" placeholder="Upišite naziv nove usluge" /><button className="primary"><Plus size={17} /> Dodaj uslugu</button><HelpHint title="Dodaj uslugu">Dodaje novu uslugu u katalog. Povezivanje s klinikom određuje se kroz dopuštene prostorije.</HelpHint></form></section>
      <DataTable rows={visibleServices} columns={[
        { header: "Naziv usluge", render: (row) => <button type="button" className="service-open-editor" onClick={() => startEditing(row)}><strong className={row.visible_in_catalog === false ? "service-hidden" : ""}>{row.name}</strong><small><MapPin size={13} />{(row.clinic_ids ?? []).map((id) => clinics.data.find((clinic) => clinic.id === id)?.name).filter(Boolean).join(", ") || "Klinika nije određena"} · {(row.room_ids ?? []).map((id) => rooms.data.find((room) => room.id === id)?.name).filter(Boolean).join(", ") || "Prostorija nije određena"}</small></button> },
        { header: "Trajanje", render: (row) => <span className={row.visible_in_catalog === false ? "service-hidden" : ""}>{row.duration_minutes} min</span> },
        { header: "Cijena", render: (row) => <span className={row.visible_in_catalog === false ? "service-hidden" : ""}>{euro.format(Number(row.price))}</span> },
        { header: "", render: (row) => <div className="service-row-actions"><button type="button" className="service-visibility-button" title={`Uredi ${row.name}`} aria-label={`Uredi uslugu ${row.name}`} onClick={() => startEditing(row)}><Pencil size={17} /></button><button type="button" className="service-visibility-button" title={row.visible_in_catalog === false ? `Prikaži ${row.name}` : `Sakrij ${row.name} iz operativnih usluga`} aria-label={row.visible_in_catalog === false ? `Prikaži uslugu ${row.name}` : `Sakrij uslugu ${row.name}`} onClick={() => toggleVisibility(row)}>{row.visible_in_catalog === false ? <Eye size={17} /> : <EyeOff size={17} />}</button><button type="button" className="service-delete-button" title={`Obriši ${row.name}`} aria-label={`Obriši uslugu ${row.name}`} onClick={() => remove(row)}><Trash2 size={17} /></button></div> }
      ]} />
      {editingId !== null && services.data.find((service) => service.id === editingId) && (() => { const service = services.data.find((item) => item.id === editingId)!; const clinicRooms = rooms.data.filter((room) => String(room.clinic_id ?? "") === editDraft.clinic_id); return <div className="modal-backdrop service-editor-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setEditingId(null); }}><form className="modal-panel service-editor-modal" role="dialog" aria-modal="true" aria-labelledby="service-editor-title" onSubmit={(event) => { event.preventDefault(); saveEditing(service); }}><header><div><span className="eyebrow">Usluga</span><h2 id="service-editor-title">{service.name}</h2><p>Promijenite trajanje, cijenu i mjesto izvođenja.</p></div><button type="button" className="service-modal-close" aria-label="Zatvori" onClick={() => setEditingId(null)}><X size={20} /></button></header><div className="service-editor-grid"><label>Trajanje<select value={editDraft.duration_minutes} onChange={(event) => setEditDraft({ ...editDraft, duration_minutes: Number(event.target.value) })}>{Array.from({ length: 48 }, (_, index) => (index + 1) * 10).map((minutes) => <option key={minutes} value={minutes}>{minutes} min</option>)}</select></label><label>Cijena u EUR<input required type="number" min="0" step="0.01" value={editDraft.price} onChange={(event) => setEditDraft({ ...editDraft, price: event.target.value })} /></label><label className="service-clinic-field">Klinika<select value={editDraft.clinic_id} onChange={(event) => setEditDraft({ ...editDraft, clinic_id: event.target.value, room_ids: [] })}><option value="">Bez klinike</option>{clinics.data.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}</select></label></div><fieldset className="service-room-picker"><legend>Prostorije</legend>{!editDraft.clinic_id && <p>Odaberite kliniku kako biste vidjeli njezine prostorije.</p>}{editDraft.clinic_id && clinicRooms.length === 0 && <p>Odabrana klinika nema aktivnih prostorija.</p>}{clinicRooms.map((room) => <label key={room.id} className={editDraft.room_ids.includes(room.id) ? "selected" : ""}><input type="checkbox" checked={editDraft.room_ids.includes(room.id)} onChange={(event) => setEditDraft({ ...editDraft, room_ids: event.target.checked ? [...editDraft.room_ids, room.id] : editDraft.room_ids.filter((id) => id !== room.id) })} /><MapPin size={16} /><span><strong>{room.name}</strong><small>{room.type || "Prostorija"}</small></span></label>)}</fieldset><footer><button type="button" onClick={() => setEditingId(null)}>Odustani</button><button className="primary"><Save size={17} /> Spremi promjene</button></footer></form></div>; })()}
    </section>
  );
}
