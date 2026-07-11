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
  "src/program1/pages/SyntheticReviewWorkspace.tsx",
  "src/program1/pages/SyntheticEvaluationRunner.tsx",
  "src/program1/data/syntheticEvaluation.ts",
  "src/program1/types/syntheticEvaluation.ts",
  "src/program1/components/SyntheticEvaluationBoundary.tsx",
  "src/program1/components/SyntheticEvaluationPreflight.tsx",
  "src/program1/components/SyntheticEvaluationTaskList.tsx",
  "scripts/program1-evaluation-readiness.mjs",
  "src/program1/data/syntheticScenarios.ts",
  "src/program1/types/syntheticReview.ts",
  "src/program1/utils/syntheticReviewSelectors.ts",
  "src/program1/utils/syntheticReviewValidation.ts",
  "src/program1/components/SyntheticSafetyBanner.tsx",
  "src/program1/components/SyntheticScenarioSelector.tsx",
  "src/program1/components/SyntheticScenarioOverview.tsx",
  "src/program1/components/SyntheticTimeline.tsx",
  "src/program1/components/SyntheticEvidenceList.tsx",
  "src/program1/components/SyntheticFindingsList.tsx",
  "src/program1/components/SyntheticReadinessPanel.tsx",
  "src/program1/components/SyntheticLimitations.tsx",
  "src/program1/components/SyntheticComparison.tsx",
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
assertIncludes("src/routes/AppRoutes.tsx", "/program1/synthetic-review");
assertIncludes("src/routes/AppRoutes.tsx", "/program1/synthetic-evaluation");
assertIncludes("src/routes/AppRoutes.tsx", "/reception");
assertIncludes("src/components/AppShell.tsx", "/api/public-config");
assertIncludes("src/components/AppShell.tsx", "Demo/development okruzenje");
assertIncludes("src/components/AppShell.tsx", "Spremnost");
assertIncludes("src/components/AppShell.tsx", "Program 1 Demo");
assertIncludes("src/components/AppShell.tsx", "Program 1 Evaluacija");
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
assertIncludes("src/pages/AppointmentDetail.tsx", "Savjetodavni signali");
assertIncludes("src/pages/AppointmentDetail.tsx", "Za ljudski pregled");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nije klinicko odobrenje");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ne mijenja status termina");
assertIncludes("src/pages/AppointmentDetail.tsx", "Non-blocking signal");
assertIncludes("src/pages/AppointmentDetail.tsx", "To nije klinicka odluka i ne mijenja status termina.");
assertIncludes("src/pages/AppointmentDetail.tsx", "ne pokrece radnju");
assertIncludes("src/pages/AppointmentDetail.tsx", "PREVIEW");
assertIncludes("src/pages/AppointmentDetail.tsx", "Clinical readiness preview trenutno nije dostupan.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Template");
assertIncludes("src/pages/AppointmentDetail.tsx", "Verzija");
assertIncludes("src/pages/AppointmentDetail.tsx", "Binding");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot");
assertIncludes("src/pages/AppointmentDetail.tsx", "nije implementiran");
assertIncludes("src/pages/AppointmentDetail.tsx", "snapshot_warning");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ovo nije produkcijsko pravilo.");
assertIncludes("src/types/index.ts", "ClinicalReadinessSnapshotHistoryItem");
assertIncludes("src/types/index.ts", "ClinicalReadinessSnapshotHistoryResponse");
assertIncludes("src/api/client.ts", "getClinicalReadinessSnapshotHistory");
assertIncludes("src/api/client.ts", "getClinicalReadinessSnapshotDetail");
assertIncludes("src/api/client.ts", "captureClinicalReadinessSnapshot");
assertIncludes("src/api/client.ts", "supersedeClinicalReadinessSnapshot");
assertIncludes("src/api/client.ts", "/clinical-readiness-snapshots");
assertNotIncludes("src/api/client.ts", "acknowledgeClinicalReadiness");
assertNotIncludes("src/api/client.ts", "createClinicalReadinessAcknowledgment");
assertNotIncludes("src/api/client.ts", "/clinical-readiness-acknowledgments");
assertIncludes("src/types/index.ts", "ClinicalReadinessAcknowledgmentListResponse");
assertIncludes("src/types/index.ts", "ClinicalReadinessAcknowledgmentDetailResponse");
assertIncludes("src/api/client.ts", "getClinicalReadinessAcknowledgments");
assertIncludes("src/api/client.ts", "getClinicalReadinessAcknowledgmentDetail");
assertIncludes("src/api/client.ts", "/clinical-readiness/acknowledgments");
assertNotIncludes("src/api/client.ts", "postClinicalReadinessAcknowledgment");
assertIncludes("src/types/index.ts", "ClinicalFindingListResponse");
assertIncludes("src/types/index.ts", "ClinicalFindingDetailResponse");
assertIncludes("src/api/client.ts", "getClinicalFindings");
assertIncludes("src/api/client.ts", "getClinicalFindingDetail");
assertIncludes("src/api/client.ts", "/clinical-findings");
assertIncludes("src/types/index.ts", "ClinicalEvidenceTimelineListResponse");
assertIncludes("src/types/index.ts", "ClinicalEvidenceTimelineEventPreview");
assertIncludes("src/api/client.ts", "getClinicalEvidenceTimeline");
assertIncludes("src/api/client.ts", "/clinical-evidence-timeline");
assertNotIncludes("src/api/client.ts", "postClinicalEvidenceTimeline");
assertNotIncludes("src/api/client.ts", "createClinicalEvidenceTimeline");
assertNotIncludes("src/api/client.ts", "updateClinicalEvidenceTimeline");
assertNotIncludes("src/api/client.ts", "deleteClinicalEvidenceTimeline");
assertNotIncludes("src/api/client.ts", "createClinicalFinding");
assertNotIncludes("src/api/client.ts", "updateClinicalFinding");
assertNotIncludes("src/api/client.ts", "deleteClinicalFinding");
assertNotIncludes("src/api/client.ts", "createClinicalFindingExtraction");
assertNotIncludes("src/api/client.ts", "extractClinicalFinding");
assertNotIncludes("src/api/client.ts", "createClinicalOpenQuestion");
assertNotIncludes("src/api/client.ts", "updateClinicalOpenQuestion");
assertNotIncludes("src/api/client.ts", "/open-questions");
assertNotIncludes("src/pages/PatientDetail.tsx", "FindingExtraction");
assertNotIncludes("src/pages/PatientDetail.tsx", "Pokreni extraction nalaza");
assertNotIncludes("src/pages/PatientDetail.tsx", "ClinicalOpenQuestion");
assertNotIncludes("src/pages/PatientDetail.tsx", "Otvori pitanje iz nalaza");
assertIncludes("src/pages/PatientDetail.tsx", "Nalazi povezani s izvorom");
assertIncludes("src/pages/PatientDetail.tsx", "Klinicka vremenska crta");
assertIncludes("src/pages/PatientDetail.tsx", "Source-linked prikaz klinickih dogadjaja.");
assertIncludes("src/pages/PatientDetail.tsx", "Nije klinicka odluka, ne stvara zadatak i ne salje poruku pacijentu.");
assertIncludes("src/pages/PatientDetail.tsx", "Ne mijenja status termina.");
assertIncludes("src/pages/PatientDetail.tsx", "Nema prikazanih source-linked timeline dogadjaja.");
assertIncludes("src/pages/PatientDetail.tsx", "Klinicka vremenska crta trenutno nije dostupna.");
assertIncludes("src/pages/PatientDetail.tsx", "Nemate dozvolu za prikaz klinicke vremenske crte.");
assertIncludes("src/pages/PatientDetail.tsx", "timelineEventTypeLabel");
assertIncludes("src/pages/PatientDetail.tsx", "Snapshot spremnosti spremljen");
assertIncludes("src/pages/PatientDetail.tsx", "Izvor nije dovoljno specificiran - provjeriti originalni zapis.");
assertIncludes("src/pages/PatientDetail.tsx", "Ovo su source-linked zapisi za pregled.");
assertIncludes("src/pages/PatientDetail.tsx", "Nalaz nije dijagnoza bez lijecnicke potvrde.");
assertIncludes("src/pages/PatientDetail.tsx", "Ovaj prikaz ne stvara zadatak i ne salje poruku pacijentu.");
assertIncludes("src/pages/PatientDetail.tsx", "Za klinicku interpretaciju odgovoran je lijecnik.");
assertIncludes("src/pages/PatientDetail.tsx", "Nema prikazanih source-linked finding zapisa.");
assertIncludes("src/pages/PatientDetail.tsx", "To ne znaci da nema klinickih rizika");
assertIncludes("src/pages/PatientDetail.tsx", "Nalazi trenutno nisu dostupni.");
assertIncludes("src/pages/PatientDetail.tsx", "Nemate dozvolu za prikaz source-linked nalaza.");
assertIncludes("src/pages/PatientDetail.tsx", "findingLifecycleStatusLabel");
assertIncludes("src/pages/PatientDetail.tsx", "Potrebna odluka lijecnika");
assertIncludes("src/pages/PatientDetail.tsx", "Izvor nije dovoljno specificiran - provjeriti originalni dokument.");
assertIncludes("src/pages/PatientDetail.tsx", "Za ljudski pregled");
assertNotIncludes("src/pages/PatientDetail.tsx", "dijagnosticirano");
assertNotIncludes("src/pages/PatientDetail.tsx", "lijeceno");
assertNotIncludes("src/pages/PatientDetail.tsx", "odobreno");
assertNotIncludes("src/pages/PatientDetail.tsx", "clearance");
assertNotIncludes("src/pages/PatientDetail.tsx", "override");
assertNotIncludes("src/pages/PatientDetail.tsx", "resolved by AI");
assertNotIncludes("src/pages/PatientDetail.tsx", "task created");
assertNotIncludes("src/pages/PatientDetail.tsx", "outcome proven");
assertNotIncludes("src/pages/PatientDetail.tsx", "patient notified");
assertNotIncludes("src/pages/PatientDetail.tsx", "automatski zakljuceno");
assertNotIncludes("src/pages/PatientDetail.tsx", "Task");
assertNotIncludes("src/pages/PatientDetail.tsx", "Outcome Evidence");
assertNotIncludes("src/pages/PatientDetail.tsx", "Potvrdi nalaz");
assertNotIncludes("src/pages/PatientDetail.tsx", "Potvrdi timeline");
assertNotIncludes("src/pages/PatientDetail.tsx", "Odobri timeline");
assertNotIncludes("src/pages/PatientDetail.tsx", "Clear timeline");
assertNotIncludes("src/pages/PatientDetail.tsx", "Override timeline");
assertNotIncludes("src/pages/PatientDetail.tsx", "Timeline action");
assertNotIncludes("src/pages/PatientDetail.tsx", "Odobri nalaz");
assertNotIncludes("src/pages/PatientDetail.tsx", "Clear finding");
assertNotIncludes("src/pages/PatientDetail.tsx", "Override finding");
assertNotIncludes("src/pages/PatientDetail.tsx", "Create task");
assertNotIncludes("src/pages/PatientDetail.tsx", "Posalji pacijentu");
assertIncludes("src/pages/AppointmentDetail.tsx", "Pregledani savjetodavni signali");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ovo je zapis ljudskog pregleda savjetodavnog signala. Nije klinicko odobrenje. Ne mijenja status termina.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ne salje poruku pacijentu.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Za klinicku interpretaciju odgovoran je lijecnik.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nema spremljenih zapisa ljudskog pregleda savjetodavnih signala za ovaj termin.");
assertIncludes("src/pages/AppointmentDetail.tsx", "To ne znaci da nema otvorenih readiness pitanja");
assertIncludes("src/pages/AppointmentDetail.tsx", "Zapisi pregleda trenutno nisu dostupni. To ne znaci da je klinicka spremnost potvrdjena ili odbijena.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nemate dozvolu za prikaz zapisa ljudskog pregleda savjetodavnih signala.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ostali podaci u radnom prostoru ostaju dostupni prema vasim dozvolama.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Povezano sa snapshot zapisom");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot ostaje nepromijenjen.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Pregled ne mijenja spremljeni snapshot.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Razlog kao biljeska pregleda");
assertIncludes("src/pages/AppointmentDetail.tsx", "Razlog je prikazan kao biljeska pregleda, ne kao klinicki zakljucak.");
assertIncludes("src/pages/AppointmentDetail.tsx", "aria-live=\"polite\"");
assertIncludes("src/pages/AppointmentDetail.tsx", "Za ljudsku interpretaciju.");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Potvrdi pregled");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "acknowledge");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Odobri");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Clear");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Override");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Create task");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Posalji pacijentu");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "poslano pacijentu");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "pacijent spreman");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "postupak odobren");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "rijeseno");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "resolved");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "approved by");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "cleared by");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "overridden by");
assertIncludes("../backend/app/api/routes/appointments.py", '"/appointments/{appointment_id}/clinical-readiness-snapshots"');
assertIncludes("../backend/app/api/routes/appointments.py", '"/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}"');
assertIncludes("../backend/app/schemas/common.py", "ClinicalReadinessSnapshotDetailResponse");
assertIncludes("src/pages/AppointmentDetail.tsx", "Povijest snapshotova klinicke spremnosti");
assertIncludes("src/pages/AppointmentDetail.tsx", "Read-only prikaz spremljenih preview zapisa. Snapshot nije klinicka odluka, nije odobrenje postupka i nije odluka da se postupak smije provesti.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Povijest snapshotova trenutno nije dostupna.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nema spremljenih snapshotova za ovaj termin.");
assertIncludes("src/pages/AppointmentDetail.tsx", "snapshotHistoryItems");
assertIncludes("src/pages/AppointmentDetail.tsx", "Spremi snapshot previewa");
assertIncludes("src/pages/AppointmentDetail.tsx", "Spremi snapshot Clinical Readiness Previewa");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot zapis je spremljeni preview zapis.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nije klinicko odobrenje");
assertIncludes("src/pages/AppointmentDetail.tsx", "Razlog spremanja snapshota");
assertIncludes("src/pages/AppointmentDetail.tsx", "Razlog je obavezan.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot previewa je spremljen.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot zapis nije spremljen. Provjerite dozvole ili pokusajte ponovno.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nemate dozvolu za spremanje snapshot zapisa.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot je spremljen, ali povijest nije osvjezena.");
assertIncludes("src/pages/AppointmentDetail.tsx", "refreshSnapshotHistoryAfterCapture");
assertIncludes("src/pages/AppointmentDetail.tsx", "createSnapshotIdempotencyKey");
assertIncludes("src/pages/AppointmentDetail.tsx", "idempotency_key");
assertIncludes("src/pages/AppointmentDetail.tsx", "randomUUID");
assertIncludes("src/pages/AppointmentDetail.tsx", "Detalji snapshota");
assertIncludes("src/pages/AppointmentDetail.tsx", "Detalji Clinical Readiness Snapshota");
assertIncludes("src/pages/AppointmentDetail.tsx", "Detalji snapshota trenutno nisu dostupni.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Snapshot nema spremljene stavke.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Potencijalni blocker u spremljenom previewu - ne blokira automatski workflow.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Spremi novi snapshot i oznaci ovaj kao zamijenjen");
assertIncludes("src/pages/AppointmentDetail.tsx", "Zamijeni snapshot novim preview zapisom");
assertIncludes("src/pages/AppointmentDetail.tsx", "Ova radnja sprema novi snapshot trenutnog server-side previewa");
assertIncludes("src/pages/AppointmentDetail.tsx", "Zamjena ne mijenja stari sadrzaj");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nije zamijenjen");
assertIncludes("src/pages/AppointmentDetail.tsx", "Zamijenjen novijim preview zapisom");
assertIncludes("src/pages/AppointmentDetail.tsx", "Razlog zamjene snapshota");
assertIncludes("src/pages/AppointmentDetail.tsx", "Razlog zamjene je obavezan.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Nemate dozvolu za oznacavanje snapshot zapisa kao zamijenjenog.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Novi snapshot je spremljen, a prethodni je oznacen kao zamijenjen.");
assertIncludes("src/pages/AppointmentDetail.tsx", "Novi snapshot je spremljen, ali povijest nije osvjezena.");
assertIncludes("src/pages/AppointmentDetail.tsx", "client_preview_generated_at");
assertIncludes("src/types/index.ts", "ClinicalReadinessSnapshotCaptureRequest");
assertIncludes("src/types/index.ts", "ClinicalReadinessSnapshotResponse");
assertIncludes("src/types/index.ts", "ClinicalReadinessSnapshotDetailResponse");
assertIncludes("src/pages/AppointmentDetail.tsx", "snapshotDetail.warning");
assertIncludes("../backend/app/api/routes/appointments.py", '"/appointments/{appointment_id}/clinical-readiness-snapshots/{snapshot_id}/supersede"');
assertIncludes("../backend/app/schemas/common.py", "ClinicalReadinessSnapshotSupersedeRequest");
assertIncludes("../backend/app/schemas/common.py", "ClinicalReadinessSnapshotSupersedeResponse");
assertIncludes("../backend/app/services/clinical_readiness_snapshots.py", "CLINICAL_READINESS_SNAPSHOT_DISCLAIMER");
assertIncludes("../backend/app/services/clinical_readiness_snapshots.py", "Ne predstavlja clinical approval");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "DEMO_TEMPLATE_VERSION");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "DEMO_TEMPLATE_VERSION_WARNING");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Clinical readiness template je demo/pilot staticna definicija, nije produkcijsko pravilo.");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Ovaj prikaz je live read-only preview i ne sprema se kao trajni zapis.");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Nema specificnog clinical readiness templatea za ovu uslugu; koristi se genericki preview.");
assertIncludes("../backend/app/services/clinical_readiness_preview.py", "Koristi se demo/pilot template");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "select_clinical_readiness_template");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "keyword_fallback");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "generic_fallback");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "binding_status=\"explicit\"");
assertIncludes("../backend/app/services/clinical_readiness_template_bindings.py", "DEMO_SERVICE_CODE_BINDINGS");
assertIncludes("../backend/app/services/clinical_readiness_template_bindings.py", "EXPLICIT_BINDING_WARNING");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "GASTROSCOPY_TEMPLATE");
assertIncludes("../backend/app/services/clinical_readiness_templates.py", "COLONOSCOPY_TEMPLATE");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "AI cleared");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Mark ready");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Approved");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Cleared");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Procedure allowed");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Override readiness");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Override accepted");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Create task");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Task completed");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Capture snapshot");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Save snapshot");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Approve");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Clear");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Procedure approved");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Outcome documented");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Outcome Evidence");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Clear readiness");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "clinical approval");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "readiness clearance");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Delete snapshot");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Edit snapshot");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Supersede snapshot");
assertNotIncludes("src/api/client.ts", "deleteClinicalReadinessSnapshot");
assertNotIncludes("src/api/client.ts", "updateClinicalReadinessSnapshot");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Procedure blocked");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Ready to proceed");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Create evidence");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Bind template");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Edit template");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Oznaci da je pregledano");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "Dodaj biljesku pregleda");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "acknowledge");
assertNotIncludes("src/pages/AppointmentDetail.tsx", "patient messaging");
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
assertIncludes("src/program1/pages/SyntheticReviewWorkspace.tsx", "Program 1 - Synthetic Review");
assertIncludes("src/program1/components/SyntheticSafetyBanner.tsx", "SINTETICKI PODACI");
assertIncludes("src/program1/components/SyntheticSafetyBanner.tsx", "NIJE ZA KLINICKU UPORABU");
assertIncludes("src/program1/components/SyntheticSafetyBanner.tsx", "NE SADRZI PODATKE STVARNIH PACIJENATA");
assertIncludes("src/program1/data/syntheticScenarios.ts", "SYN-ALPHA");
assertIncludes("src/program1/data/syntheticScenarios.ts", "SYN-BETA");
assertIncludes("src/program1/data/syntheticScenarios.ts", "SYN-GAMMA");
assertIncludes("src/program1/data/syntheticScenarios.ts", "SYN-DELTA");
assertIncludes("src/program1/data/syntheticScenarios.ts", "SYN-EPSILON");
assertIncludes("src/program1/data/syntheticScenarios.ts", "syntheticOnly: true");
assertIncludes("src/program1/data/syntheticScenarios.ts", "realDataUsed: false");
assertIncludes("src/program1/utils/syntheticReviewValidation.ts", "validateSyntheticScenarios");
assertIncludes("src/program1/components/SyntheticComparison.tsx", "Usporedba je deskriptivna");
assertIncludes("src/program1/components/SyntheticComparison.tsx", "Ne predstavlja rangiranje ili preporuku");
assertIncludes("src/program1/components/SyntheticComparison.tsx", "Ne odreduje klinicki prioritet");
assertIncludes("src/styles.css", ".program1-workspace, .program1-workspace > * { min-width: 0; }");
assertIncludes("src/styles.css", ".program1-workspace .page-header { flex-direction: column; align-items: stretch; }");
assertIncludes("src/styles.css", ".program1-workspace label input, .program1-workspace label select { width: 100%; min-width: 0; }");
assertIncludes("src/components/workspace/WorkspaceTabs.tsx", 'role="tablist"');
assertIncludes("src/components/workspace/WorkspaceTabs.tsx", 'role="tab"');
assertIncludes("src/components/workspace/WorkspaceTabs.tsx", 'role="tabpanel"');
assertIncludes("src/components/workspace/WorkspaceTabs.tsx", 'aria-selected=');
assertIncludes("src/components/workspace/WorkspaceTabs.tsx", '"ArrowLeft", "ArrowRight", "Home", "End"');
assertIncludes("src/program1/components/SyntheticScenarioSelector.tsx", "aria-pressed=");
assertIncludes("src/program1/components/SyntheticEvidenceList.tsx", "Nema sinteticnih dokaza");
assertIncludes("src/program1/components/SyntheticFindingsList.tsx", "Nema sinteticnih nalaza");
assertIncludes("src/program1/components/SyntheticTimeline.tsx", "Nema sinteticnih dogadaja");
assertIncludes("src/program1/components/SyntheticComparison.tsx", "<caption>");
assertIncludes("src/styles.css", "prefers-reduced-motion: reduce");
assertIncludes("src/program1/pages/SyntheticEvaluationRunner.tsx", "Program 1 - Moderator Evaluation Runner");
assertIncludes("src/program1/pages/SyntheticEvaluationRunner.tsx", "Bez spremanja, izvoza i session evidence tvrdnje");
assertIncludes("src/program1/components/SyntheticEvaluationBoundary.tsx", "LOKALNA SINTETIČKA EVALUACIJA");
assertIncludes("src/program1/components/SyntheticEvaluationBoundary.tsx", "Ne unosite ni ne izgovarajte podatke stvarnih pacijenata");
assertIncludes("src/program1/data/syntheticEvaluation.ts", "Evaluira se sučelje, a ne znanje ili rad sudionika");
assertIncludes("src/program1/data/syntheticEvaluation.ts", "keyboard");
assertIncludes("src/program1/pages/SyntheticEvaluationRunner.tsx", "Zaustavi lokalni prolaz");
assertIncludes("package.json", "program1:evaluation-readiness");
assertIncludes("scripts/program1-evaluation-readiness.mjs", "candidate:clean-worktree");
assertIncludes("scripts/program1-evaluation-readiness.mjs", "READY FOR SEPARATELY AUTHORIZED EXTERNAL SESSION");
assertIncludes("scripts/program1-evaluation-readiness.mjs", "forbiddenPrimitives");
[
  "src/program1/pages/SyntheticReviewWorkspace.tsx",
  "src/program1/data/syntheticScenarios.ts",
  "src/program1/utils/syntheticReviewSelectors.ts",
  "src/program1/utils/syntheticReviewValidation.ts",
  "src/program1/components/SyntheticSafetyBanner.tsx",
  "src/program1/components/SyntheticScenarioSelector.tsx",
  "src/program1/components/SyntheticScenarioOverview.tsx",
  "src/program1/components/SyntheticTimeline.tsx",
  "src/program1/components/SyntheticEvidenceList.tsx",
  "src/program1/components/SyntheticFindingsList.tsx",
  "src/program1/components/SyntheticReadinessPanel.tsx",
  "src/program1/components/SyntheticLimitations.tsx",
  "src/program1/components/SyntheticComparison.tsx",
  "src/program1/pages/SyntheticEvaluationRunner.tsx",
  "src/program1/data/syntheticEvaluation.ts",
  "src/program1/types/syntheticEvaluation.ts",
  "src/program1/components/SyntheticEvaluationBoundary.tsx",
  "src/program1/components/SyntheticEvaluationPreflight.tsx",
  "src/program1/components/SyntheticEvaluationTaskList.tsx",
].forEach((file) => {
  [
    "useApi",
    "fetch(",
    "axios",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "document.cookie",
    "navigator.clipboard",
    "window.print",
    "showSaveFilePicker",
    "createObjectURL",
    "WebSocket",
    "EventSource",
    "sendBeacon",
    "download=",
    "dangerouslySetInnerHTML"
  ].forEach((value) => assertNotIncludes(file, value));
});
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
