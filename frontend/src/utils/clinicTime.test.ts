import { describe, expect, test } from "vitest";
import { formatUtcTimestampInClinic, getClinicToday } from "./clinicTime";

describe("clinic timezone helpers", () => {
  test("returns the Europe/Zagreb date in standard time", () => {
    const instant = new Date("2026-01-20T23:30:00Z");

    expect(getClinicToday("Europe/Zagreb", instant)).toBe("2026-01-21");
  });

  test("returns the Europe/Zagreb date in daylight-saving time", () => {
    const instant = new Date("2026-07-20T22:30:00Z");

    expect(getClinicToday("Europe/Zagreb", instant)).toBe("2026-07-21");
  });

  test("uses clinic-local midnight when UTC and clinic dates differ", () => {
    const instant = new Date("2026-07-20T22:30:00Z");

    expect(getClinicToday("America/New_York", instant)).toBe("2026-07-20");
    expect(getClinicToday("Europe/Zagreb", instant)).not.toBe(instant.toISOString().slice(0, 10));
  });

  test("formats API UTC timestamp in selected clinic timezone", () => {
    expect(formatUtcTimestampInClinic("2026-07-20T22:30:00Z", "Europe/Zagreb")).toContain("00:30");
  });

  test("the active clinic timezone changes the same instant's clinic date", () => {
    const instant = new Date("2026-07-20T22:30:00Z");

    localStorage.setItem("astra_active_clinic_timezone", "Europe/Zagreb");
    expect(getClinicToday(undefined, instant)).toBe("2026-07-21");

    localStorage.setItem("astra_active_clinic_timezone", "America/New_York");
    expect(getClinicToday(undefined, instant)).toBe("2026-07-20");
  });
});
