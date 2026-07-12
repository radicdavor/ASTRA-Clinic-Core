import { FormEvent, useMemo, useRef, useState } from "react";
import {
  CheckCircle2,
  Ban,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Droplets,
  FlaskConical,
  LayoutTemplate,
  Plus,
  Printer,
  Search,
  UserPlus,
  X,
} from "lucide-react";
import { api } from "../api/client";
import { HelpHint } from "../components/HelpHint";
import { DateInput } from "../components/DateInput";
import { QuickPatientModal } from "../components/QuickPatientModal";
import { useApi } from "../hooks/useApi";
import { LabHistoryItem, LabOrder, LabTemplate, Patient } from "../types";
import { formatDate, formatDateTime } from "../utils/date";

const statusLabel: Record<string, string> = {
  ordered: "Naručeno",
  collected: "Uzorak uzet",
  resulted: "Rezultati uneseni",
  reviewed: "Liječnik pregledao",
  cancelled: "Otkazano",
};
const today = () => new Date().toISOString().slice(0, 10);
const TEMPLATE_CATEGORIES = ["Metabolizam", "Kosa i koža", "Gastroenterologija", "Endokrinologija", "Nutritivni status", "Preventiva"];
export function Laboratory() {
  const dayPickerRef=useRef<HTMLInputElement>(null);
  const orders = useApi<LabOrder[]>("/api/laboratory/orders", []),
    patients = useApi<Patient[]>("/api/patients", []),
    templates = useApi<LabTemplate[]>("/api/laboratory/templates", []);
  const [query, setQuery] = useState(""),
    [activityDate, setActivityDate] = useState(today()),
    [activityFilter, setActivityFilter] = useState("all"),
    [resultFilter, setResultFilter] = useState("all"),
    [patientQuery, setPatientQuery] = useState(""),
    [showNew, setShowNew] = useState(false),
    [showTemplates, setShowTemplates] = useState(false),
    [showQuickPatient, setShowQuickPatient] = useState(false),
    [showCancel,setShowCancel]=useState(false),
    [history,setHistory]=useState<LabHistoryItem[]|null>(null),
    [historyTest,setHistoryTest]=useState(""),
    [selectedId, setSelectedId] = useState<number | null>(null);
  const [draft, setDraft] = useState({
    patient_id: "",
    external_laboratory: "",
    ordered_at: today(),
    notes: "",
    tests: "KKS, CRP",
    template_id: null as number | null,
  });
  const [values, setValues] = useState<Record<number, string>>({}),
    [metadata,setMetadata]=useState<Record<number,{unit:string;low:string;high:string}>>({}),
    [conclusion, setConclusion] = useState(""),
    [cancelReason,setCancelReason]=useState(""),
    [specimenType, setSpecimenType] = useState("blood");
  const selected = orders.data.find((o) => o.id === selectedId);
  const selectedPatient = patients.data.find((patient) => patient.id === Number(draft.patient_id));
  const patientMatches = patientQuery.trim().length < 2 ? [] : patients.data.filter((patient) => `${patient.first_name} ${patient.last_name} ${patient.oib ?? ""} ${patient.phone ?? ""}`.toLocaleLowerCase("hr").includes(patientQuery.trim().toLocaleLowerCase("hr"))).slice(0, 8);
  const filtered = useMemo(
    () =>
      orders.data.filter((o) => {
        const matchesText = `${o.patient.first_name} ${o.patient.last_name} ${o.results.map((r) => r.test_name).join(" ")}`
          .toLocaleLowerCase("hr")
          .includes(query.toLocaleLowerCase("hr"));
        const matchesActivity = activityFilter === "all" || (activityFilter === "ordered" ? o.ordered_at === activityDate : o.collected_at?.slice(0,10) === activityDate);
        const matchesResult = resultFilter==="all" || (resultFilter==="sample"&&!o.collected_at) || (resultFilter==="results"&&!!o.collected_at&&o.results.some(result=>result.flag==="pending")) || (resultFilter==="review"&&o.status==="resulted");
        return matchesText && matchesActivity && matchesResult;
      }),
    [orders.data, query, activityDate, activityFilter, resultFilter],
  );
  const dailyCollected=orders.data.filter(order=>order.collected_at?.slice(0,10)===activityDate);
  function moveDay(offset:number){const date=new Date(`${activityDate}T12:00:00`);date.setDate(date.getDate()+offset);setActivityDate(`${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`)}
  function open(order: LabOrder) {
    setSelectedId(order.id);
    setValues(
      Object.fromEntries(
        order.results.map((r) => [r.id, r.value ?? r.text_value ?? ""]),
      ),
    );
    setMetadata(Object.fromEntries(order.results.map(result=>[result.id,{unit:result.unit??"",low:result.reference_low??"",high:result.reference_high??""}])) as Record<number,{unit:string;low:string;high:string}>);
    setConclusion(order.review_conclusion ?? "");
    setSpecimenType(order.specimen_type ?? "blood");
  }
  function replaceOrder(updated:LabOrder){orders.setData(orders.data.map((order)=>order.id===updated.id?updated:order));open(updated)}
  async function collect(){if(!selected)return;replaceOrder(await api<LabOrder>(`/api/laboratory/orders/${selected.id}/collect`,{method:"POST",body:JSON.stringify({specimen_type:specimenType})}))}
  async function loadHistory(testName:string){if(!selected)return;setHistoryTest(testName);setHistory(await api<LabHistoryItem[]>(`/api/laboratory/patients/${selected.patient_id}/history?test_name=${encodeURIComponent(testName)}`))}
  async function cancelOrder(){if(!selected||cancelReason.trim().length<3)return;replaceOrder(await api<LabOrder>(`/api/laboratory/orders/${selected.id}/cancel`,{method:"POST",body:JSON.stringify({reason:cancelReason})}));setShowCancel(false);setCancelReason("")}
  function applyTemplate(template: LabTemplate) {
    setDraft({
      ...draft,
      template_id: template.id,
      tests: template.tests.map((test) => test.test_name).join(", "),
    });
    setShowTemplates(false);
  }
  async function create(e: FormEvent) {
    e.preventDefault();
    const tests = draft.tests
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean)
      .map((test_name) => ({ test_name }));
    const created = await api<LabOrder>("/api/laboratory/orders", {
      method: "POST",
      body: JSON.stringify({
        ...draft,
        patient_id: Number(draft.patient_id),
        tests,
      }),
    });
    orders.setData([created, ...orders.data]);
    setShowNew(false);
    open(created);
  }
  async function saveResults() {
    if (!selected) return;
    const updated = await api<LabOrder>(
      `/api/laboratory/orders/${selected.id}/results`,
      {
        method: "PUT",
        body: JSON.stringify({
          collected: false,
          results: selected.results.map((r) => ({
            id: r.id,
            value:
              values[r.id] !== "" && !Number.isNaN(Number(values[r.id]))
                ? Number(values[r.id])
                : null,
            text_value:
              values[r.id] !== "" && Number.isNaN(Number(values[r.id]))
                ? values[r.id]
                : null,
            unit:metadata[r.id]?.unit||null,
            reference_low:metadata[r.id]?.low!==""?Number(metadata[r.id].low):null,
            reference_high:metadata[r.id]?.high!==""?Number(metadata[r.id].high):null,
          })),
        }),
      },
    );
    orders.setData(orders.data.map((o) => (o.id === updated.id ? updated : o)));
    open(updated);
  }
  async function review() {
    if (!selected) return;
    const updated = await api<LabOrder>(
      `/api/laboratory/orders/${selected.id}/review`,
      { method: "POST", body: JSON.stringify({ conclusion }) },
    );
    orders.setData(orders.data.map((o) => (o.id === updated.id ? updated : o)));
    open(updated);
  }
  return (
    <section className="page laboratory-page">
      <header className="page-header">
        <div>
          <h1>Laboratorij i nalazi</h1>
          <p>
            Narudžbe pretraga, unos rezultata i liječnički pregled na jednom
            mjestu.
          </p>
        </div>
        <button className="primary" onClick={() => setShowNew(true)}>
          <Plus size={17} /> Nova narudžba
        </button>
      </header>
      <div className="lab-safety">
        <FlaskConical size={19} />
        <span>
          <strong>Rezultat nije dijagnoza.</strong> Oznake nisko i visoko samo
          uspoređuju broj sa zadanim referentnim rasponom. Liječnik tumači
          nalaz.
        </span>
        <HelpHint title="Kako radi laboratorij">
          Narudžba povezuje pacijenta i pretrage. Nakon unosa svih rezultata
          liječnik zapisuje zaključak i potvrđuje pregled.
        </HelpHint>
      </div>
      <section className="lab-day-board"><div className="lab-day-navigator"><span className="eyebrow">Dnevni pregled uzoraka</span><div><button aria-label="Prethodni dan" title="Prethodni dan" onClick={()=>moveDay(-1)}><ChevronLeft size={19}/></button><button className="lab-day-date" title="Odaberi datum iz kalendara" onClick={()=>dayPickerRef.current?.showPicker()}><CalendarDays size={17}/><strong>{formatDate(activityDate)}</strong></button><button aria-label="Sljedeći dan" title="Sljedeći dan" onClick={()=>moveDay(1)}><ChevronRight size={19}/></button><input ref={dayPickerRef} className="native-date-picker" type="date" value={activityDate} tabIndex={-1} aria-hidden="true" onChange={e=>setActivityDate(e.target.value)}/></div></div><label>Prikaži<select value={activityFilter} onChange={e=>setActivityFilter(e.target.value)}><option value="all">Sve narudžbe</option><option value="ordered">Naručeno taj dan</option><option value="collected">Uzorak uzet taj dan</option></select></label><div className="lab-day-counts"><button className={resultFilter==="sample"?"active":""} onClick={()=>setResultFilter(resultFilter==="sample"?"all":"sample")}><b>{orders.data.filter(order=>!order.collected_at).length}</b> čeka uzorak</button><button className={resultFilter==="results"?"active":""} onClick={()=>setResultFilter(resultFilter==="results"?"all":"results")}><b>{orders.data.filter(order=>order.collected_at&&order.results.some(result=>result.flag==="pending")).length}</b> čeka rezultate</button><button className={resultFilter==="review"?"active":""} onClick={()=>setResultFilter(resultFilter==="review"?"all":"review")}><b>{orders.data.filter(order=>order.status==="resulted").length}</b> čeka liječnika</button><span><b>{dailyCollected.length}</b> uzeto taj dan</span></div></section>
      <div className="lab-workspace">
        <section className="lab-list">
          <div className="lab-search">
            <Search size={16} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Pretraži pacijenta ili pretragu"
            />
          </div>
          {filtered.map((o) => (
            <button
              key={o.id}
              className={selectedId === o.id ? "active" : ""}
              onClick={() => open(o)}
            >
              <span>
                <strong>
                  {o.patient.first_name} {o.patient.last_name}
                </strong>
                <small>{o.results.map((r) => r.test_name).join(", ")}</small>
              </span>
              <span>
                <i className={`lab-status ${o.status}`}>
                  {statusLabel[o.status]}
                </i>
                <small>{formatDate(o.ordered_at)}</small>
              </span>
            </button>
          ))}
          {!filtered.length && (
            <p className="resource-empty">Nema laboratorijskih narudžbi.</p>
          )}
        </section>
        <section className="lab-detail">
          {!selected && (
            <div className="lab-empty">
              <FlaskConical size={34} />
              <h2>Odaberite nalaz</h2>
              <p>
                Kliknite narudžbu kako biste unijeli ili pregledali rezultate.
              </p>
            </div>
          )}
          {selected && (
            <>
              <header>
                <div>
                  <span className="eyebrow">Pacijent</span>
                  <h2>
                    {selected.patient.first_name} {selected.patient.last_name}
                  </h2>
                  <p>
                    {selected.external_laboratory || "Laboratorij nije naveden"}{" "}
                    · {formatDate(selected.ordered_at)}
                  </p>
                </div>
                <div className="lab-detail-tools"><i className={`lab-status ${selected.status}`}>{statusLabel[selected.status]}</i><button onClick={()=>window.print()}><Printer size={15}/> Ispiši</button>{!["reviewed","cancelled"].includes(selected.status)&&<button className="danger-icon" onClick={()=>setShowCancel(true)}><Ban size={15}/> Otkaži</button>}</div>
              </header>
              {selected.status!=="cancelled"&&<section className="lab-transport lab-transport-simple"><header><div><span className="eyebrow">Uzorak</span><h3>Uzimanje uzorka</h3></div></header><div className="lab-transport-steps"><article className={selected.collected_at?"done":"current"}><Droplets size={18}/><span><strong>Uzorak uzet</strong><small>{selected.collected_at?formatDateTime(selected.collected_at):"Čeka uzimanje"}</small></span></article></div><div className="lab-transport-actions">{!selected.collected_at&&<><label>Vrsta uzorka<select value={specimenType} onChange={e=>setSpecimenType(e.target.value)}><option value="blood">Krv</option><option value="urine">Urin</option><option value="stool">Stolica</option><option value="other">Drugo</option></select></label><button onClick={collect}><Droplets size={16}/> Evidentiraj uzimanje</button></>}</div></section>}
              {selected.status==="cancelled"&&<div className="lab-cancelled"><strong>Narudžba je otkazana</strong><p>{selected.cancellation_reason}</p></div>}
              <div className="lab-results">
                <div className="lab-result-head">
                  <span>Pretraga</span>
                  <span>Rezultat</span>
                  <span>Jedinica</span><span>Referentno</span>
                  <span>Status</span>
                </div>
                {selected.results.map((r) => (
                  <div className="lab-result-row" key={r.id}>
                    <button className="lab-history-button" onClick={()=>loadHistory(r.test_name)}><strong>{r.test_name}</strong><small>Povijest pretrage</small></button>
                    <input
                      disabled={["reviewed","cancelled"].includes(selected.status)}
                      value={values[r.id] ?? ""}
                      onChange={(e) =>
                        setValues({ ...values, [r.id]: e.target.value })
                      }
                      placeholder="Unesite vrijednost"
                    />
                    <input className="lab-unit-input" disabled={selected.status==="reviewed"} value={metadata[r.id]?.unit??""} onChange={e=>setMetadata({...metadata,[r.id]:{...(metadata[r.id]??{low:"",high:""}),unit:e.target.value}})} placeholder="npr. mg/L"/>
                    <span className="lab-reference-inputs"><input type="number" step="any" disabled={selected.status==="reviewed"} value={metadata[r.id]?.low??""} onChange={e=>setMetadata({...metadata,[r.id]:{...(metadata[r.id]??{unit:"",high:""}),low:e.target.value}})} placeholder="od"/><i>–</i><input type="number" step="any" disabled={selected.status==="reviewed"} value={metadata[r.id]?.high??""} onChange={e=>setMetadata({...metadata,[r.id]:{...(metadata[r.id]??{unit:"",low:""}),high:e.target.value}})} placeholder="do"/></span>
                    <i className={`lab-flag ${r.flag}`}>
                      {r.flag === "low"
                        ? "Nisko"
                        : r.flag === "high"
                          ? "Visoko"
                          : r.flag === "normal"
                            ? "U rasponu"
                            : "Čeka unos"}
                    </i>
                  </div>
                ))}
              </div>
              {!['reviewed','cancelled'].includes(selected.status) && (
                <div className="lab-actions">
                  <button onClick={saveResults}>Spremi rezultate</button>
                  <label>
                    Liječnički zaključak
                    <textarea
                      value={conclusion}
                      onChange={(e) => setConclusion(e.target.value)}
                      placeholder="Kliničko tumačenje liječnika"
                    />
                  </label>
                  <button
                    className="primary"
                    disabled={
                      selected.status !== "resulted" ||
                      conclusion.trim().length < 2
                    }
                    onClick={review}
                  >
                    <CheckCircle2 size={17} /> Potvrdi pregled
                  </button>
                </div>
              )}
              {selected.status === "reviewed" && (
                <div className="lab-reviewed">
                  <CheckCircle2 size={20} />
                  <div>
                    <strong>Liječnik je pregledao nalaz</strong>
                    <p>{selected.review_conclusion}</p>
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      </div>
      {showNew && (
        <div
          className="modal-backdrop"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setShowNew(false);
          }}
        >
          <form className="modal-panel lab-new-modal" onSubmit={create}>
            <header>
              <div>
                <span className="eyebrow">Nova narudžba</span>
                <h2>Naruči laboratorijske pretrage</h2>
              </div>
              <button type="button" onClick={() => setShowNew(false)}>
                <X size={19} />
              </button>
            </header>
            <div className="lab-patient-field">
              <strong>Pacijent</strong>
              {!selectedPatient && <div className="lab-patient-search"><Search size={17}/><input autoComplete="off" value={patientQuery} onChange={(e) => { setPatientQuery(e.target.value); setDraft({...draft, patient_id:""}); }} placeholder="Upišite ime, prezime, OIB ili telefon"/></div>}
              {!selectedPatient && patientQuery.trim().length >= 2 && <div className="lab-patient-results">{patientMatches.map((patient) => <button type="button" key={patient.id} onClick={() => { setDraft({...draft,patient_id:String(patient.id)}); setPatientQuery(`${patient.first_name} ${patient.last_name}`); }}><strong>{patient.first_name} {patient.last_name}</strong><small>{patient.date_of_birth ? `Rođen/a: ${formatDate(patient.date_of_birth)}` : "Datum rođenja nije upisan"}{patient.oib ? ` · OIB: ${patient.oib}` : ""}</small></button>)}{patientMatches.length===0&&<div className="patient-not-found"><p>Nema pronađenih pacijenata.</p><button type="button" className="primary" onClick={()=>setShowQuickPatient(true)}><UserPlus size={15}/> Dodaj pacijenta</button></div>}</div>}
              {selectedPatient && <div className="lab-selected-patient"><span><strong>{selectedPatient.first_name} {selectedPatient.last_name}</strong><small>{selectedPatient.date_of_birth ? `Rođen/a: ${formatDate(selectedPatient.date_of_birth)}` : "Datum rođenja nije upisan"}{selectedPatient.oib ? ` · OIB: ${selectedPatient.oib}` : ""}</small></span><button type="button" onClick={() => { setDraft({...draft,patient_id:""}); setPatientQuery(""); }}>Promijeni</button></div>}
            </div>
            <label>
              Datum narudžbe
              <DateInput required value={draft.ordered_at} onChange={(value) => setDraft({ ...draft, ordered_at: value })}/>
            </label>
            <label>
              Vanjski laboratorij
              <input
                value={draft.external_laboratory}
                onChange={(e) =>
                  setDraft({ ...draft, external_laboratory: e.target.value })
                }
                placeholder="Npr. vanjski laboratorij"
              />
            </label>
            <div className="lab-template-field">
              <div>
                <strong>Pretrage, odvojene zarezom</strong>
                <span className="lab-template-tools">
                  <button
                    type="button"
                    title="Odaberi predložak pretraga"
                    onClick={() => setShowTemplates(!showTemplates)}
                  >
                    <LayoutTemplate size={17} /> Predlošci
                  </button>
                </span>
              </div>
              {showTemplates && (
                <div className="lab-template-picker">
                  <header>
                    <strong>Odaberite predložak</strong>
                    <button
                      type="button"
                      onClick={() => setShowTemplates(false)}
                    >
                      <X size={16} />
                    </button>
                  </header>
                  {TEMPLATE_CATEGORIES.map((category) => {
                    const categoryTemplates = templates.data.filter((template) => template.category === category);
                    return categoryTemplates.length ? <section className="lab-template-group" key={category}><h3>{category}</h3>{categoryTemplates.map((template) => <button type="button" key={template.id} onClick={() => applyTemplate(template)}><span><strong>{template.name}</strong><small>{template.condition} · {template.description}</small></span><i>{template.tests.length} pretraga</i></button>)}</section> : null;
                  })}
                </div>
              )}
              <textarea
                required
                value={draft.tests}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    tests: e.target.value,
                    template_id: null,
                  })
                }
              />
              <small className="lab-template-note">Predložak je početna lista. Liječnik može promijeniti pretrage prije naručivanja.</small>
              {draft.template_id && (
                <small className="lab-template-selected">
                  <LayoutTemplate size={13} /> Primijenjen predložak:{" "}
                  {templates.data.find((t) => t.id === draft.template_id)?.name}
                </small>
              )}
            </div>
            <label>
              Napomena
              <textarea
                value={draft.notes}
                onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
              />
            </label>
            <footer>
              <button type="button" onClick={() => setShowNew(false)}>
                Odustani
              </button>
              <button className="primary" disabled={!draft.patient_id}>Kreiraj narudžbu</button>
            </footer>
          </form>
        </div>
      )}
      {history&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setHistory(null)}}><section className="modal-panel lab-history-modal"><header><div><span className="eyebrow">Povijest rezultata</span><h2>{historyTest}</h2><p>{selected?.patient.first_name} {selected?.patient.last_name}</p></div><button onClick={()=>setHistory(null)}><X size={18}/></button></header><div>{history.map(item=><article key={`${item.order_id}-${item.ordered_at}`}><time>{formatDate(item.ordered_at)}</time><strong>{item.value??item.text_value??"Bez rezultata"} {item.unit??""}</strong><i className={`lab-flag ${item.flag}`}>{item.flag}</i></article>)}{!history.length&&<p>Nema ranijih rezultata ove pretrage.</p>}</div><footer><button onClick={()=>setHistory(null)}>Zatvori</button></footer></section></div>}
      {showCancel&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setShowCancel(false)}}><section className="modal-panel lab-cancel-modal"><header><div><span className="eyebrow">Kritična radnja</span><h2>Otkaži laboratorijsku narudžbu</h2></div><button onClick={()=>setShowCancel(false)}><X size={18}/></button></header><p>Narudžba ostaje u povijesti i auditu, ali više se neće obrađivati.</p><label>Razlog otkazivanja<textarea autoFocus value={cancelReason} onChange={e=>setCancelReason(e.target.value)}/></label><footer><button onClick={()=>setShowCancel(false)}>Odustani</button><button className="danger" disabled={cancelReason.trim().length<3} onClick={cancelOrder}>Potvrdi otkazivanje</button></footer></section></div>}
      {showQuickPatient&&<QuickPatientModal initialQuery={patientQuery} onClose={()=>setShowQuickPatient(false)} onCreated={patient=>{patients.setData([...patients.data,patient]);setDraft({...draft,patient_id:String(patient.id)});setPatientQuery(`${patient.first_name} ${patient.last_name}`);setShowQuickPatient(false)}}/>}
    </section>
  );
}
