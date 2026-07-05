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
  "src/components/AppShell.tsx",
  "src/components/AuditTimeline.tsx",
].forEach(read);

assertIncludes("src/routes/AppRoutes.tsx", "/appointments/:id");
assertIncludes("src/routes/AppRoutes.tsx", "/api-keys");
assertIncludes("src/components/AppShell.tsx", "Demo/development okruzenje");
assertIncludes("src/pages/Invoices.tsx", "Demo fiskalizacija - nije stvarna fiskalizacija.");
assertIncludes("src/components/AuditTimeline.tsx", "before_json");

console.log("Frontend pilot smoke passed.");
