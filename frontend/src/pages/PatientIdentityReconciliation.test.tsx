import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { PatientIdentityReconciliationReviewPage } from "./PatientIdentityReconciliationReview";
import { PatientIdentityReconciliationStatus } from "./PatientIdentityReconciliationStatus";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof import("../api/client")>("../api/client");
  return { ...actual, api: vi.fn() };
});

const mockedApi = vi.mocked(api);

describe("Patient identity reconciliation UI", () => {
  beforeEach(() => mockedApi.mockReset());

  it("shows only opaque requester status and preserves it across refresh", async () => {
    mockedApi.mockResolvedValue({ request_id: "opaque-request", status: "pending_review", submitted_identity: {}, created_at: "2026-08-02T00:00:00Z", updated_at: "2026-08-02T00:00:00Z" });
    render(<MemoryRouter initialEntries={["/patient-identity-reconciliations/opaque-request"]}><Routes><Route path="/patient-identity-reconciliations/:id" element={<PatientIdentityReconciliationStatus />} /></Routes></MemoryRouter>);
    expect(await screen.findByText("Čeka kontrolirani pregled identiteta")).toBeTruthy();
    expect(screen.queryByText(/candidate|match reason|foreign/i)).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Osvježi status" }));
    await waitFor(() => expect(mockedApi).toHaveBeenCalledTimes(2));
  });

  it("requires a reason, prevents double action, and exposes no global search", async () => {
    mockedApi.mockResolvedValueOnce([{ request_id: "request-1", status: "pending_review", requesting_clinic_id: 7, requesting_institution_id: 2, submitted_identity: { first_name: "Ana", last_name: "Horvat", date_of_birth: "1987-04-03" }, candidates: [{ patient_id: 12, first_name: "Ana", last_name: "Horvat", date_of_birth: "1987-04-03", oib_masked: "********901" }], match_reasons: { "12": ["name_date_of_birth"] }, created_at: "2026-08-02T00:00:00Z", updated_at: "2026-08-02T00:00:00Z" }]);
    render(<MemoryRouter><PatientIdentityReconciliationReviewPage /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: /request-1/ }));
    expect(screen.queryByRole("searchbox")).toBeNull();
    const approve = screen.getByRole("button", { name: "Odobri povezivanje" });
    expect((approve as HTMLButtonElement).disabled).toBe(true);
    await userEvent.type(screen.getByRole("textbox"), "Verified synthetic evidence");
    mockedApi.mockResolvedValueOnce({ request_id: "request-1", status: "approved_link" }).mockResolvedValueOnce([]);
    await userEvent.dblClick(approve);
    await waitFor(() => expect(mockedApi.mock.calls.filter(call => String(call[0]).endsWith("approve-link"))).toHaveLength(1));
  });
});
