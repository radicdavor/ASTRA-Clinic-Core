import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { BookOpenCheck, Boxes, Building2, CalendarCheck, CalendarDays, CheckSquare2, ClipboardCheck, ClipboardList, FileSearch, FileText, KeyRound, LayoutDashboard, LogOut, PackageSearch, Pill, Search, Settings, ShieldCheck, Stethoscope, TestTube, Users } from "lucide-react";
import { clearToken } from "../api/client";
import { useApi } from "../hooks/useApi";
import { ToastHost } from "./ToastHost";

const nav = [
  { to: "/", label: "Nadzorna ploca", icon: LayoutDashboard },
  { to: "/patients", label: "Pacijenti", icon: Users },
  { to: "/reception", label: "Prijem", icon: CalendarCheck },
  { to: "/clinical-documents", label: "Dokumenti", icon: FileSearch },
  { to: "/laboratory", label: "Laboratorij", icon: TestTube },
  { to: "/therapies", label: "Terapije", icon: Pill },
  { to: "/appointments", label: "Termini", icon: CalendarDays },
  { to: "/workflow", label: "Zadaci", icon: CheckSquare2 },
  { to: "/knowledge", label: "Klinicka knjiznica", icon: BookOpenCheck },
  { to: "/gastroenterology", label: "Gastroenterologija", icon: Stethoscope },
  { to: "/services", label: "Usluge", icon: Stethoscope },
  { to: "/clinics", label: "Klinike", icon: Building2 },
  { to: "/modules", label: "Moduli", icon: Settings },
  { to: "/inventory", label: "Inventar", icon: Boxes },
  { to: "/suppliers", label: "Dobavljaci", icon: PackageSearch },
  { to: "/purchase-orders", label: "Narudzbenice", icon: ClipboardList },
  { to: "/invoices", label: "Racuni", icon: FileText },
  { to: "/audit-log", label: "Audit log", icon: ShieldCheck },
  { to: "/api-keys", label: "API kljucevi", icon: KeyRound },
  { to: "/readiness", label: "Spremnost", icon: ClipboardCheck }
];

const program1DemoNav = [
  { to: "/program1/synthetic-review", label: "Program 1 Demo", icon: TestTube },
  { to: "/program1/synthetic-evaluation", label: "Program 1 Evaluacija", icon: ClipboardCheck }
];

export function AppShell() {
  const navigate = useNavigate();
  const publicConfig = useApi<{ demo_mode: boolean; real_data_allowed: boolean; warnings?: string[] } | null>("/api/public-config", null);
  const fallbackDemoMode = import.meta.env.VITE_APP_ENV !== "production";
  const showDemoBanner = publicConfig.data ? publicConfig.data.demo_mode || !publicConfig.data.real_data_allowed : fallbackDemoMode;
  const warningText = publicConfig.data?.warnings?.join(" ") || "Demo/development okruzenje - ne unositi stvarne podatke pacijenata.";

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
        <nav>
          {[...nav, ...(showDemoBanner ? program1DemoNav : [])].map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}>
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <main>
        {showDemoBanner && (
          <div className="demo-banner">
            {warningText}
          </div>
        )}
        <header className="topbar">
          <div className="search">
            <Search size={18} />
            <input placeholder="Pretrazi pacijenta, uslugu, status..." />
          </div>
          <button
            className="icon-button"
            title="Odjava"
            onClick={() => {
              clearToken();
              navigate("/login");
            }}
          >
            <LogOut size={18} />
          </button>
        </header>
        <Outlet />
      </main>
      <ToastHost />
    </div>
  );
}
