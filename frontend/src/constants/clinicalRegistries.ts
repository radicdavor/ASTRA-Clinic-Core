export const clinicalFormStructuredTypes = new Set([
  "repeatable_group",
  "structured_diagnosis_list",
  "structured_medication_list",
  "structured_anatomical_sites",
  "structured_polyp_list",
  "structured_biopsy_list",
  "structured_intervention_list",
  "structured_specimen_list",
  "structured_segment_findings",
]);

export const interventionLabels = {
  biopsy: "Biopsija",
  polypectomy: "Polipektomija",
  clip_placement: "Klip",
  injection: "Injekcija",
  hemostasis: "Hemostaza",
  dilation: "Dilatacija",
  foreign_body_removal: "Uklanjanje stranog tijela",
  other: "Drugo",
} as const;

export const specimenTypes = ["biopsy", "polyp", "mucosal_resection", "cytology", "other"] as const;
export const retrievalStatuses = ["not_applicable", "not_retrieved", "retrieved", "collected"] as const;
