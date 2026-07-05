import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Boxes, CalendarDays, ClipboardList, FileText, KeyRound, LayoutDashboard, LogOut, PackageSearch, Search, Settings, ShieldCheck, Stethoscope, Users } from "lucide-react";
import { clearToken } from "../api/client";

const nav = [
  { to: "/", label: "Nadzorna ploča", icon: LayoutDashboard },
  { to: "/patients", label: "Pacijenti", icon: Users },
  { to: "/appointments", label: "Termini", icon: CalendarDays },
  { to: "/services", label: "Usluge", icon: Stethoscope },
  { to: "/modules", label: "Moduli", icon: Settings },
  { to: "/inventory", label: "Inventar", icon: Boxes },
  { to: "/suppliers", label: "Dobavljači", icon: PackageSearch },
  { to: "/purchase-orders", label: "Narudžbenice", icon: ClipboardList },
  { to: "/invoices", label: "Računi", icon: FileText },
  { to: "/audit-log", label: "Audit log", icon: ShieldCheck },
  { to: "/api-keys", label: "API kljucevi", icon: KeyRound }
];

export function AppShell() {
  const navigate = useNavigate();
  const showDemoBanner = import.meta.env.VITE_APP_ENV !== "production";
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
          {nav.map((item) => {
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
            Demo/development okruzenje - ne unositi stvarne podatke pacijenata.
          </div>
        )}
        <header className="topbar">
          <div className="search">
            <Search size={18} />
            <input placeholder="Pretraži pacijenta, uslugu, status..." />
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
    </div>
  );
}
