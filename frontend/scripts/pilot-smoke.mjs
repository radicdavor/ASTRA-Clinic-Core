import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

function read(relativePath) {
  const absolute = resolve(root, relativePath);
  if (!existsSync(absolute)) throw new Error(`Missing ${relativePath}`);
  return readFileSync(absolute, "utf8");
}

function assertIncludes(file, value) {
  const content = read(file);
  if (!content.includes(value)) throw new Error(`${file} does not include ${value}`);
}

function assertNotIncludes(file, value) {
  const content = read(file);
  if (content.includes(value)) throw new Error(`${file} must not include ${value}`);
}

function unique(values) {
  return [...new Set(values)];
}

[
  "src/pages/Dashboard.tsx",
  "src/pages/AppointmentDetail.tsx",
  "src/pages/ClinicalDocuments.tsx",
  "src/pages/ClinicalDocumentDetail.tsx",
  "src/pages/Episodes.tsx",
  "src/pages/EpisodeForm.tsx",
  "src/pages/EpisodeDetail.tsx",
  "src/pages/PurchaseOrders.tsx",
  "src/pages/Invoices.tsx",
  "src/pages/ApiKeys.tsx",
  "src/pages/Readiness.tsx",
  "src/pages/Reception.tsx",
  "src/components/AppShell.tsx",
  "src/components/AuditTimeline.tsx",
  "src/components/ToastHost.tsx",
  "src/components/HelpHint.tsx",
  "src/components/ActionButton.tsx",
  "src/components/DateInput.tsx",
  "src/components/SourceBadge.tsx",
  "src/components/workspace/WorkspaceLayout.tsx",
  "src/components/workspace/WorkspaceHeader.tsx",
  "src/components/workspace/WorkspaceSection.tsx",
  "src/components/workspace/WorkspaceTabs.tsx",
  "src/utils/patientIdentity.ts",
].forEach(read);

assertIncludes("src/routes/AppRoutes.tsx", "/appointments/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/patients/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/episodes");
assertIncludes("src/routes/AppRoutes.tsx", "/episodes/new");
assertIncludes("src/routes/AppRoutes.tsx", "/episodes/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/clinical-documents");
assertIncludes("src/routes/AppRoutes.tsx", "/clinical-documents/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/api-keys");
assertIncludes("src/routes/AppRoutes.tsx", "/readiness");
assertIncludes("src/routes/AppRoutes.tsx", "/reception");
assertIncludes("src/components/AppShell.tsx", "/api/public-config");
assertIncludes("src/components/AppShell.tsx", "Demo/development okruzenje");
assertIncludes("src/components/AppShell.tsx", "Spremnost");
assertIncludes("src/components/AppShell.tsx", "Dokumenti");
assertIncludes("src/components/AppShell.tsx", "Prijem");
assertNotIncludes("src/components/AppShell.tsx", "Epizode");
assertIncludes("src/components/SourceBadge.tsx", "/clinical-documents/${source.document_id}");
assertIncludes("src/components/ToastHost.tsx", "Radnja je spremljena");
assertIncludes("src/components/ToastHost.tsx", "Zatvori obavijest");
assertIncludes("src/components/DateInput.tsx", "dd/mm/yyyy");
assertIncludes("src/utils/date.ts", "`${match[3]}/${match[2]}/${match[1]}`");
[
  "src/pages/PatientForm.tsx",
  "src/pages/AppointmentForm.tsx",
  "src/pages/Dashboard.tsx",
  "src/pages/EpisodeForm.tsx",
  "src/pages/EpisodeDetail.tsx",
  "src/pages/PurchaseOrders.tsx",
].forEach((file) => assertNotIncludes(file, "type=\"date\""));
assertIncludes("src/api/client.ts", "Pacijent je spremljen.");
assertIncludes("src/api/client.ts", "Klinicki dokument je spremljen.");
assertIncludes("src/api/client.ts", "Epizoda je spremljena.");
assertIncludes("src/api/client.ts", "Uplata je evidentirana.");
assertIncludes("src/api/client.ts", "Status termina je azuriran.");
assertIncludes("src/api/client.ts", "Prijava je istekla");
assertIncludes("src/api/client.ts", "window.location.href = \"/login\"");
assertIncludes("src/pages/AppointmentDetail.tsx", "Obavezni varijabilni materijal mora imati kolicinu.");
assertIncludes("src/pages/PurchaseOrders.tsx", "Kolicina zaprimanja ne smije biti veca od preostale kolicine.");
assertIncludes("src/pages/Invoices.tsx", "remaining");
assertIncludes("src/pages/ApiKeys.tsx", "opasni scopeovi");
assertIncludes("src/pages/Invoices.tsx", "Demo fiskalizacija - nije stvarna fiskalizacija.");
assertIncludes("src/components/AuditTimeline.tsx", "before_json");
assertIncludes("src/components/AuditTimeline.tsx", "actionLabels");
assertIncludes("src/components/AuditTimeline.tsx", "entityRoute");
assertIncludes("src/components/AuditTimeline.tsx", "ClinicalEpisode");
assertIncludes("src/pages/PatientForm.tsx", "OIB");
assertIncludes("src/pages/PatientForm.tsx", "Spremi pacijenta");
assertIncludes("src/pages/PatientForm.tsx", "possible-duplicates");
assertIncludes("src/pages/PatientForm.tsx", "Moguci duplikati pacijenta");
assertIncludes("src/pages/AppointmentForm.tsx", "Ime, prezime ili OIB");
assertIncludes("src/pages/AppointmentForm.tsx", "selectedPatient");
assertIncludes("src/pages/AppointmentForm.tsx", "return_to");
assertIncludes("src/pages/AppointmentForm.tsx", "appointment");
assertIncludes("src/pages/AppointmentForm.tsx", "/appointments/${appointment.id}");
assertIncludes("src/pages/AppointmentForm.tsx", "service-context");
assertIncludes("src/pages/AppointmentForm.tsx", "formatPatientIdentity");
assertIncludes("src/pages/AppointmentForm.tsx", "Klinicka epizoda");
assertIncludes("src/pages/AppointmentForm.tsx", "Bez epizode");
assertNotIncludes("src/pages/AppointmentForm.tsx", "Kreiraj novu epizodu");
assertIncludes("src/pages/PatientForm.tsx", "return_to");
assertIncludes("src/pages/PatientForm.tsx", "/appointments/new?patient_id=${patient.id}");
assertIncludes("src/pages/PatientDetail.tsx", "WorkspaceHeader");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/clinical-documents");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/clinical-summary");
assertIncludes("src/pages/PatientDetail.tsx", "KnowledgeCard");
assertIncludes("src/pages/PatientDetail.tsx", "knowledge-sidebar");
assertIncludes("src/pages/PatientDetail.tsx", "Dokumenti koji cekaju pregled");
assertIncludes("src/pages/PatientDetail.tsx", "SourceBadge");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/appointments");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/invoices");
assertIncludes("src/pages/PatientDetail.tsx", "Moguci duplikati pacijenta");
assertIncludes("src/pages/PatientDetail.tsx", "summary-strip");
assertIncludes("src/pages/PatientDetail.tsx", "Sazetak");
assertIncludes("src/pages/PatientDetail.tsx", "Klinicki dokumenti");
assertIncludes("src/pages/PatientDetail.tsx", "AI sazetak pacijenta");
assertIncludes("src/pages/PatientDetail.tsx", "/clinical-summary/generate-draft");
assertIncludes("src/pages/PatientDetail.tsx", "/clinical-summary/review");
assertIncludes("src/pages/PatientDetail.tsx", "AI draft - potreban je lijecnicki pregled.");
assertIncludes("src/pages/PatientDetail.tsx", "Zadnji termin");
assertIncludes("src/pages/PatientDetail.tsx", "Otvoreni racuni");
assertIncludes("src/pages/Patients.tsx", "/patients/${row.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "/patients/${appointment.data.patient.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "/episodes/${appointment.data.episode.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "Termin nije povezan s klinickom epizodom.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Zavrsi uz potrosnju");
assertIncludes("src/pages/Episodes.tsx", "/api/episodes");
assertIncludes("src/pages/EpisodeForm.tsx", "/api/episodes");
assertIncludes("src/pages/EpisodeDetail.tsx", "WorkspaceLayout");
assertIncludes("src/pages/EpisodeDetail.tsx", "AuditTimeline");
assertIncludes("src/pages/EpisodeDetail.tsx", "/api/episodes/${id}/appointments");
assertIncludes("src/pages/EpisodeDetail.tsx", "/api/episodes/${id}/clinical-plans");
assertIncludes("src/pages/EpisodeDetail.tsx", "/api/episodes/${id}/clinical-timeline");
assertIncludes("src/pages/EpisodeDetail.tsx", "AI prijedlog");
assertIncludes("src/pages/EpisodeDetail.tsx", "Potvrdi");
assertIncludes("src/pages/EpisodeDetail.tsx", "Uredi");
assertIncludes("src/pages/EpisodeDetail.tsx", "Odbij");
assertIncludes("src/pages/EpisodeDetail.tsx", "activePlan");
assertIncludes("src/pages/EpisodeDetail.tsx", "physician_confirmed");
assertIncludes("src/pages/EpisodeDetail.tsx", "physician_conclusion");
assertIncludes("src/types/index.ts", "physician_conclusion");
assertIncludes("src/pages/EpisodeDetail.tsx", "Ne mijenja epizodu");
assertIncludes("src/pages/ClinicalDocuments.tsx", "/api/clinical-documents/upload");
assertIncludes("src/pages/ClinicalDocuments.tsx", "Pretraga po imenu, OIB-u, telefonu ili e-posti");
assertIncludes("src/pages/ClinicalDocuments.tsx", "selectedPatient");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/extract");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/review");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/reject-summary");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Spremi izmjene");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "AI prijedlog, nije sluzbeno");
assertIncludes("src/components/ActionButton.tsx", "requiresConfirm");
assertIncludes("src/components/ActionButton.tsx", "confirmMessage");
assertIncludes("src/utils/patientIdentity.ts", "formatPatientIdentity");
assertIncludes("src/utils/patientIdentity.ts", "hasStrongPatientIdentifier");
assertIncludes("src/pages/Invoices.tsx", "Demo fiskalizacija - nije stvarna fiskalizacija.");
assertIncludes("src/pages/ApiKeys.tsx", "opasni scopeovi");
assertIncludes("src/pages/AppointmentDetail.tsx", "Potvrditi zavrsetak termina");
assertIncludes("src/pages/PurchaseOrders.tsx", "Potvrditi zaprimanje robe");
assertIncludes("src/pages/Readiness.tsx", "/api/readiness");
assertIncludes("src/pages/Readiness.tsx", "Ne mijenja podatke");
assertIncludes("src/pages/Readiness.tsx", "target_path");
assertIncludes("src/pages/Readiness.tsx", "target_label");
assertIncludes("src/pages/Readiness.tsx", "Sljedeci korak");
assertIncludes("src/pages/Readiness.tsx", "decision_impact");
assertIncludes("src/pages/Readiness.tsx", "Blokira demo");
assertIncludes("src/pages/Readiness.tsx", "readiness-detail");
assertIncludes("src/pages/Reception.tsx", "/api/reception/day");
assertIncludes("src/pages/Reception.tsx", "Dan");
assertIncludes("src/pages/Reception.tsx", "Tjedan");
assertIncludes("src/pages/Reception.tsx", "Sve klinike");
assertIncludes("src/pages/Reception.tsx", "Slobodno");
assertIncludes("src/pages/Reception.tsx", "reception-card");
assertIncludes("src/pages/Reception.tsx", "Oznaci kao pristigao");
assertIncludes("src/pages/Reception.tsx", "/patients/${selected.patient_id}");
assertIncludes("src/pages/Reception.tsx", "/appointments/${selected.id}");
assertIncludes("src/pages/Readiness.tsx", "Nepregledani dokumenti ne ulaze u sluzbeni sazetak pacijenta.");
assertIncludes("../backend/app/api/routes/core.py", "/clinical-documents?review_status=needs_physician_review");
assertIncludes("../backend/app/api/routes/core.py", "patient_summary_stale");

const backendCore = read("../backend/app/api/routes/core.py");
const appRoutes = read("src/routes/AppRoutes.tsx");
const readinessTargetPaths = unique([...backendCore.matchAll(/target_path="([^"]+)"/g)].map((match) => match[1]));
const readinessTargetLabels = unique([...backendCore.matchAll(/target_label="([^"]+)"/g)].map((match) => match[1]));

if (readinessTargetPaths.length === 0) {
  throw new Error("No readiness target_path values found in backend readiness endpoint");
}

for (const targetPath of readinessTargetPaths) {
  const routePath = targetPath.split("?")[0];
  if (!appRoutes.includes(`path="${routePath}"`)) {
    throw new Error(`Readiness target path ${targetPath} is not registered in AppRoutes.tsx`);
  }
}

for (const targetLabel of readinessTargetLabels) {
  if (!targetLabel.trim()) {
    throw new Error("Readiness target_label must not be empty");
  }
}

console.log("Frontend pilot smoke passed.");
