import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClinicalDocumentDetail } from "./ClinicalDocumentDetail";

function json(body: unknown) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }));
}

describe("ClinicalDocumentDetail addenda", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/clinical-documents/7/addenda")) {
        return json([{
          id: 41,
          original_document_id: 7,
          signed_report_id: 19,
          original_document_type: "signed_clinical_report",
          patient_id: 3,
          institution_id: 1,
          clinic_id: 2,
          author_user_id: 9,
          reason: "Naknadno pojašnjenje",
          content: "Odvojena potpisana dopuna.",
          status: "signed",
          signed_at: "2026-07-21T10:15:00Z",
          signed_by_user_id: 9,
          created_at: "2026-07-21T10:15:00Z",
          updated_at: "2026-07-21T10:15:00Z",
        }]);
      }
      if (url.includes("/api/clinical-documents/7/evidence-timeline") || url.includes("/api/audit-log")) return json([]);
      if (url.includes("/api/clinical-documents/7")) {
        return json({
          id: 7,
          patient_id: 3,
          source_type: "internal",
          document_type: "gastroscopy",
          title: "Potpisani nalaz",
          document_date: "2026-07-21",
          raw_text: "Originalni sadržaj",
          ai_extraction_status: "not_run",
          physician_reviewed: true,
          review_status: "signed",
          is_clinical_record: true,
          record_classification: "clinical",
          can_edit: false,
          can_review: false,
          can_add_addendum: false,
          created_at: "2026-07-21T10:00:00Z",
          updated_at: "2026-07-21T10:00:00Z",
        });
      }
      return json([]);
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("shows a signed addendum separately from the original document", async () => {
    render(
      <MemoryRouter initialEntries={["/clinical-documents/7"]}>
        <Routes><Route path="/clinical-documents/:id" element={<ClinicalDocumentDetail />} /></Routes>
      </MemoryRouter>,
    );

    await screen.findByRole("heading", { name: "Potpisani nalaz" });
    const addenda = await screen.findByLabelText("Postojeće dopune dokumenta");

    expect(within(addenda).getByText("Naknadno pojašnjenje")).toBeTruthy();
    expect(within(addenda).getByText("Odvojena potpisana dopuna.")).toBeTruthy();
    expect(await screen.findByDisplayValue("Originalni sadržaj")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Spremi dopunu" })).toBeNull();
  });
});
