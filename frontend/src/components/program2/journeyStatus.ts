export const journeyStatusLabels: Record<string, string> = {
  requested: "Zatraženo", booked: "Termin potvrđen", awaiting_forms: "Čeka obrasce",
  awaiting_documents: "Čeka dokumente", preparation_in_progress: "Priprema u tijeku",
  ready_for_arrival: "Čeka dolazak", arrived: "Pacijent stigao", check_in_review: "Prijem u tijeku",
  ready_for_clinician: "Čeka liječnika", in_encounter: "Pregled u tijeku",
  procedure_completed: "Postupak dovršen", awaiting_billing: "Čeka račun", awaiting_payment: "Čeka plaćanje",
  completed: "Dovršeno", cancelled: "Otkazano", no_show: "Pacijent nije došao", blocked: "Blokirano",
  not_requested: "Nije zatraženo", partial: "Nedostaje dio", complete: "Potpuno",
  review_required: "Treba pregled", not_assigned: "Nije dodijeljeno", assigned: "Dodijeljeno",
  acknowledged: "Potvrđeno", in_progress: "U tijeku", not_arrived: "Nije započeta",
  in_review: "U provjeri", ready: "Spremno", not_started: "Nije započeto", aborted: "Prekinuto",
  not_ready: "Nije spremno", pending: "Čeka potvrdu", confirmed: "Potvrđeno",
  not_applicable: "Nije primjenjivo", invoice_created: "Račun izrađen", adjustment_required: "Treba ispravak",
  closed: "Zatvoreno", not_due: "Nije dospjelo", unpaid: "Neplaćeno",
  partially_paid: "Djelomično plaćeno", paid: "Plaćeno", refunded: "Vraćeno",
  deferred: "Odgođeno", clear: "Bez blokade",
  not_confirmed: "Nije potvrđeno", requires_clinician_review: "Treba liječničku provjeru",
  received: "Zaprimljeno", stored: "Pohranjeno", ocr_pending: "Čeka OCR",
  ocr_completed: "OCR dovršen", classification_pending: "Čeka razvrstavanje", classified: "Razvrstano",
  summary_pending: "Čeka sažetak", summary_generated: "Sažetak izrađen", reviewed: "Pregledano",
  rejected: "Odbijeno", pending_review: "Čeka pregled", accepted: "Prihvaćeno",
  scheduled: "Planirano", queued: "U redu za slanje", sent: "Poslano", delivered: "Dostavljeno",
  failed: "Neuspjelo", open: "Otvoreno", resolved: "Riješeno",
};

export function journeyStatusLabel(value?: string | null) {
  if (!value) return "Nije određeno";
  return journeyStatusLabels[value] ?? value.split("_").join(" ");
}

export function journeyStageLabel(value?: string | null) {
  if (value === "requested") return "Zahtjev zaprimljen";
  return journeyStatusLabel(value);
}

export function activityClockTime(value: string) {
  return value.slice(11, 16);
}
