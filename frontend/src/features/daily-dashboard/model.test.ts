import { describe, expect, test } from "vitest";
import {
  buildTimelineBlocks,
  canonicalJourneyRows,
  fallbackActivities,
  formatMinutes,
  groupRowsByRoom,
  operationalState,
  rowActivityWindow,
  timelineSlots,
  visibleRange,
  type DashboardRow,
} from "./model";

function row(overrides: Partial<DashboardRow> = {}): DashboardRow {
  return {
    journey_id: 1,
    appointment_id: 101,
    time: "08:00:00",
    patient_name: "Test Pacijent",
    service_id: 1,
    service_name: "Prvi pregled",
    clinician_id: 1,
    clinician_name: "dr. Test",
    room_id: 1,
    room_name: "Ordinacija 1",
    clinic_id: 1,
    clinic_name: "Klinika",
    intake_channel: "manual",
    workflow_stage: "ready_for_arrival",
    document_status: "complete",
    preparation_status: "complete",
    arrival_status: "not_arrived",
    check_in_status: "not_arrived",
    encounter_status: "not_started",
    consumables_status: "not_ready",
    billing_status: "not_ready",
    payment_status: "not_due",
    blocker_status: "clear",
    blocker_labels: [],
    blockers: [],
    allowed_actions: ["open_check_in"],
    reception_warning: false,
    reception_warning_details: [],
    activity_count: 1,
    current_activity_id: null,
    next_activity_id: null,
    activities: [{ id: 11, sequence: 1, time: "08:00:00", end_time: "08:30:00", service_name: "Prvi pregled", clinician_name: "dr. Test", room_name: "Ordinacija 1", status: "ready" }],
    ...overrides,
  };
}

describe("daily dashboard model", () => {
  test("uses earliest activity start and latest activity end for one physical arrival", () => {
    const window = rowActivityWindow(row({
      time: "09:15:00",
      activities: [
        { id: 2, sequence: 2, time: "09:30:00", end_time: "10:30:00", service_name: "Gastroskopija", clinician_name: "dr. Test", room_name: "Endoskopija", status: "ready" },
        { id: 1, sequence: 1, time: "09:00:00", end_time: "09:20:00", service_name: "Pregled", clinician_name: "dr. Test", room_name: "Ordinacija", status: "completed" },
      ],
    }));
    expect(window).toEqual({ start: 9 * 60, end: 10 * 60 + 30 });
  });

  test("falls back to a minimum block when end_time is missing", () => {
    const source = row({ activities: [{ id: 11, sequence: 1, time: "14:00:00", service_name: "Kontrola", clinician_name: null, room_name: null, status: "ready" }] });
    expect(rowActivityWindow(source)).toEqual({ start: 14 * 60, end: 14 * 60 + 30 });
    expect(fallbackActivities(source, 14 * 60 + 30)).toHaveLength(1);
  });

  test("falls back to clinic day start when time data is malformed", () => {
    expect(rowActivityWindow(row({ time: "nije-vrijeme", activities: [] }))).toEqual({ start: 7 * 60, end: 7 * 60 + 30 });
  });

  test("deduplicates duplicate backend rows into one physical patient arrival", () => {
    const rows = canonicalJourneyRows([
      row({ journey_id: 44, activities: [{ id: 1, sequence: 1, time: "09:00:00", end_time: "09:30:00", service_name: "Pregled", clinician_name: null, room_name: "A", status: "ready" }] }),
      row({ journey_id: 44, activities: [{ id: 2, sequence: 2, time: "09:30:00", end_time: "10:00:00", service_name: "Gastroskopija", clinician_name: null, room_name: "B", status: "ready" }] }),
    ]);
    expect(rows).toHaveLength(1);
    expect(rows[0].activities.map(activity => activity.service_name)).toEqual(["Pregled", "Gastroskopija"]);
    expect(buildTimelineBlocks(rows)).toHaveLength(1);
  });

  test("extends visible range for appointments outside the 07:00-20:00 clinic day", () => {
    const blocks = buildTimelineBlocks([
      row({ journey_id: 1, time: "06:30:00", activities: [{ id: 1, sequence: 1, time: "06:30:00", end_time: "07:00:00", service_name: "Rano", clinician_name: null, room_name: "A", status: "ready" }] }),
      row({ journey_id: 2, time: "20:00:00", activities: [{ id: 2, sequence: 1, time: "20:00:00", end_time: "20:30:00", service_name: "Kasno", clinician_name: null, room_name: "B", status: "ready" }] }),
    ]);
    const range = visibleRange(blocks);
    expect(formatMinutes(range.start)).toBe("06:30");
    expect(formatMinutes(range.end)).toBe("20:30");
    expect(timelineSlots(range.start, range.end)).toContain(20 * 60 + 30);
  });

  test("assigns overlapping patients to separate lanes", () => {
    const blocks = buildTimelineBlocks([
      row({ journey_id: 1, time: "08:00:00", activities: [{ id: 1, sequence: 1, time: "08:00:00", end_time: "08:45:00", service_name: "A", clinician_name: null, room_name: "Soba", status: "ready" }] }),
      row({ journey_id: 2, time: "08:15:00", activities: [{ id: 2, sequence: 1, time: "08:15:00", end_time: "08:30:00", service_name: "B", clinician_name: null, room_name: "Soba", status: "ready" }] }),
      row({ journey_id: 3, time: "08:45:00", activities: [{ id: 3, sequence: 1, time: "08:45:00", end_time: "09:00:00", service_name: "C", clinician_name: null, room_name: "Soba", status: "ready" }] }),
    ]);
    expect(blocks.map(block => block.lane)).toEqual([0, 1, 0]);
    expect(blocks.every(block => block.laneCount === 2)).toBe(true);
  });

  test("prefers backend canonical operational status over frontend compatibility fallback", () => {
    const state = operationalState(row({
      workflow_stage: "ready_for_clinician",
      blocker_status: "blocked",
      blockers: [{ id: 1, title: "Stari blocker", details: "Fallback ne smije pobijediti.", is_clinical: true }],
      operational_status: "awaiting_payment",
      operational_status_label: "Čeka plaćanje",
      operational_status_severity: "warning",
      operational_status_reasons: [{ code: "invoice_unpaid", label: "Račun nije plaćen." }],
    }));
    expect(state.tone).toBe("orange");
    expect(state.label).toBe("Čeka plaćanje");
    expect(state.detail).toBe("Račun nije plaćen.");
  });

  test("keeps completed but unpaid patients orange, not green", () => {
    const state = operationalState(row({ workflow_stage: "completed", payment_status: "unpaid", allowed_actions: ["open_payment"] }));
    expect(state.tone).toBe("orange");
    expect(state.label).toBe("Čeka plaćanje");
  });

  test("groups room view by the activity room when it differs from journey room", () => {
    const groups = groupRowsByRoom([
      row({
        journey_id: 1,
        room_name: "Ordinacija",
        activities: [
          { id: 1, sequence: 1, time: "09:00:00", end_time: "09:30:00", service_name: "Pregled", clinician_name: null, room_name: "Ordinacija", status: "ready" },
          { id: 2, sequence: 2, time: "09:30:00", end_time: "10:00:00", service_name: "Gastroskopija", clinician_name: null, room_name: "Endoskopija", status: "ready" },
        ],
      }),
    ], "Endoskopija");
    expect(groups).toHaveLength(1);
    expect(groups[0].roomName).toBe("Endoskopija");
  });
});
