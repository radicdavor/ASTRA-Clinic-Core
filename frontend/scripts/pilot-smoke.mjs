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

[
  "src/pages/Dashboard.tsx",
  "src/pages/AppointmentDetail.tsx",
  "src/pages/PurchaseOrders.tsx",
  "src/pages/Invoices.tsx",
  "src/pages/ApiKeys.tsx",
  "src/pages/Readiness.tsx",
  "src/components/AppShell.tsx",
  "src/components/AuditTimeline.tsx",
  "src/components/HelpHint.tsx",
  "src/components/ActionButton.tsx",
  "src/components/workspace/WorkspaceLayout.tsx",
  "src/components/workspace/WorkspaceHeader.tsx",
  "src/components/workspace/WorkspaceSection.tsx",
  "src/components/workspace/WorkspaceTabs.tsx",
  "src/utils/patientIdentity.ts",
].forEach(read);

assertIncludes("src/routes/AppRoutes.tsx", "/appointments/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/patients/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/api-keys");
assertIncludes("src/routes/AppRoutes.tsx", "/readiness");
assertIncludes("src/components/AppShell.tsx", "/api/public-config");
assertIncludes("src/components/AppShell.tsx", "Demo/development okruzenje");
assertIncludes("src/components/AppShell.tsx", "Spremnost");
assertIncludes("src/pages/AppointmentDetail.tsx", "Obavezni varijabilni materijal mora imati kolicinu.");
assertIncludes("src/pages/PurchaseOrders.tsx", "Kolicina zaprimanja ne smije biti veca od preostale kolicine.");
assertIncludes("src/pages/Invoices.tsx", "remaining");
assertIncludes("src/pages/ApiKeys.tsx", "opasni scopeovi");
assertIncludes("src/pages/Invoices.tsx", "Demo fiskalizacija - nije stvarna fiskalizacija.");
assertIncludes("src/components/AuditTimeline.tsx", "before_json");
assertIncludes("src/components/AuditTimeline.tsx", "actionLabels");
assertIncludes("src/components/AuditTimeline.tsx", "entityRoute");
assertIncludes("src/pages/PatientForm.tsx", "OIB");
assertIncludes("src/pages/PatientForm.tsx", "Spremi pacijenta");
assertIncludes("src/pages/PatientForm.tsx", "possible-duplicates");
assertIncludes("src/pages/PatientForm.tsx", "Moguci duplikati pacijenta");
assertIncludes("src/pages/AppointmentForm.tsx", "Ime, prezime ili OIB");
assertIncludes("src/pages/AppointmentForm.tsx", "selectedPatient");
assertIncludes("src/pages/AppointmentForm.tsx", "service-context");
assertIncludes("src/pages/AppointmentForm.tsx", "formatPatientIdentity");
assertIncludes("src/pages/PatientDetail.tsx", "WorkspaceHeader");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/appointments");
assertIncludes("src/pages/PatientDetail.tsx", "/api/patients/${id}/invoices");
assertIncludes("src/pages/PatientDetail.tsx", "Moguci duplikati pacijenta");
assertIncludes("src/pages/PatientDetail.tsx", "summary-strip");
assertIncludes("src/pages/PatientDetail.tsx", "Zadnji termin");
assertIncludes("src/pages/PatientDetail.tsx", "Otvoreni racuni");
assertIncludes("src/pages/Patients.tsx", "/patients/${row.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "/patients/${appointment.data.patient.id}");
assertIncludes("src/pages/AppointmentDetail.tsx", "Zavrsi uz potrosnju");
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

console.log("Frontend pilot smoke passed.");
