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
  assert.ok(source.includes("window.prompt"), "payment deferral requires a human-entered reason");
});
