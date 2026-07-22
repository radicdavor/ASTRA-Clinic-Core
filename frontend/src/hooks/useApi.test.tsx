import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { useApi } from "./useApi";

const apiMock = vi.hoisted(() => vi.fn());

vi.mock("../api/client", () => ({
  api: (...args: unknown[]) => apiMock(...args),
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(done => { resolve = done; });
  return { promise, resolve };
}

describe("useApi", () => {
  beforeEach(() => apiMock.mockReset());

  test("prekida prethodni zahtjev i ne dopušta mu prepisivanje novijih podataka", async () => {
    const first = deferred<{ value: string }>();
    const second = deferred<{ value: string }>();
    apiMock.mockImplementation((path: string) => path === "/first" ? first.promise : second.promise);

    const { result, rerender } = renderHook(
      ({ path }) => useApi<{ value: string }>(path, { value: "fallback" }),
      { initialProps: { path: "/first" as string | null } },
    );
    const firstSignal = apiMock.mock.calls[0][1].signal as AbortSignal;

    rerender({ path: "/second" });
    expect(result.current.data.value).toBe("fallback");
    await act(async () => second.resolve({ value: "second" }));
    await waitFor(() => expect(result.current.data.value).toBe("second"));
    expect(firstSignal.aborted).toBe(true);

    await act(async () => first.resolve({ value: "stale" }));
    expect(result.current.data.value).toBe("second");
  });

  test("ne šalje zahtjev dok putanja nije dostupna", async () => {
    const { result } = renderHook(() => useApi<{ value: string }>(null, { value: "fallback" }));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data.value).toBe("fallback");
    expect(result.current.error).toBeNull();
    expect(apiMock).not.toHaveBeenCalled();
  });
});
