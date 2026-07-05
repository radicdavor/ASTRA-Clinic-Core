const labels: Record<string, string> = {
  scheduled: "Zakazano",
  confirmed: "Potvrđeno",
  arrived: "Stigao/la",
  in_progress: "U tijeku",
  completed: "Završeno",
  cancelled: "Otkazano",
  no_show: "Nije došao/la",
  rescheduled: "Premješteno",
  waiting_for_result: "Čeka nalaz",
  follow_up_needed: "Treba kontrolu"
};

export function statusLabel(status: string) {
  return labels[status] ?? status;
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status}`}>{statusLabel(status)}</span>;
}
