import { beforeEach, describe, expect, test } from "vitest";
import { clearToken, getToken, setToken } from "./client";

describe("auth token storage hardening", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  test("stores new access tokens only in session storage", () => {
    setToken("new-session-token");
    expect(sessionStorage.getItem("astra_token")).toBe("new-session-token");
    expect(localStorage.getItem("astra_token")).toBeNull();
    expect(getToken()).toBe("new-session-token");
  });

  test("migrates legacy localStorage tokens into session storage", () => {
    localStorage.setItem("astra_token", "legacy-token");
    expect(getToken()).toBe("legacy-token");
    expect(sessionStorage.getItem("astra_token")).toBe("legacy-token");
    expect(localStorage.getItem("astra_token")).toBeNull();
  });

  test("clearToken removes session and legacy token copies", () => {
    sessionStorage.setItem("astra_token", "session-token");
    localStorage.setItem("astra_token", "legacy-token");
    clearToken();
    expect(sessionStorage.getItem("astra_token")).toBeNull();
    expect(localStorage.getItem("astra_token")).toBeNull();
  });
});
