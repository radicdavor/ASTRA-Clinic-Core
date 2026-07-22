import { getActiveClinicTimezone } from "../api/client";

export const defaultClinicTimezone = "Europe/Zagreb";

export function getClinicToday(timeZone = getActiveClinicTimezone(), instant = new Date()) {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: timeZone || defaultClinicTimezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(instant);
}

export function formatUtcTimestampInClinic(value: string | null | undefined, timeZone = getActiveClinicTimezone()) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("hr-HR", {
    timeZone: timeZone || defaultClinicTimezone,
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
