import { afterEach, describe, expect, test } from "vitest";
import {
  calendarWeekday,
  formatShortCalendarDate,
  isCalendarSunday,
  mondayOfCalendarWeek,
  moveCalendarDate,
  parseIsoCalendarDate,
} from "./receptionDate";

const originalTimezone = process.env.TZ;

afterEach(() => {
  process.env.TZ = originalTimezone;
});

describe("Reception ISO calendar-date helpers", () => {
  test.each([
    ["2026-01-31", 1, "2026-02-01"],
    ["2026-03-01", -1, "2026-02-28"],
    ["2026-12-31", 1, "2027-01-01"],
    ["2024-02-28", 1, "2024-02-29"],
    ["2024-02-29", 1, "2024-03-01"],
    ["2026-07-27", 14, "2026-08-10"],
    ["2026-07-27", -14, "2026-07-13"],
  ])("moves %s by %i calendar days to %s", (value, days, expected) => {
    expect(moveCalendarDate(value, days)).toBe(expected);
  });

  test("calculates Monday, Sunday and the Croatian short label without local parsing", () => {
    expect(mondayOfCalendarWeek("2026-08-02")).toBe("2026-07-27");
    expect(calendarWeekday("2026-07-27")).toBe(1);
    expect(isCalendarSunday("2026-08-02")).toBe(true);
    expect(formatShortCalendarDate("2026-08-02")).toBe("Ned 02.08.");
  });

  test.each(["2026-02-29", "2026-13-01", "2026-00-01", "2026-01-32", "26-01-01", "2026-1-01", ""])(
    "rejects invalid ISO calendar date %j",
    (value) => {
      expect(() => parseIsoCalendarDate(value)).toThrow(RangeError);
    }
  );

  test("rejects non-integer offsets", () => {
    expect(() => moveCalendarDate("2026-07-27", 0.5)).toThrow(RangeError);
  });

  test.each(["UTC", "Europe/Zagreb", "Pacific/Kiritimati", "America/Los_Angeles"])(
    "returns identical dates when the process timezone is %s",
    (timezone) => {
      process.env.TZ = timezone;
      expect(moveCalendarDate("2026-12-31", 1)).toBe("2027-01-01");
      expect(mondayOfCalendarWeek("2026-08-02")).toBe("2026-07-27");
      expect(formatShortCalendarDate("2024-02-29")).toBe("Čet 29.02.");
    }
  );
});
