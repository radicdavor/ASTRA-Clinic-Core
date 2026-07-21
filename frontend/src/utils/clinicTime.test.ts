import { describe, expect, test } from "vitest";
import { formatUtcTimestampInClinic, getClinicToday } from "./clinicTime";

describe("clinic timezone helpers", () => {
  test("returns clinic-local today instead of UTC date", () => {
    const instant = new Date("2026-07-20T22:30:00Z");

    expect(getClinicToday("Europe/Zagreb", instant)).toBe("2026-07-21");
    expect(getClinicToday("America/New_York", instant)).toBe("2026-07-20");
  });

  test("formats API UTC timestamp in selected clinic timezone", () => {
    expect(formatUtcTimestampInClinic("2026-07-20T22:30:00Z", "Europe/Zagreb")).toContain("00:30");
  });
});
