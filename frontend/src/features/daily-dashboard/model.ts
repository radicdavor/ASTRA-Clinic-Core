import type {
  DailyDashboardActivity as OpenApiDailyDashboardActivity,
  DailyDashboardBlocker as OpenApiDailyDashboardBlocker,
  DailyDashboardClinic as OpenApiDailyDashboardClinic,
  DailyDashboardResponse as OpenApiDailyDashboardResponse,
  DailyDashboardRow as OpenApiDailyDashboardRow,
} from "../../api/generated-openapi";

export type DashboardBlocker = OpenApiDailyDashboardBlocker & { details: string | null; is_clinical: boolean };

export type DashboardActivity = Omit<OpenApiDailyDashboardActivity, "end_time"> & { end_time?: string };

export type DashboardRow = Omit<
  OpenApiDailyDashboardRow,
  "activities" | "allowed_actions" | "blocker_labels" | "blockers" | "reception_warning" | "reception_warning_details"
> & {
  activities: DashboardActivity[];
  allowed_actions: string[];
  blocker_labels: string[];
  blockers: DashboardBlocker[];
  reception_warning: boolean;
  reception_warning_details: string[];
};

export type DashboardClinic = OpenApiDailyDashboardClinic;

export type DashboardResponse = Omit<
  OpenApiDailyDashboardResponse,
  "available_clinics" | "can_filter_clinician" | "rows"
> & {
  available_clinics: DashboardClinic[];
  can_filter_clinician: boolean;
  rows: DashboardRow[];
};

export type StatusTone = "gray" | "blue" | "red" | "orange" | "green";

export type OperationalAction = "reception" | "encounter" | "consumables" | "billing" | "open";

export type OperationalState = {
  tone: StatusTone;
  label: string;
  detail: string;
  action?: OperationalAction;
  actionLabel?: string;
};

export type TimelineBlock = {
  row: DashboardRow;
  state: OperationalState;
  startMinutes: number;
  endMinutes: number;
  lane: number;
  laneCount: number;
  parallel: boolean;
  roomName: string;
};

export const dayStart = 7 * 60;
export const dayEnd = 20 * 60;
export const slotMinutes = 30;
export const minimumBlockMinutes = 30;

const documentContext: Record<string, string> = {
  requested: "Ranije nalaze pacijent može donijeti na pregled; to ne blokira početak pregleda.",
  partial: "Dio nalaza je zaprimljen; ostalo se može pregledati tijekom pregleda.",
  review_required: "Nalazi čekaju liječnički pregled, ali nisu administrativni uvjet za dolazak.",
};

const severityTone: Record<string, StatusTone> = {
  neutral: "gray",
  info: "blue",
  active: "blue",
  warning: "orange",
  critical: "red",
  success: "green",
};

export function minutesFromTime(value?: string | null) {
  if (!value) return Number.NaN;
  const [hours, minutes] = value.split(":").map(Number);
  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) return Number.NaN;
  return hours * 60 + minutes;
}

export function formatMinutes(minutes: number) {
  const bounded = Math.max(0, minutes);
  const hours = Math.floor(bounded / 60);
  const mins = bounded % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

export function rowActivityWindow(row: DashboardRow) {
  const starts = orderedActivities(row).map(activity => minutesFromTime(activity.time)).filter(Number.isFinite);
  const ends = orderedActivities(row).map(activity => minutesFromTime(activity.end_time)).filter(Number.isFinite);
  const fallbackStart = minutesFromTime(row.time);
  const start = Math.min(...(starts.length ? starts : [Number.isFinite(fallbackStart) ? fallbackStart : dayStart]));
  const explicitEnd = ends.length ? Math.max(...ends) : Number.NaN;
  const end = Number.isFinite(explicitEnd) && explicitEnd > start ? explicitEnd : start + minimumBlockMinutes;
  return { start, end: Math.max(end, start + minimumBlockMinutes) };
}

export function activityDurationLabel(activity: DashboardActivity) {
  const start = minutesFromTime(activity.time);
  const end = minutesFromTime(activity.end_time);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return activity.time.slice(0, 5);
  return `${formatMinutes(start)}–${formatMinutes(end)}`;
}

export function orderedActivities(row: DashboardRow) {
  return [...(row.activities ?? [])].sort((a, b) => {
    const sequence = a.sequence - b.sequence;
    if (sequence !== 0) return sequence;
    return minutesFromTime(a.time) - minutesFromTime(b.time);
  });
}

export function fallbackActivities(row: DashboardRow, endMinutes: number): DashboardActivity[] {
  const activities = orderedActivities(row);
  if (activities.length) return activities;
  return [{
    id: row.appointment_id,
    sequence: 1,
    time: row.time,
    end_time: formatMinutes(endMinutes),
    service_name: row.service_name,
    clinician_name: row.clinician_name,
    room_name: row.room_name,
    status: row.workflow_stage,
  }];
}

export function operationalState(row: DashboardRow): OperationalState {
  if (row.operational_status_label && row.operational_status_severity) {
    const tone = severityTone[row.operational_status_severity] ?? "gray";
    const detail = row.operational_status_reasons?.map(item => item.label).join("; ") || row.operational_status || "Operativni status dolaska.";
    const canOpenEncounter = row.allowed_actions.includes("open_encounter") && ["ready_for_clinician", "in_encounter"].includes(row.workflow_stage);
    if (tone === "green") return { tone, label: row.operational_status_label, detail };
    if (tone === "orange") {
      if (row.operational_status === "awaiting_consumables" && row.allowed_actions.includes("record_consumables")) {
        return { tone, label: row.operational_status_label, detail, action: "consumables", actionLabel: "Evidentiraj materijal" };
      }
      return { tone, label: row.operational_status_label, detail, action: "billing", actionLabel: "Naplati" };
    }
    if (canOpenEncounter) {
      return {
        tone,
        label: row.operational_status_label,
        detail,
        action: "encounter",
        actionLabel: row.workflow_stage === "in_encounter" ? "Nastavi pregled" : "Otvori pregled",
      };
    }
    if (row.allowed_actions.includes("open_check_in")) {
      return { tone, label: row.operational_status_label, detail, action: "reception", actionLabel: "Otvori prijem" };
    }
    return {
      tone,
      label: row.operational_status_label,
      detail,
      action: tone === "gray" ? "open" : undefined,
      actionLabel: tone === "gray" ? "Otvori" : undefined,
    };
  }

  // Compatibility fallback for older API/mock payloads. Backend operational_status is the source of truth.
  const blocker = row.blockers[0];
  const redFlagCount = row.blockers.length + row.reception_warning_details.length;
  if (redFlagCount > 0) {
    const detail = [
      ...row.blockers.map(item => item.details || item.title),
      ...row.reception_warning_details,
    ].filter(Boolean).join("; ");
    const canOpenEncounter = row.allowed_actions.includes("open_encounter") && ["ready_for_clinician", "in_encounter"].includes(row.workflow_stage);
    return {
      tone: "red",
      label: row.workflow_stage === "ready_for_clinician" || row.workflow_stage === "in_encounter" ? "Čeka pregled/pretragu" : blocker?.title || "Crvena napomena",
      detail: detail || "Postoji odstupanje koje treba ljudsku provjeru.",
      action: canOpenEncounter ? "encounter" : row.allowed_actions.includes("open_check_in") ? "reception" : "open",
      actionLabel: canOpenEncounter ? "Otvori pregled" : row.allowed_actions.includes("open_check_in") ? "Otvori prijem" : "Otvori",
    };
  }
  if (row.workflow_stage === "completed" && ["paid", "not_due", "cancelled"].includes(row.payment_status)) {
    return { tone: "green", label: "Završeno", detail: "Sve aktivnosti su završene i plaćanje je riješeno." };
  }
  if (row.workflow_stage === "completed") {
    return { tone: "orange", label: "Čeka plaćanje", detail: "Klinički dio je završen; plaćanje još nije potpuno riješeno.", action: "billing", actionLabel: "Naplati" };
  }
  if (row.workflow_stage === "no_show") return { tone: "red", label: "Nije došao/la", detail: "Pacijent nije došao na termin." };
  if (row.workflow_stage === "procedure_completed") {
    return {
      tone: "orange",
      label: "Čeka materijal",
      detail: "Treba potvrditi korišteni materijal.",
      action: row.allowed_actions.includes("record_consumables") ? "consumables" : "open",
      actionLabel: row.allowed_actions.includes("record_consumables") ? "Evidentiraj materijal" : "Otvori",
    };
  }
  if (["awaiting_billing", "awaiting_payment"].includes(row.workflow_stage)) {
    return {
      tone: "orange",
      label: row.workflow_stage === "awaiting_billing" ? "Čeka račun" : "Čeka plaćanje",
      detail: row.workflow_stage === "awaiting_billing" ? "Račun treba izraditi." : "Račun je izrađen i čeka plaćanje.",
      action: "billing",
      actionLabel: "Naplati",
    };
  }
  if (["ready_for_clinician", "in_encounter"].includes(row.workflow_stage)) {
    return {
      tone: "blue",
      label: row.workflow_stage === "in_encounter" ? "Pregled u tijeku" : "Čeka pregled/pretragu",
      detail: row.workflow_stage === "in_encounter" ? "Klinički susret je otvoren." : "Prijem je završen; pacijent čeka liječnika ili pretragu.",
      action: row.allowed_actions.includes("open_encounter") ? "encounter" : "open",
      actionLabel: row.workflow_stage === "in_encounter" ? "Nastavi pregled" : "Otvori pregled",
    };
  }
  if (["arrived", "check_in_review"].includes(row.workflow_stage)) {
    return {
      tone: "blue",
      label: "Stigao",
      detail: "Otvorite prijem: opći podaci, potpis i kratka pitanja prije pregleda.",
      action: row.allowed_actions.includes("open_check_in") ? "reception" : "open",
      actionLabel: row.allowed_actions.includes("open_check_in") ? "Otvori prijem" : "Otvori",
    };
  }
  if (["requested", "booked", "awaiting_forms", "awaiting_documents", "preparation_in_progress", "ready_for_arrival"].includes(row.workflow_stage)) {
    return {
      tone: "gray",
      label: "Čeka dolazak",
      detail: documentContext[row.document_status] || "Pacijent je naručen; prijem počinje kad se javi tajnici ili sestri.",
      action: row.allowed_actions.includes("open_check_in") ? "reception" : "open",
      actionLabel: row.allowed_actions.includes("open_check_in") ? "Otvori prijem" : "Otvori",
    };
  }
  return { tone: "gray", label: "Nije započeto", detail: "Nema trenutne operativne radnje.", action: "open", actionLabel: "Otvori" };
}

export function canonicalJourneyRows(rows: DashboardRow[]) {
  const grouped = new Map<number, DashboardRow>();
  for (const row of rows) {
    const existing = grouped.get(row.journey_id);
    if (!existing) {
      grouped.set(row.journey_id, { ...row, activities: orderedActivities(row) });
      continue;
    }
    const activityById = new Map(existing.activities.map(activity => [activity.id, activity]));
    for (const activity of row.activities ?? []) activityById.set(activity.id, activity);
    grouped.set(row.journey_id, {
      ...existing,
      blockers: [...existing.blockers, ...row.blockers.filter(blocker => !existing.blockers.some(item => item.id === blocker.id))],
      reception_warning: existing.reception_warning || row.reception_warning,
      reception_warning_details: [...new Set([...existing.reception_warning_details, ...row.reception_warning_details])],
      activities: [...activityById.values()].sort((a, b) => a.sequence - b.sequence || minutesFromTime(a.time) - minutesFromTime(b.time)),
    });
  }
  return [...grouped.values()];
}

export function buildTimelineBlocks(rows: DashboardRow[]) {
  const prepared = canonicalJourneyRows(rows).map(row => {
    const state = operationalState(row);
    const window = rowActivityWindow(row);
    return { row, state, startMinutes: window.start, endMinutes: window.end, lane: 0, laneCount: 1, parallel: false, roomName: row.room_name || "Bez prostorije" };
  }).sort((a, b) => a.startMinutes - b.startMinutes || a.endMinutes - b.endMinutes || a.row.journey_id - b.row.journey_id);

  const lanes: number[] = [];
  for (const block of prepared) {
    let lane = lanes.findIndex(end => end <= block.startMinutes);
    if (lane === -1) {
      lane = lanes.length;
      lanes.push(block.endMinutes);
    } else {
      lanes[lane] = block.endMinutes;
    }
    block.lane = lane;
  }
  const laneCount = Math.max(1, lanes.length);
  return prepared.map(block => ({
    ...block,
    laneCount,
    parallel: prepared.some(other =>
      other.row.journey_id !== block.row.journey_id
      && other.startMinutes < block.endMinutes
      && other.endMinutes > block.startMinutes
      && other.row.patient_id !== block.row.patient_id
      && other.row.clinician_id !== block.row.clinician_id
      && other.row.room_id !== block.row.room_id
    ),
  }));
}

export function visibleRange(blocks: TimelineBlock[]) {
  if (!blocks.length) return { start: dayStart, end: dayEnd };
  const earliest = Math.min(...blocks.map(block => block.startMinutes));
  const latest = Math.max(...blocks.map(block => block.endMinutes));
  return {
    start: Math.max(0, Math.min(dayStart, Math.floor(earliest / slotMinutes) * slotMinutes)),
    end: Math.min(24 * 60, Math.max(dayEnd, Math.ceil(latest / slotMinutes) * slotMinutes)),
  };
}

export function timelineSlots(start: number, end: number) {
  const slots = [];
  for (let value = start; value <= end; value += slotMinutes) slots.push(value);
  return slots;
}

export function primaryRoomName(row: DashboardRow, preferredRoomName?: string) {
  const activities = orderedActivities(row);
  if (preferredRoomName && activities.some(activity => activity.room_name === preferredRoomName)) return preferredRoomName;
  return activities.find(activity => activity.room_name)?.room_name || row.room_name || "Bez prostorije";
}

export function groupRowsByRoom(rows: DashboardRow[], preferredRoomName?: string) {
  const grouped = new Map<string, DashboardRow[]>();
  for (const row of canonicalJourneyRows(rows)) {
    const name = primaryRoomName(row, preferredRoomName);
    grouped.set(name, [...(grouped.get(name) ?? []), row]);
  }
  return [...grouped.entries()]
    .map(([roomName, roomRows]) => ({ roomName, blocks: buildTimelineBlocks(roomRows) }))
    .sort((a, b) => a.roomName.localeCompare(b.roomName));
}

export function focusFor(state: OperationalState) {
  if (state.action === "reception") return "arrival";
  if (state.action === "encounter") return "encounter";
  if (state.action === "consumables") return "consumables";
  if (state.action === "billing") return "billing";
  return "attention";
}
