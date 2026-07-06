import { Patient } from "../types";
import { formatDate } from "./date";

export function formatPatientName(patient?: Patient | null) {
  if (!patient) return "";
  return `${patient.first_name ?? ""} ${patient.last_name ?? ""}`.trim();
}

export function formatPatientIdentity(patient?: Patient | null) {
  if (!patient) return "Nema podataka o pacijentu";
  const parts = [
    patient.date_of_birth ? `roden/a ${formatDate(patient.date_of_birth)}` : null,
    patient.oib ? `OIB ${patient.oib}` : null,
    patient.phone || patient.email || null
  ].filter(Boolean);
  return parts.length ? parts.join(" / ") : "Nema dodatnih identifikacijskih podataka";
}

export function hasStrongPatientIdentifier(patient?: Patient | null) {
  return Boolean(patient?.oib || patient?.date_of_birth || patient?.phone || patient?.email);
}
