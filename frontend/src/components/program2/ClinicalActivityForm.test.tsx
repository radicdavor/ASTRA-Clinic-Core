import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { setToken } from "../../api/client";
import type { ClinicalFormInstance, JourneyActivity } from "../../types/program2";
import { ClinicalActivityForm } from "./ClinicalActivityForm";

const activity: JourneyActivity = {
  id: 41, journey_id: 12, appointment_id: 9, service_id: 3, activity_key: "gastroscopy",
  activity_kind: "gastroscopy", specialty_key: "gastroenterology", clinic_id: 1,
  primary_provider_id: 2, room_id: 4, sequence: 2, depends_on_activity_id: null, required: true,
  planned_start: "2026-07-19T09:00:00Z", planned_end: "2026-07-19T09:30:00Z",
  actual_start: null, actual_end: null, status: "in_progress", not_performed_reason: null,
  form_resolution_status: "resolved", billing_status: "pending", consumables_status: "pending",
};

const draftForm: ClinicalFormInstance = {
  id: 17, activity_id: 41, form_version_id: 5, purpose: "clinical_report", status: "draft",
  data_json: {}, rendered_summary: null, completed_by: null, signed_by: null, completed_at: null,
  signed_at: null, amended_from_instance_id: null, binding_source: "default_service",
  resolved_at: "2026-07-19T08:00:00Z", revision_number: 0,
  updated_at: "2026-07-19T08:00:00Z",
  form_version: {
    id: 5, definition_id: 2, version: 1, status: "published", output_document_type: "clinical_report",
    sections_json: [{ section_key: "outcome", title: "Završetak", fields: [{ field_key: "complications", label: "Komplikacije", type: "long_text", required: true }] }],
  },
};

function jsonResponse(value: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(value), { status, headers: { "Content-Type": "application/json" } }));
}

function renderForm(onChanged = vi.fn().mockResolvedValue(undefined)) {
  return render(<MemoryRouter><ClinicalActivityForm journeyId={12} activity={activity} serviceName="Gastroskopija" onChanged={onChanged}/></MemoryRouter>);
}

beforeEach(() => { localStorage.clear(); setToken("synthetic-token"); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); localStorage.clear(); });

describe("atomsko dovršavanje kliničkog obrasca", () => {
  test("šalje trenutačni lokalni unos bez prethodnog spremanja skice", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn().mockResolvedValue(undefined);
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/form") && !init?.method) return jsonResponse(draftForm);
      if (url.endsWith("/form/complete")) return jsonResponse({ ...draftForm, status: "completed", data_json: { complications: "Bez komplikacija." }, revision_number: 1, completed_at: "2026-07-19T08:05:00Z" });
      throw new Error(`Neočekivan zahtjev: ${url} ${init?.method}`);
    });

    renderForm(onChanged);
    const complications = await screen.findByLabelText("Komplikacije *");
    await user.type(complications, "Bez komplikacija.");
    expect(screen.getByText("Nespremljene promjene")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "Dovrši obrazac" }));
    await user.click(screen.getByRole("button", { name: "Potvrdi" }));
    expect(await screen.findByText("Obrazac dovršen")).toBeTruthy();

    const completeCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/form/complete"));
    expect(completeCall).toBeTruthy();
    expect(JSON.parse(String(completeCall?.[1]?.body))).toMatchObject({
      data: { complications: "Bez komplikacija." },
      expected_instance_id: 17,
      expected_revision_number: 0,
      idempotency_key: expect.any(String),
    });
    expect(onChanged).toHaveBeenCalled();
  });

  test("zadržava unesene podatke i označava polje nakon validacijske pogreške", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/form") && !init?.method) return jsonResponse(draftForm);
      if (url.endsWith("/form/complete")) return jsonResponse({ detail: { code: "required_fields", message: "Dopunite obvezna polja.", fields: [{ field_key: "complications", label: "Komplikacije", message: "Polje je obvezno." }] } }, 422);
      throw new Error(`Neočekivan zahtjev: ${url}`);
    });

    renderForm();
    const complications = await screen.findByLabelText("Komplikacije *") as HTMLTextAreaElement;
    await user.type(complications, "Bez komplikacija.");
    await user.click(screen.getByRole("button", { name: "Dovrši obrazac" }));
    await user.click(screen.getByRole("button", { name: "Potvrdi" }));

    await waitFor(() => expect(complications.value).toBe("Bez komplikacija."));
    expect(complications.getAttribute("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(complications);
    expect(screen.getByText("Nespremljene promjene")).toBeTruthy();
    expect(screen.getAllByText("Polje je obvezno.").length).toBeGreaterThan(0);
  });

  test("sprema skicu i uklanja oznaku nespremljenih promjena", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/form") && !init?.method) return jsonResponse(draftForm);
      if (url.endsWith("/form") && init?.method === "PATCH") return jsonResponse({ ...draftForm, status: "in_progress", data_json: { complications: "Bez komplikacija." }, revision_number: 1, updated_at: "2026-07-19T08:01:00Z" });
      throw new Error(`Neočekivan zahtjev: ${url}`);
    });

    renderForm();
    await user.type(await screen.findByLabelText("Komplikacije *"), "Bez komplikacija.");
    await user.click(screen.getByRole("button", { name: "Spremi skicu" }));

    expect(await screen.findByText("Skica spremljena")).toBeTruthy();
    expect(screen.queryByText("Nespremljene promjene")).toBeNull();
  });

  test("zadržava lokalni unos kada drugi korisnik spremi noviju reviziju", async () => {
    const user = userEvent.setup();
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (url.endsWith("/form") && !init?.method) return jsonResponse(draftForm);
      if (url.endsWith("/form") && init?.method === "PATCH") return jsonResponse({ detail: {
        code: "stale_form", message: "Drugi korisnik je izmijenio ovaj nalaz.", actual_revision_number: 1,
        current_updated_at: "2026-07-19T08:02:00Z", server_data: { complications: "Server verzija" },
      } }, 409);
      throw new Error(`Neočekivan zahtjev: ${url}`);
    });

    renderForm();
    const complications = await screen.findByLabelText("Komplikacije *") as HTMLTextAreaElement;
    await user.type(complications, "Moja lokalna verzija");
    await user.click(screen.getByRole("button", { name: "Spremi skicu" }));

    expect(await screen.findByText("Drugi korisnik je izmijenio ovaj nalaz")).toBeTruthy();
    expect(complications.value).toBe("Moja lokalna verzija");
    await user.click(screen.getByRole("button", { name: "Učitaj verziju sa servera" }));
    expect(complications.value).toBe("Server verzija");
    expect(screen.queryByText("Nespremljene promjene")).toBeNull();
  });
});
