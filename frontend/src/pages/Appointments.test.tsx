import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { Appointment } from "../types";
import { Appointments, parallelAppointmentIds } from "./Appointments";

function appointment(
  id: number,
  patientId: number,
  providerId: number,
  roomId: number,
  start: string,
  end: string,
): Appointment {
  return {
    id,
    patient_id: patientId,
    service_id: id,
    provider_id: providerId,
    room_id: roomId,
    date: "2026-07-23",
    start_time: start,
    end_time: end,
    duration_minutes: 30,
    status: "scheduled",
    source: "manual",
    patient: { id: patientId, first_name: `Pacijent ${patientId}`, last_name: "Test", date_of_birth: "1990-01-01" },
    service: { id, name: id === 1 ? "Prvi pregled" : "Kolonoskopija", duration_minutes: 30, price: "100.00", active: true },
    provider: { id: providerId, full_name: `dr. Liječnik ${providerId}`, work_start: "07:00", work_end: "20:00" },
    room: { id: roomId, name: roomId === 1 ? "Demo ordinacija 1" : "Endoskopska sala 1" },
  };
}

const parallelAppointments = [
  appointment(1, 10, 100, 1, "09:00:00", "09:30:00"),
  appointment(2, 20, 200, 2, "09:00:00", "10:00:00"),
];

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

test("marks only valid parallel appointments with different patients, clinicians and rooms", () => {
  expect([...parallelAppointmentIds(parallelAppointments)]).toEqual([1, 2]);

  const sameDoctor = [
    parallelAppointments[0],
    { ...parallelAppointments[1], provider_id: parallelAppointments[0].provider_id },
  ];
  expect(parallelAppointmentIds(sameDoctor).size).toBe(0);
});

test("appointment rows make service, clinician, room and parallel context visible", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(parallelAppointments), { status: 200, headers: { "Content-Type": "application/json" } }),
  );

  render(<MemoryRouter><Appointments/></MemoryRouter>);

  const table = await screen.findByRole("table", { name: "Naručeni termini" });
  expect(within(table).getByText("Prvi pregled")).toBeTruthy();
  expect(within(table).getByText("Kolonoskopija")).toBeTruthy();
  expect(within(table).getByText("dr. Liječnik 100")).toBeTruthy();
  expect(within(table).getByText("dr. Liječnik 200")).toBeTruthy();
  expect(within(table).getByText("Demo ordinacija 1")).toBeTruthy();
  expect(within(table).getByText("Endoskopska sala 1")).toBeTruthy();
  expect(within(table).getAllByLabelText("Paralelni termin s drugim pacijentom, liječnikom i prostorijom")).toHaveLength(2);
});
