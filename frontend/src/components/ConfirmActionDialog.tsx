import { ReactNode, useState } from "react";

type ConfirmActionDialogProps = {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: () => void | Promise<void>;
};

export function ConfirmActionDialog({ open, title, message, confirmLabel = "Potvrdi", onCancel, onConfirm }: ConfirmActionDialogProps) {
  const [busy, setBusy] = useState(false);
  if (!open) return null;

  async function confirm() {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <section className="modal-panel action-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="action-confirm-title">
        <header>
          <div>
            <span className="eyebrow">Potvrda radnje</span>
            <h2 id="action-confirm-title">{title}</h2>
          </div>
        </header>
        <p>{message}</p>
        <footer>
          <button type="button" onClick={onCancel} disabled={busy}>Odustani</button>
          <button type="button" className="primary" onClick={confirm} disabled={busy}>{busy ? "Spremanje..." : confirmLabel}</button>
        </footer>
      </section>
    </div>
  );
}
