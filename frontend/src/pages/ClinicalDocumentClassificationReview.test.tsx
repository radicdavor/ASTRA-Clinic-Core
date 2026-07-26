import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClinicalDocumentClassificationReview } from "./ClinicalDocumentClassificationReview";

function json(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  }));
}

describe("ClinicalDocumentClassificationReview", () => {
  beforeEach(() => {
    Object.defineProperty(document, "cookie", { writable: true, value: "astra_csrf=test-csrf" });
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/document-classification-queue/7")) {
        return json({
          id: 7,
          patient_id: 3,
          clinic_id: 2,
          institution_id: 1,
          title: "Nalaz za klasifikaciju",
          document_type: "laboratory",
          source_type: "uploaded",
          document_date: "2026-07-25",
          received_at: "2026-07-25T08:00:00Z",
          created_at: "2026-07-25T08:00:00Z",
          review_status: "draft",
          record_classification: "unclassified",
          patient: { id: 3, first_name: "Sintetički", last_name: "Pacijent", date_of_birth: "1990-01-01" }
        });
      }
      if (url.includes("/api/clinical-documents/7/classification/review") && init?.method === "POST") {
        return json({
          id: 7,
          patient_id: 3,
          source_type: "uploaded",
          document_type: "laboratory",
          title: "Nalaz za klasifikaciju",
          ai_extraction_status: "not_run",
          physician_reviewed: false,
          review_status: "draft",
          record_classification: "clinical",
          created_at: "2026-07-25T08:00:00Z",
          updated_at: "2026-07-25T08:00:00Z"
        });
      }
      return json({}, 404);
    }));
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test("shows untrusted status and submits an explicit human classification", async () => {
    render(
      <MemoryRouter initialEntries={["/clinical-documents/7/classification"]}>
        <Routes>
          <Route path="/clinical-documents/:id/classification" element={<ClinicalDocumentClassificationReview />} />
          <Route path="/clinical-documents/:id" element={<p>Klinički dokument otvoren</p>} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByRole("heading", { name: "Klasificiraj dokument" })).toBeTruthy();
    expect(screen.getByText("Čeka klasifikaciju")).toBeTruthy();
    expect(screen.getByText("Sintetički Pacijent")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Potvrđena klasifikacija"), { target: { value: "clinical" } });
    fireEvent.change(screen.getByLabelText("Napomena pregledavatelja"), {
      target: { value: "Pregledan izvor i potvrđena klinička vrsta." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Potvrdi klasifikaciju" }));

    await screen.findByText("Klinički dokument otvoren");
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/clinical-documents/7/classification/review"),
        expect.objectContaining({ method: "POST" })
      );
    });
    const reviewCall = vi.mocked(fetch).mock.calls.find(([url]) =>
      String(url).includes("/classification/review")
    );
    expect(reviewCall?.[1]?.body).toContain('"record_classification":"clinical"');
  });
});
