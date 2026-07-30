import { describe, expect, test } from "vitest";
import { formatUtcTimestampInClinic, getClinicToday, getClinicTodayForTimezone } from "./clinicTime";

describe("clinic timezone helpers", () => {
  test("returns clinic-local today instead of UTC date", () => {
    const instant = new Date("2026-07-20T22:30:00Z");

    expect(getClinicToday("Europe/Zagreb", instant)).toBe("2026-07-21");
    expect(getClinicToday("America/New_York", instant)).toBe("2026-07-20");
  });

  test("formats API UTC timestamp in selected clinic timezone", () => {
    expect(formatUtcTimestampInClinic("2026-07-20T22:30:00Z", "Europe/Zagreb")).toContain("00:30");
  });

  test.each([
    ["Europe/Zagreb", "2026-03-29T00:30:00Z", "2026-03-29"],
    ["Europe/Zagreb", "2026-10-25T01:30:00Z", "2026-10-25"],
    ["America/Los_Angeles", "2026-07-27T01:30:00Z", "2026-07-26"],
    ["Pacific/Kiritimati", "2026-07-26T11:30:00Z", "2026-07-27"],
    ["Etc/UTC", "2026-07-26T23:30:00Z", "2026-07-26"],
  ])("uses explicit IANA timezone %s for %s", (timezone, instant, expected) => {
    expect(getClinicTodayForTimezone(timezone, new Date(instant))).toBe(expected);
  });

  test("rejects missing and invalid explicit clinic timezones", () => {
    expect(() => getClinicTodayForTimezone("", new Date())).toThrow(RangeError);
    expect(() => getClinicTodayForTimezone("Invalid/Zone", new Date())).toThrow(RangeError);
  });
});
