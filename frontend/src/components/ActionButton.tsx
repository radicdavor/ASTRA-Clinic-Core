import { ButtonHTMLAttributes, MouseEvent, ReactNode, useState } from "react";
import { HelpHint } from "./HelpHint";

type ActionButtonProps = {
  variant: "info" | "create" | "update" | "workflow" | "danger" | "ai" | "admin";
  helpTitle?: string;
  help?: ReactNode;
  requiresConfirm?: boolean;
  confirmMessage?: string;
  children: ReactNode;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onClick"> & {
  onClick?: () => void | Promise<void>;
};

export function ActionButton({ variant, helpTitle, help, requiresConfirm, confirmMessage, children, className = "", onClick, type = "button", ...props }: ActionButtonProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function runAction() {
    setBusy(true);
    try {
      await onClick?.();
      setConfirmOpen(false);
    } finally {
      setBusy(false);
    }
  }

  async function handleClick(event: MouseEvent<HTMLButtonElement>) {
    if (requiresConfirm) {
      event.preventDefault();
      setConfirmOpen(true);
      return;
    }
    await onClick?.();
  }

  return (
    <span className="action-with-help">
      <button type={type} className={`action-button action-${variant} ${className}`.trim()} onClick={onClick ? handleClick : undefined} {...props}>
        {children}
      </button>
      {help && <HelpHint title={helpTitle ?? String(children)}>{help}</HelpHint>}
      {confirmOpen && (
        <div className="modal-backdrop">
          <section className="modal-panel action-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="action-confirm-title">
            <header>
              <div>
                <span className="eyebrow">Potvrda radnje</span>
                <h2 id="action-confirm-title">{helpTitle ?? "Potvrditi radnju"}</h2>
              </div>
            </header>
            <p>{confirmMessage ?? "Potvrditi radnju?"}</p>
            <footer>
              <button type="button" onClick={() => setConfirmOpen(false)} disabled={busy}>Odustani</button>
              <button type="button" className="primary" onClick={runAction} disabled={busy}>{busy ? "Spremanje..." : "Potvrdi"}</button>
            </footer>
          </section>
        </div>
      )}
    </span>
  );
}
