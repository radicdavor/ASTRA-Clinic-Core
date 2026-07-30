export type IsoCalendarDateParts = {
  year: number;
  month: number;
  day: number;
};

const isoCalendarDatePattern = /^(\d{4})-(\d{2})-(\d{2})$/;
const weekdayLabels = ["Ned", "Pon", "Uto", "Sri", "Čet", "Pet", "Sub"];

function isLeapYear(year: number) {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

function daysInMonth(year: number, month: number) {
  if (month === 2) return isLeapYear(year) ? 29 : 28;
  return [4, 6, 9, 11].includes(month) ? 30 : 31;
}

export function parseIsoCalendarDate(value: string): IsoCalendarDateParts {
  const match = isoCalendarDatePattern.exec(value);
  if (!match) throw new RangeError("Calendar date must use YYYY-MM-DD.");
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) {
    throw new RangeError("Calendar date is not valid.");
  }
  return { year, month, day };
}

function toUtcCalendarDate({ year, month, day }: IsoCalendarDateParts) {
  const date = new Date(0);
  date.setUTCHours(12, 0, 0, 0);
  date.setUTCFullYear(year, month - 1, day);
  return date;
}

function fromUtcCalendarDate(date: Date) {
  const year = date.getUTCFullYear();
  if (year < 1 || year > 9999) throw new RangeError("Calendar date is outside the supported range.");
  return `${String(year).padStart(4, "0")}-${String(date.getUTCMonth() + 1).padStart(2, "0")}-${String(date.getUTCDate()).padStart(2, "0")}`;
}

export function moveCalendarDate(value: string, days: number) {
  if (!Number.isInteger(days)) throw new RangeError("Calendar-day offset must be an integer.");
  const date = toUtcCalendarDate(parseIsoCalendarDate(value));
  date.setUTCDate(date.getUTCDate() + days);
  return fromUtcCalendarDate(date);
}

export function calendarWeekday(value: string) {
  return toUtcCalendarDate(parseIsoCalendarDate(value)).getUTCDay();
}

export function mondayOfCalendarWeek(value: string) {
  const daysSinceMonday = (calendarWeekday(value) + 6) % 7;
  return moveCalendarDate(value, -daysSinceMonday);
}

export function isCalendarSunday(value: string) {
  return calendarWeekday(value) === 0;
}

export function formatShortCalendarDate(value: string) {
  const { month, day } = parseIsoCalendarDate(value);
  return `${weekdayLabels[calendarWeekday(value)]} ${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.`;
}
