import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import {
  BookOpenCheck,
  Boxes,
  Building2,
  CalendarDays,
  CheckSquare2,
  ChevronDown,
  ClipboardCheck,
  ClipboardList,
  FileSearch,
  FileText,
  KeyRound,
  LayoutDashboard,
  LogOut,
  PackageSearch,
  Pill,
  Settings,
  ShieldCheck,
  Stethoscope,
  TestTube,
  Users,
  WalletCards,
} from "lucide-react";
import { getActiveClinicId, getDemoPersonaKey, getSessionUser, logout, setActiveClinicId, setActiveClinicTimezone, switchDemoPersona, type DemoPersonaKey, type UserClinicsResponse } from "../api/client";
import { useApi } from "../hooks/useApi";
import { ToastHost } from "./ToastHost";

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard };
type NavEntry = NavItem | { label: string; icon: typeof LayoutDashboard; items: NavItem[] };

const items = {
  today: { to: "/", label: "Danas", icon: LayoutDashboard },
  patients: { to: "/patients", label: "Pacijenti", icon: Users },
  appointments: { to: "/appointments", label: "Naručivanje", icon: CalendarDays },
  reception: { to: "/reception", label: "Prijem", icon: ClipboardCheck },
  tasks: { to: "/workflow", label: "Zadaci", icon: CheckSquare2 },
  documents: { to: "/clinical-documents", label: "Dokumenti", icon: FileSearch },
  laboratory: { to: "/laboratory", label: "Laboratorij", icon: TestTube },
  therapies: { to: "/therapies", label: "Terapije", icon: Pill },
  gastroenterology: { to: "/gastroenterology", label: "Gastroenterologija", icon: Stethoscope },
  knowledge: { to: "/knowledge", label: "Znanje", icon: BookOpenCheck },
  inventory: { to: "/inventory", label: "Inventar", icon: Boxes },
  suppliers: { to: "/suppliers", label: "Dobavljači", icon: PackageSearch },
  purchaseOrders: { to: "/purchase-orders", label: "Narudžbenice", icon: ClipboardList },
  invoices: { to: "/invoices", label: "Računi", icon: FileText },
  services: { to: "/services", label: "Usluge", icon: Stethoscope },
  clinics: { to: "/clinics", label: "Klinike i osoblje", icon: Building2 },
  modules: { to: "/modules", label: "Moduli", icon: Settings },
  audit: { to: "/audit-log", label: "Evidencija aktivnosti", icon: ShieldCheck },
  apiKeys: { to: "/api-keys", label: "API ključevi", icon: KeyRound },
  readiness: { to: "/readiness", label: "Spremnost sustava", icon: ClipboardCheck },
  demoReview: { to: "/program1/synthetic-review", label: "Program 1 Demo", icon: TestTube },
  demoEvaluation: { to: "/program1/synthetic-evaluation", label: "Program 1 Evaluacija", icon: ClipboardCheck },
} satisfies Record<string, NavItem>;

const roleLabels: Record<string, string> = {
  admin: "Administrator",
  physician: "Liječnik",
  nurse: "Medicinska sestra/tehničar",
  receptionist: "Tajnica/administratorica",
  billing: "Naplata",
  inventory_manager: "Voditelj zaliha",
  document_reviewer: "Pregledavatelj dokumenata",
  ai_agent: "AI servisni račun",
};

const demoPersonas: Array<{ key: DemoPersonaKey; label: string }> = [
  { key: "admin", label: "Administrator" },
  { key: "receptionist", label: "Tajnica" },
  { key: "nurse", label: "Medicinska sestra" },
  { key: "physician_1", label: "Liječnik 1" },
  { key: "physician_2", label: "Liječnik 2" },
];

function group(label: string, icon: typeof LayoutDashboard, groupedItems: NavItem[]): NavEntry {
  return { label, icon, items: groupedItems };
}

export function navigationForRole(role: string, showDemo: boolean): NavEntry[] {
  if (role === "admin") {
    const administrationItems = [items.services, items.clinics, items.modules];
    if (showDemo) administrationItems.push(items.demoReview, items.demoEvaluation);
    return [
      items.today,
      group("Operacije", ClipboardCheck, [items.patients, items.appointments, items.reception, items.tasks, items.documents, items.laboratory, items.therapies, items.gastroenterology, items.knowledge]),
      group("Nabava i financije", WalletCards, [items.inventory, items.suppliers, items.purchaseOrders, items.invoices]),
      group("Administracija", Settings, administrationItems),
      group("Sigurnost", ShieldCheck, [items.audit, items.apiKeys, items.readiness]),
    ];
  }
  if (role === "physician") return [
    items.today,
    items.patients,
    group("Klinički rad", Stethoscope, [items.documents, items.laboratory, items.therapies, items.gastroenterology, items.knowledge]),
    items.tasks,
    items.appointments,
  ];
  if (role === "nurse") return [
    items.today,
    items.patients,
    items.tasks,
    group("Klinička podrška", TestTube, [items.documents, items.laboratory, items.therapies, items.reception]),
    group("Raspored i zalihe", Boxes, [items.appointments, items.inventory]),
  ];
  if (role === "receptionist") return [items.today, items.patients, items.appointments, items.reception, items.documents];
  if (role === "billing") return [items.today, items.patients, items.invoices];
  if (role === "inventory_manager") return [items.inventory, items.suppliers, items.purchaseOrders];
  if (role === "document_reviewer") return [items.today, items.patients, items.documents];
  return [items.today];
}

function isGroup(entry: NavEntry): entry is Extract<NavEntry, { items: NavItem[] }> {
  return "items" in entry;
}

function NavigationItem({ item }: { item: NavItem }) {
  const Icon = item.icon;
  return (
    <NavLink to={item.to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
      <Icon size={18} aria-hidden="true" />
      {item.label}
    </NavLink>
  );
}

export function AppShell() {
  const navigate = useNavigate();
  const publicConfig = useApi<{ demo_mode: boolean; real_data_allowed: boolean; demo_persona_switcher_enabled?: boolean; warnings?: string[] } | null>("/api/public-config", null);
  const clinicAccess = useApi<UserClinicsResponse | null>("/auth/me/clinics", null);
  const [activeClinic, setActiveClinic] = useState(getActiveClinicId() ?? "");
  const [pendingClinic, setPendingClinic] = useState<string | null>(null);
  const [persona, setPersona] = useState<DemoPersonaKey | null>(getDemoPersonaKey());
  const [pendingPersona, setPendingPersona] = useState<DemoPersonaKey | null>(null);
  const [switchingPersona, setSwitchingPersona] = useState(false);
  const fallbackDemoMode = import.meta.env.VITE_APP_ENV !== "production";
  const showDemoBanner = publicConfig.data ? publicConfig.data.demo_mode || !publicConfig.data.real_data_allowed : fallbackDemoMode;
  const warningText = publicConfig.data?.warnings?.join(" ") || "Demo/development okruženje – ne unositi stvarne podatke pacijenata.";
  const role = (getSessionUser()?.role ?? "").replace(/^demo_/, "") || "receptionist";
  const navigation = useMemo(() => navigationForRole(role, showDemoBanner), [role, showDemoBanner]);
  const selectedClinic = clinicAccess.data?.clinics.find((clinic) => String(clinic.id) === activeClinic);
  const inferredPersona = persona
    ?? (role === "physician" ? "physician_1" : demoPersonas.some((item) => item.key === role) ? role as DemoPersonaKey : null);

  useEffect(() => {
    if (!clinicAccess.data) return;
    const availableIds = clinicAccess.data.clinics.map((clinic) => String(clinic.id));
    const stored = getActiveClinicId();
    if (stored && availableIds.includes(stored)) {
      const clinic = clinicAccess.data.clinics.find((item) => String(item.id) === stored);
      setActiveClinicTimezone(clinic?.timezone ?? null);
      setActiveClinic(stored);
      return;
    }
    if (clinicAccess.data.default_clinic_id) {
      const next = String(clinicAccess.data.default_clinic_id);
      const clinic = clinicAccess.data.clinics.find((item) => String(item.id) === next);
      setActiveClinicId(next);
      setActiveClinicTimezone(clinic?.timezone ?? null);
      setActiveClinic(next);
    } else {
      setActiveClinicId(null);
      setActiveClinicTimezone(null);
      setActiveClinic("");
    }
  }, [clinicAccess.data]);

  function applyClinicChange() {
    if (!pendingClinic || !clinicAccess.data) return;
    const clinic = clinicAccess.data.clinics.find((item) => String(item.id) === pendingClinic);
    setActiveClinicId(pendingClinic);
    setActiveClinicTimezone(clinic?.timezone ?? null);
    setActiveClinic(pendingClinic);
    setPendingClinic(null);
    window.location.reload();
  }

  async function applyPersonaChange() {
    if (!pendingPersona || switchingPersona) return;
    setSwitchingPersona(true);
    try {
      const session = await switchDemoPersona(pendingPersona);
      setPersona(session.persona_key);
      setPendingPersona(null);
      window.location.assign("/");
    } finally {
      setSwitchingPersona(false);
    }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">A</div>
          <div>
            <strong>ASTRA</strong>
            <span>Clinic Core</span>
          </div>
        </div>
        <nav aria-label="Glavna navigacija">
          {navigation.map((entry) => {
            if (!isGroup(entry)) return <NavigationItem key={entry.to} item={entry} />;
            const Icon = entry.icon;
            return (
              <details className="nav-group" key={entry.label}>
                <summary>
                  <Icon size={18} aria-hidden="true" />
                  <span>{entry.label}</span>
                  <ChevronDown size={15} aria-hidden="true" />
                </summary>
                <div className="nav-group-items">
                  {entry.items.map((item) => <NavigationItem key={item.to} item={item} />)}
                </div>
              </details>
            );
          })}
        </nav>
      </aside>
      <main>
        {showDemoBanner && <div className="demo-banner">{warningText}</div>}
        <header className="topbar">
          <div className="topbar-context-group">
            {publicConfig.data?.demo_persona_switcher_enabled ? (
              <label className="demo-persona-picker">
                <span>DEMO PRIKAZ ULOGE</span>
                <select
                  aria-label="Demo prikaz uloge"
                  value={inferredPersona ?? ""}
                  disabled={switchingPersona}
                  onChange={(event) => {
                    const next = event.target.value as DemoPersonaKey;
                    if (next && next !== inferredPersona) setPendingPersona(next);
                  }}
                >
                  {!inferredPersona && <option value="">Odaberite personu</option>}
                  {demoPersonas.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
                </select>
              </label>
            ) : (
              <span className="topbar-role">Uloga: <strong>{roleLabels[role] ?? "Korisnik"}</strong></span>
            )}
            {publicConfig.data?.demo_persona_switcher_enabled && (
              <span className="demo-persona-context">
                DEMO · {demoPersonas.find((item) => item.key === inferredPersona)?.label ?? roleLabels[role] ?? "Korisnik"}
                {selectedClinic ? ` · ${selectedClinic.name}` : ""}
              </span>
            )}
            {clinicAccess.data && clinicAccess.data.clinics.length > 0 && (
              <label className="clinic-context-picker">
                Aktivna klinika
                <select
                  value={activeClinic}
                  onChange={(event) => {
                    const next = event.target.value;
                    if (next && next !== activeClinic) setPendingClinic(next);
                  }}
                >
                  {clinicAccess.data.requires_selection && <option value="">Odaberite kliniku</option>}
                  {clinicAccess.data.clinics.map((clinic) => <option key={clinic.id} value={clinic.id}>{clinic.name}</option>)}
                </select>
              </label>
            )}
            {clinicAccess.data?.requires_selection && !activeClinic && <span className="clinic-context-warning">Odaberite kliniku za prikaz podataka.</span>}
          </div>
          <button
            className="icon-button"
            aria-label="Odjava"
            title="Odjava"
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
          >
            <LogOut size={18} />
          </button>
        </header>
        {clinicAccess.data?.requires_selection && !activeClinic ? (
          <section className="page-card clinic-context-empty">
            <h1>Odaberite aktivnu kliniku</h1>
            <p>Korisnik ima pristup u više klinika. Odaberite kliniku u gornjoj traci kako bi se prikazali dnevni podaci.</p>
          </section>
        ) : <Outlet />}
      </main>
      {pendingClinic && clinicAccess.data && (
        <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setPendingClinic(null)}>
          <section className="modal-panel clinic-change-dialog" role="dialog" aria-modal="true" aria-labelledby="clinic-change-title">
            <header>
              <div>
                <span className="eyebrow">Promjena radnog konteksta</span>
                <h2 id="clinic-change-title">Promijeniti aktivnu kliniku?</h2>
              </div>
            </header>
            <p>
              Prikazat će se podaci klinike <strong>{clinicAccess.data.clinics.find((clinic) => String(clinic.id) === pendingClinic)?.name}</strong>.
              Spremite otvorene skice prije nastavka.
            </p>
            <footer>
              <button type="button" onClick={() => setPendingClinic(null)}>Odustani</button>
              <button type="button" className="primary" autoFocus onClick={applyClinicChange}>Promijeni kliniku</button>
            </footer>
          </section>
        </div>
      )}
      {pendingPersona && (
        <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && !switchingPersona && setPendingPersona(null)}>
          <section className="modal-panel clinic-change-dialog" role="dialog" aria-modal="true" aria-labelledby="persona-change-title">
            <header>
              <div>
                <span className="eyebrow">Sintetički sigurnosni kontekst</span>
                <h2 id="persona-change-title">Promijeniti demo ulogu?</h2>
              </div>
            </header>
            <p>
              Nastavit ćete kao <strong>{demoPersonas.find((item) => item.key === pendingPersona)?.label}</strong>.
              Otvoreni prikazi će se zatvoriti, a klinika i podaci ponovno učitati s ovlastima te osobe.
            </p>
            <footer>
              <button type="button" disabled={switchingPersona} onClick={() => setPendingPersona(null)}>Odustani</button>
              <button type="button" className="primary" disabled={switchingPersona} autoFocus onClick={applyPersonaChange}>
                {switchingPersona ? "Promjena uloge…" : "Promijeni demo ulogu"}
              </button>
            </footer>
          </section>
        </div>
      )}
      <ToastHost />
    </div>
  );
}
