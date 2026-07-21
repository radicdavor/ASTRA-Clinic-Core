import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { BookOpenCheck, Boxes, Building2, CalendarDays, CheckSquare2, ChevronDown, ClipboardCheck, ClipboardList, FileSearch, FileText, KeyRound, LayoutDashboard, LogOut, MoreHorizontal, PackageSearch, Pill, Settings, ShieldCheck, Stethoscope, TestTube, Users } from "lucide-react";
import { getActiveClinicId, getSessionUser, logout, setActiveClinicId, setActiveClinicTimezone, type UserClinicsResponse } from "../api/client";
import { useApi } from "../hooks/useApi";
import { ToastHost } from "./ToastHost";

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard; roles?: string[] };
type NavGroup = { label: string; items: NavItem[] };
const all = ["admin"];
const clinical = ["admin", "physician", "nurse", "document_reviewer"];
const patientRoles = ["admin", "physician", "nurse", "receptionist", "billing", "document_reviewer"];
const schedulingRoles = ["admin", "physician", "nurse", "receptionist"];

const primaryNav: NavItem[] = [
  { to: "/", label: "Danas", icon: LayoutDashboard, roles: patientRoles },
  { to: "/patients", label: "Pacijenti", icon: Users, roles: patientRoles },
  { to: "/appointments", label: "Naručivanje", icon: CalendarDays, roles: schedulingRoles },
  { to: "/knowledge", label: "Znanje", icon: BookOpenCheck, roles: ["admin", "physician"] },
];

const secondaryGroups: NavGroup[] = [
  { label: "Klinički alati", items: [
    { to: "/clinical-documents", label: "Dokumenti", icon: FileSearch, roles: clinical.concat("receptionist") },
    { to: "/laboratory", label: "Laboratorij", icon: TestTube, roles: clinical },
    { to: "/therapies", label: "Terapije", icon: Pill, roles: clinical },
    { to: "/gastroenterology", label: "Gastroenterologija", icon: Stethoscope, roles: ["admin", "physician"] },
  ]},
  { label: "Organizacija rada", items: [
    { to: "/reception", label: "Prijem", icon: ClipboardCheck, roles: ["admin", "receptionist", "nurse"] },
    { to: "/workflow", label: "Zadaci", icon: CheckSquare2, roles: ["admin", "physician", "nurse", "receptionist"] },
  ]},
  { label: "Nabava i zalihe", items: [
    { to: "/inventory", label: "Inventar", icon: Boxes, roles: ["admin", "nurse", "inventory_manager"] },
    { to: "/suppliers", label: "Dobavljači", icon: PackageSearch, roles: ["admin", "inventory_manager"] },
    { to: "/purchase-orders", label: "Narudžbenice", icon: ClipboardList, roles: ["admin", "inventory_manager"] },
  ]},
  { label: "Financije", items: [{ to: "/invoices", label: "Računi", icon: FileText, roles: ["admin", "billing", "receptionist", "physician"] }] },
  { label: "Administracija", items: [
    { to: "/services", label: "Usluge", icon: Stethoscope, roles: all },
    { to: "/clinics", label: "Klinike i osoblje", icon: Building2, roles: all },
    { to: "/modules", label: "Moduli", icon: Settings, roles: all },
    { to: "/audit-log", label: "Evidencija aktivnosti", icon: ShieldCheck, roles: all },
    { to: "/api-keys", label: "API ključevi", icon: KeyRound, roles: all },
    { to: "/readiness", label: "Spremnost sustava", icon: ClipboardCheck, roles: all },
  ]},
];

function visible(item: NavItem, role: string) { return !item.roles || item.roles.includes(role); }

export function AppShell() {
  const navigate = useNavigate();
  const publicConfig = useApi<{ demo_mode: boolean; real_data_allowed: boolean; warnings?: string[] } | null>("/api/public-config", null);
  const clinicAccess = useApi<UserClinicsResponse | null>("/auth/me/clinics", null);
  const [activeClinic, setActiveClinic] = useState(getActiveClinicId() ?? "");
  const fallbackDemoMode = import.meta.env.VITE_APP_ENV !== "production";
  const showDemoBanner = publicConfig.data ? publicConfig.data.demo_mode || !publicConfig.data.real_data_allowed : fallbackDemoMode;
  const warningText = publicConfig.data?.warnings?.join(" ") || "Demo/development okruzenje - ne unositi stvarne podatke pacijenata.";
  const role = (getSessionUser()?.role ?? "").replace(/^demo_/, "") || "receptionist";
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
  const groups = secondaryGroups.map(group => ({ ...group, items: group.items.filter(item => visible(item, role)) })).filter(group => group.items.length);
  if (showDemoBanner && role === "admin") groups.push({ label: "Demo", items: [
    { to: "/program1/synthetic-review", label: "Program 1 Demo", icon: TestTube },
    { to: "/program1/synthetic-evaluation", label: "Program 1 Evaluacija", icon: ClipboardCheck },
  ]});

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
          {primaryNav.filter(item => visible(item, role)).map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
          {groups.length > 0 && <details className="nav-more">
            <summary><MoreHorizontal size={18}/><span>Više</span><ChevronDown size={15}/></summary>
            <div className="nav-more-groups">{groups.map(group => <section key={group.label}><h2>{group.label}</h2>{group.items.map(item => { const Icon = item.icon; return <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}><Icon size={17}/>{item.label}</NavLink>; })}</section>)}</div>
          </details>}
        </nav>
      </aside>
      <main>
        {showDemoBanner && (
          <div className="demo-banner">
            {warningText}
          </div>
        )}
        <header className="topbar">
          <div className="topbar-context-group">
            <span className="topbar-context">{role === "admin" ? "Administratorski prikaz" : "Operativni prikaz"}</span>
            {clinicAccess.data && clinicAccess.data.clinics.length > 0 && (
              <label className="clinic-context-picker">
                Aktivna klinika
                <select
                  value={activeClinic}
                  onChange={(event) => {
                    const next = event.target.value;
                    const clinic = clinicAccess.data?.clinics.find((item) => String(item.id) === next);
                    setActiveClinicId(next);
                    setActiveClinicTimezone(clinic?.timezone ?? null);
                    setActiveClinic(next);
                    window.location.reload();
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
      <ToastHost />
    </div>
  );
}
