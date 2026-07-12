import { Provider } from "../types";
export function providerHoursForDate(provider: Provider, date: string) {
  const jsDay = new Date(`${date}T12:00:00`).getDay();
  const day = (jsDay + 6) % 7;
  return provider.weekly_working_hours?.[String(day)] ?? { enabled: true, start: provider.work_start.slice(0, 5), end: provider.work_end.slice(0, 5) };
}
