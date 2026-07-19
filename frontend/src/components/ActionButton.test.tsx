import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { ActionButton } from "./ActionButton";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("ActionButton potvrda", () => {
  test("koristi kontrolirani dijalog umjesto browser-native confirm", async () => {
    const confirmSpy = vi.spyOn(window, "confirm");
    const action = vi.fn();
    render(<ActionButton variant="danger" requiresConfirm confirmMessage="Arhivirati zapis?" onClick={action}>Arhiviraj</ActionButton>);

    fireEvent.click(screen.getByRole("button", { name: "Arhiviraj" }));

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(action).not.toHaveBeenCalled();
    expect(screen.getByRole("dialog")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Potvrdi" }));

    expect(action).toHaveBeenCalledTimes(1);
  });
});
