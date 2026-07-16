import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = path => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("Daily dashboard opens the canonical journey workspace", async () => {
  const [routes, dashboard] = await Promise.all([read("src/routes/AppRoutes.tsx"), read("src/pages/DailyClinicDashboard.tsx")]);
  assert.match(routes, /journeys\/:id/);
  assert.match(dashboard, /journeys\/\$\{row\.journey_id\}/);
});

test("Journey workspace exposes all operational panels", async () => {
  const source = await read("src/pages/PatientJourneyWorkspace.tsx");
  for (const panel of ["PatientTimeline", "SourceDocumentViewer", "AISummaryPanel", "EncounterPanel", "CheckInChecklist", "ConsumablesPanel", "BillingPanel", "PaymentPanel", "BlockerPanel"]) assert.match(source, new RegExp(panel));
});

test("Financial actions remain explicit user actions", async () => {
  const source = await read("src/pages/PatientJourneyWorkspace.tsx");
  for (const endpoint of ["consumables/confirm", "billing/prepare", "/payments", "/close"]) assert.ok(source.includes(endpoint));
  assert.ok(source.includes('reasonLabel: "Razlog odgode"'), "payment deferral requires a human-entered reason");
  assert.ok(!source.includes("window.prompt"), "clinical workflow must not use browser-native prompts");
  assert.ok(!source.includes("window.confirm"), "clinical workflow must not use browser-native confirmations");
});

test("Package booking previews and books one coordinated arrival without browser-native confirmation", async () => {
  const [routes, source] = await Promise.all([read("src/routes/AppRoutes.tsx"), read("src/pages/PackageBooking.tsx")]);
  assert.match(routes, /appointments\/package/);
  assert.ok(source.includes("/schedule-preview"));
  assert.ok(source.includes("/book"));
  assert.ok(source.includes("idempotency_key"));
  assert.ok(source.includes("Potvrdi koordinirani dolazak"));
  assert.ok(!source.includes("window.confirm"));
  assert.ok(!source.includes("window.prompt"));
});
