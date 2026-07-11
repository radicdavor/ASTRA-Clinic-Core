import { ReactNode, useEffect, useId, useRef } from "react";
import { X } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function RouteModal({ title, children }: { title: string; children: ReactNode }) {
  const navigate = useNavigate();
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") navigate(-1);
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

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previousFocus?.focus();
    };
  }, [navigate]);

  return (
    <div className="route-modal-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) navigate(-1);
    }}>
      <section ref={panelRef} className="route-modal-panel" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <header className="route-modal-header">
          <div>
            <span>ASTRA radni prozor</span>
            <strong id={titleId}>{title}</strong>
          </div>
          <button ref={closeRef} type="button" className="icon-button" aria-label="Zatvori prozor" onClick={() => navigate(-1)}>
            <X size={19} aria-hidden="true" />
          </button>
        </header>
        <div className="route-modal-content">{children}</div>
      </section>
    </div>
  );
}
