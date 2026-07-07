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
assertIncludes("../backend/app/api/routes/patients.py", '"/patients"');
assertIncludes("../backend/app/api/routes/patients.py", '"/patients/{patient_id}/appointments"');
assertIncludes("../backend/app/main.py", "patients.router");
assertIncludes("../backend/app/api/routes/appointments.py", '"/appointments"');
assertIncludes("../backend/app/api/routes/appointments.py", '"/schedule/day"');
assertIncludes("../backend/app/api/routes/appointments.py", '"/appointments/{appointment_id}/clinical-readiness-preview"');
assertIncludes("../backend/app/main.py", "appointments.router");
assertIncludes("../backend/app/api/routes/reception.py", '"/reception/day"');
assertIncludes("../backend/app/api/routes/reception.py", '"/appointments/{appointment_id}/mark-arrived"');
assertIncludes("../backend/app/main.py", "reception.router");
assertIncludes("../backend/app/api/routes/catalog.py", '"/services"');
assertIncludes("../backend/app/api/routes/catalog.py", '"/modules"');
assertIncludes("../backend/app/api/routes/catalog.py", '"/providers"');
assertIncludes("../backend/app/api/routes/catalog.py", '"/rooms"');
assertIncludes("../backend/app/api/routes/catalog.py", '"/clinics"');
assertIncludes("../backend/app/api/routes/audit.py", '"/audit-log"');
assertIncludes("../backend/app/api/routes/search.py", '"/search"');
assertIncludes("../backend/app/main.py", "catalog.router");
assertIncludes("../backend/app/main.py", "audit.router");
assertIncludes("../backend/app/main.py", "search.router");
assertNotIncludes("../backend/app/main.py", "core.router");
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
assertIncludes("src/pages/PatientDetail.tsx", "Dokumenti cekaju lijecnicki pregled");
assertIncludes("src/pages/PatientDetail.tsx", "SourceBadge");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/appointments");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/invoices");
assertIncludes("src/pages/PatientDetail.tsx", "Moguci duplikati pacijenta");
assertIncludes("src/pages/PatientDetail.tsx", "summary-strip");
assertIncludes("src/pages/PatientDetail.tsx", "Sazetak");
assertIncludes("src/pages/PatientDetail.tsx", "Klinicki dokumenti");
assertIncludes("src/pages/PatientDetail.tsx", "Pregledani sazetak");
assertIncludes("src/pages/PatientDetail.tsx", "AI draft sazetka");
assertIncludes("src/pages/PatientDetail.tsx", "Sluzbeno source-linked znanje");
assertIncludes("src/pages/PatientDetail.tsx", "Sazetak je zastario");
assertIncludes("src/pages/PatientDetail.tsx", "Sazetak je pomocni prikaz i nije izvor istine.");
assertIncludes("src/pages/PatientDetail.tsx", "Izvor istine su pregledani, source-linked klinicki dokumenti.");
assertIncludes("src/pages/PatientDetail.tsx", "Sluzbeni sazetak nastaje tek nakon lijecnickog pregleda dokumenta.");
assertIncludes("src/pages/PatientDetail.tsx", "Ovo su pregledane, source-linked stavke koje zahtijevaju klinicku paznju. Nisu automatske odluke niti zadaci.");
assertIncludes("src/pages/PatientDetail.tsx", "Nisu zadaci niti odluke; potrebno je pregledati izvore.");
assertIncludes("src/pages/PatientDetail.tsx", "/clinical-summary/generate-draft");
assertIncludes("src/pages/PatientDetail.tsx", "/clinical-summary/review");
assertIncludes("../backend/app/api/routes/patient_clinical_summary.py", '"/patients/{patient_id}/clinical-summary"');
assertIncludes("../backend/app/api/routes/patient_clinical_summary.py", '"/patients/{patient_id}/clinical-summary/generate-draft"');
assertIncludes("../backend/app/main.py", "patient_clinical_summary.router");
assertIncludes("src/pages/PatientDetail.tsx", "AI draft - potreban je lijecnicki pregled.");
assertIncludes("src/pages/PatientDetail.tsx", "Zadnji termin");
assertIncludes("src/pages/PatientDetail.tsx", "Otvoreni racuni");
assertIncludes("src/pages/Patients.tsx", "/patients/${row.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "/patients/${appointment.data.patient.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "/episodes/${appointment.data.episode.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "Termin nije povezan s klinickom epizodom.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Klinicka spremnost - preview");
assertIncludes("src/pages/AppointmentDetail.tsx", "Read-only prikaz mogucih uvjeta za ovaj planirani klinicki cin. Ne donosi odluke i ne blokira postupak.");
assertIncludes("src/pages/AppointmentDetail.tsx", "PREVIEW");
assertIncludes("src/pages/AppointmentDetail.tsx", "Clinical readiness preview trenutno nije dostupan.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Template");
assertIncludes("src/pages/AppointmentDetail.tsx", "Binding");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ovo nije produkcijsko pravilo.");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Clinical readiness template je demo/pilot staticna definicija, nije produkcijsko pravilo.");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Nema specificnog clinical readiness templatea za ovu uslugu; koristi se genericki preview.");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Koristi se demo/pilot template");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "select_clinical_readiness_template");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "keyword_fallback");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "generic_fallback");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "GASTROSCOPY_TEMPLATE");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "COLONOSCOPY_TEMPLATE");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "AI cleared");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Mark ready");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Procedure allowed");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Override readiness");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Create task");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Bind template");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Edit template");
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
assertIncludes("../backend/app/api/routes/episodes.py", '"/episodes"');
assertIncludes("../backend/app/api/routes/episodes.py", '"/episodes/{episode_id}/clinical-plans"');
assertIncludes("../backend/app/api/routes/episodes.py", '"/clinical-plans/{plan_id}/confirm"');
assertIncludes("../backend/app/main.py", "episodes.router");
assertIncludes("src/pages/ClinicalDocuments.tsx", "/api/clinical-documents/upload");
assertIncludes("src/pages/ClinicalDocuments.tsx", "Pretraga po imenu, OIB-u, telefonu ili e-posti");
assertIncludes("src/pages/ClinicalDocuments.tsx", "selectedPatient");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/extract");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/review");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/reject-summary");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Spremi izmjene");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Izvorni dokument");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "AI prijedlog ekstrakcije");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Lijecnicki pregled");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Pokreni AI ekstrakciju");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Potvrdi lijecnicki pregled");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Odbij AI prijedlog");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Uklanja AI sazetak i strukturirane stavke. Izvorni dokument ostaje vidljiv i moze se rucno pregledati.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Ovaj dokument jos ne doprinosi sluzbenom klinickom znanju pacijenta.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Ovaj dokument je lijecnicki pregledan i moze doprinositi source-linked znanju pacijenta.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "AI prijedlog je odbijen. Izvorni dokument ostaje dostupan za rucni pregled.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Izvor istine su pregledani, source-linked klinicki dokumenti.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "/evidence-timeline");
assertIncludes("../backend/app/api/routes/clinical_documents.py", '"/clinical-documents"');
assertIncludes("../backend/app/api/routes/clinical_documents.py", '"/patients/{patient_id}/clinical-documents"');
assertIncludes("../backend/app/main.py", "clinical_documents.router");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Klinicki evidence timeline");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Ovo je citljiv prikaz audit dogadjaja vezanih uz ovaj dokument. Ne stvara nove klinicke cinjenice.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Nema audit dogadjaja za ovaj dokument.");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Nema sluzbeni knowledge ucinak");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Moze omoguciti sluzbeno znanje nakon pregleda");
assertIncludes("src/pages/ClinicalDocumentDetail.tsx", "Otvori sirovi Audit Log");
assertIncludes("src/components/ActionButton.tsx", "requiresConfirm");
assertIncludes("src/components/ActionButton.tsx", "confirmMessage");
assertIncludes("src/utils/patientIdentity.ts", "formatPatientIdentity");
assertIncludes("src/utils/patientIdentity.ts", "hasStrongPatientIdentifier");
assertIncludes("src/pages/Invoices.tsx", "Demo fiskalizacija - nije stvarna fiskalizacija.");
assertIncludes("src/pages/ApiKeys.tsx", "opasni scopeovi");
assertIncludes("src/pages/AppointmentDetail.tsx", "Potvrditi zavrsetak termina");
assertIncludes("src/pages/PurchaseOrders.tsx", "Potvrditi zaprimanje robe");
assertIncludes("src/pages/Readiness.tsx", "/api/readiness");
assertIncludes("../backend/app/api/routes/system.py", '"/public-config"');
assertIncludes("../backend/app/main.py", "system.router");
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
assertNotIncludes("src/pages/Readiness.tsx", "Clinical Readiness Gate");
assertNotIncludes("src/pages/Readiness.tsx", "Ready with Warning");
assertNotIncludes("src/pages/Readiness.tsx", "Not Ready");
assertIncludes("../backend/app/api/routes/readiness.py", '"/readiness"');
assertIncludes("../backend/app/main.py", "readiness.router");
assertIncludes("../backend/app/services/readiness.py", "/clinical-documents?review_status=needs_physician_review");
assertIncludes("../backend/app/services/readiness.py", "patient_summary_stale");
assertIncludes("../backend/app/services/readiness.py", "Episode Engine je eksperimentalno/deferred");

const backendReadiness = read("../backend/app/services/readiness.py");
const appRoutes = read("src/routes/AppRoutes.tsx");
const readinessTargetPaths = unique([...backendReadiness.matchAll(/target_path="([^"]+)"/g)].map((match) => match[1]));
const readinessTargetLabels = unique([...backendReadiness.matchAll(/target_label="([^"]+)"/g)].map((match) => match[1]));

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
