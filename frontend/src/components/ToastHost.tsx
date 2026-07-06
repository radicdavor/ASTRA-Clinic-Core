import { useEffect, useState } from "react";

type ToastState = {
  id: number;
  message: string;
  tone: "success" | "error";
  title?: string;
};

export function ToastHost() {
  const [toast, setToast] = useState<ToastState | null>(null);

  useEffect(() => {
    let timeout: number | undefined;

    function onToast(event: Event) {
      const detail = (event as CustomEvent<{ message?: string; tone?: "success" | "error"; title?: string }>).detail;
      window.clearTimeout(timeout);
      setToast({ id: Date.now(), message: detail?.message || "Radnja je uspjesno spremljena.", tone: detail?.tone || "success", title: detail?.title });
      timeout = window.setTimeout(() => setToast(null), 5200);
    }

    window.addEventListener("astra:toast", onToast);
    return () => {
      window.clearTimeout(timeout);
      window.removeEventListener("astra:toast", onToast);
    };
  }, []);

  if (!toast) return null;

  return (
    <div className="toast-host" role="status" aria-live="polite">
      <div className={`toast-card ${toast.tone === "error" ? "toast-card-error" : ""}`} key={toast.id}>
        <div>
          <strong>{toast.title ?? (toast.tone === "error" ? "Radnja nije spremljena" : "Radnja je spremljena")}</strong>
          <span>{toast.message}</span>
        </div>
        <button type="button" aria-label="Zatvori obavijest" onClick={() => setToast(null)}>x</button>
      </div>
    </div>
  );
}
