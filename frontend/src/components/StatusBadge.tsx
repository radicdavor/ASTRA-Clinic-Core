const labels: Record<string, string> = {
  scheduled: "Zakazano",
  confirmed: "Potvrdeno",
  arrived: "Stigao/la",
  in_progress: "U tijeku",
  completed: "Zavrseno",
  cancelled: "Otkazano",
  no_show: "Nije dosao/la",
  rescheduled: "Premjesteno",
  waiting_for_result: "Ceka nalaz",
  follow_up_needed: "Treba kontrolu",
  open: "Otvoreno",
  active: "Aktivno",
  waiting: "Ceka",
  archived: "Arhivirano"
};

export function statusLabel(status: string) {
  return labels[status] ?? status;
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status status-${status}`}>{statusLabel(status)}</span>;
}
