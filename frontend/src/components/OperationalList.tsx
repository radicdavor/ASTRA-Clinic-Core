import { ReactNode, useEffect, useId, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Clock3,
  Ellipsis,
  Filter,
  X,
} from "lucide-react";

type StatusTone = "neutral" | "in-progress" | "warning" | "danger" | "success";
type EmptyStateKind = "empty" | "filtered" | "forbidden" | "unavailable";

const statusIcons = {
  neutral: Circle,
  "in-progress": Clock3,
  warning: AlertTriangle,
  danger: AlertCircle,
  success: CheckCircle2,
};

const emptyStateCopy: Record<EmptyStateKind, { title: string; description: string }> = {
  empty: { title: "Nema zapisa", description: "Još nema zapisa za ovaj prikaz." },
  filtered: { title: "Nema rezultata za filtre", description: "Promijenite ili očistite aktivne filtre." },
  forbidden: { title: "Nemate dozvolu", description: "Vaša uloga nema pristup ovom sadržaju." },
  unavailable: { title: "Podaci trenutno nisu dostupni", description: "Pokušajte ponovno ili se obratite podršci." },
};

export function ListPageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <header className="operational-list-header">
      <div>
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action && <div className="operational-list-global-action">{action}</div>}
    </header>
  );
}

export function ListFilterBar({
  children,
  advanced,
  activeFilterCount = 0,
  showClear,
  onClear,
}: {
  children: ReactNode;
  advanced?: ReactNode;
  activeFilterCount?: number;
  showClear?: boolean;
  onClear?: () => void;
}) {
  return (
    <section className="operational-filter-region" aria-label="Filtri">
      <div className="operational-filter-primary">{children}</div>
      {advanced && (
        <details className="operational-filter-advanced">
          <summary>
            <Filter size={16} aria-hidden="true" />
            Napredni filtri
            {activeFilterCount > 0 && <span aria-label={`${activeFilterCount} aktivnih naprednih filtara`}>{activeFilterCount}</span>}
          </summary>
          <div>{advanced}</div>
        </details>
      )}
      {onClear && (showClear ?? activeFilterCount > 0) && (
        <button type="button" className="clear-filters" onClick={onClear}>
          <X size={15} aria-hidden="true" />
          Očisti
        </button>
      )}
    </section>
  );
}

export function StatusSummary({
  label,
  detail,
  tone = "neutral",
}: {
  label: string;
  detail?: string;
  tone?: StatusTone;
}) {
  const Icon = statusIcons[tone];
  const accessibleLabel = detail ? `${label}. ${detail}` : label;
  return (
    <span className={`operational-status operational-status-${tone}`} aria-label={accessibleLabel} title={accessibleLabel}>
      <Icon size={16} aria-hidden="true" />
      <span>
        <strong>{label}</strong>
        {detail && <small>{detail}</small>}
      </span>
    </span>
  );
}

export function RowPrimaryAction({ children }: { children: ReactNode }) {
  return <div className="operational-primary-action">{children}</div>;
}

export function RowMoreMenu({ label, children }: { label: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handlePointer(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function handleKey(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      triggerRef.current?.focus();
    }
    document.addEventListener("mousedown", handlePointer);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handlePointer);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div className="operational-more-menu" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        aria-label={label}
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((current) => !current)}
      >
        <Ellipsis size={18} aria-hidden="true" />
      </button>
      {open && <div className="operational-more-menu-popover" role="menu">{children}</div>}
    </div>
  );
}

export function OperationalRow({
  primary,
  secondary,
  status,
  action,
  more,
}: {
  primary: ReactNode;
  secondary?: ReactNode;
  status: ReactNode;
  action: ReactNode;
  more?: ReactNode;
}) {
  return (
    <article className="operational-row">
      <div className="operational-row-identity">
        <strong>{primary}</strong>
        {secondary && <span>{secondary}</span>}
      </div>
      <div className="operational-row-status">{status}</div>
      <div className="operational-row-actions">
        <RowPrimaryAction>{action}</RowPrimaryAction>
        {more}
      </div>
    </article>
  );
}

export function ProgressiveDetailPanel({
  open,
  title,
  onClose,
  loading = false,
  error,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  loading?: boolean;
  error?: string;
  children?: ReactNode;
}) {
  const titleId = useId();
  const panelRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const focusable = Array.from(panelRef.current.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      ));
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [onClose, open]);

  if (!open) return null;
  return (
    <div className="progressive-detail-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section ref={panelRef} className="progressive-detail-panel" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <header>
          <h2 id={titleId}>{title}</h2>
          <button ref={closeRef} type="button" className="icon-button" aria-label="Zatvori detalj" onClick={onClose}>
            <X size={19} aria-hidden="true" />
          </button>
        </header>
        <div className="progressive-detail-content" aria-live="polite">
          {loading ? <p>Učitavanje detalja…</p> : error ? <p className="form-error" role="alert">{error}</p> : children}
        </div>
      </section>
    </div>
  );
}

export function EmptyState({
  kind = "empty",
  title,
  description,
  action,
}: {
  kind?: EmptyStateKind;
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  const copy = emptyStateCopy[kind];
  return (
    <div className={`operational-empty-state operational-empty-state-${kind}`} role={kind === "unavailable" ? "alert" : "status"}>
      <strong>{title ?? copy.title}</strong>
      <p>{description ?? copy.description}</p>
      {action}
    </div>
  );
}
