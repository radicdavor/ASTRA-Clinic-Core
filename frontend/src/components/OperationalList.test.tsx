import { afterEach, describe, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import {
  EmptyState,
  ListFilterBar,
  OperationalRow,
  ProgressiveDetailPanel,
  RowMoreMenu,
  StatusSummary,
} from "./OperationalList";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("operativni popis", () => {
  test("status uvijek ima tekst i pristupačan opis", () => {
    render(<StatusSummary tone="danger" label="Problem" detail="Nedostaje odobrenje." />);

    const status = screen.getByLabelText("Problem. Nedostaje odobrenje.");
    expect(status.textContent).toContain("Problem");
    expect(status.textContent).toContain("Nedostaje odobrenje.");
  });

  test("red ima jednu primarnu radnju, a ostale smješta u tipkovnički meni", () => {
    render(
      <OperationalRow
        primary="Sintetički zapis"
        status={<StatusSummary label="Čeka pregled" />}
        action={<button type="button">Pregledaj</button>}
        more={<RowMoreMenu label="Dodatne radnje"><button role="menuitem">Otvori audit</button></RowMoreMenu>}
      />
    );

    expect(screen.getAllByText("Pregledaj")).toHaveLength(1);
    const menuButton = screen.getByRole("button", { name: "Dodatne radnje" });
    fireEvent.click(menuButton);
    expect(screen.getByRole("menuitem", { name: "Otvori audit" })).toBeTruthy();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    expect(document.activeElement).toBe(menuButton);
  });

  test("napredni filtri su sklopljeni, broje se i mogu očistiti", () => {
    const clear = vi.fn();
    render(
      <ListFilterBar advanced={<label>Izvor<input /></label>} activeFilterCount={2} onClear={clear}>
        <label>Pretraga<input /></label>
      </ListFilterBar>
    );

    const advanced = screen.getByText("Napredni filtri").closest("details") as HTMLDetailsElement;
    expect(advanced.open).toBe(false);
    expect(screen.getByLabelText("2 aktivnih naprednih filtara")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Očisti" }));
    expect(clear).toHaveBeenCalledTimes(1);
  });

  test("detail panel zadržava fokus, zatvara se Escapeom i vraća fokus", () => {
    const close = vi.fn();
    const { rerender } = render(<button type="button">Izvorni red</button>);
    const trigger = screen.getByRole("button", { name: "Izvorni red" });
    trigger.focus();

    rerender(
      <>
        <button type="button">Izvorni red</button>
        <ProgressiveDetailPanel open title="Tehnički detalj" onClose={close}>
          <button type="button">Prva radnja</button>
          <button type="button">Zadnja radnja</button>
        </ProgressiveDetailPanel>
      </>
    );

    expect(screen.getByRole("dialog", { name: "Tehnički detalj" })).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Zatvori detalj" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(close).toHaveBeenCalledTimes(1);

    rerender(<button type="button">Izvorni red</button>);
    expect(document.activeElement?.textContent).toBe("Izvorni red");
  });

  test("razlikuje prazno, filtrirano, zabranjeno i nedostupno stanje", () => {
    const { rerender } = render(<EmptyState kind="empty" />);
    expect(screen.getByText("Nema zapisa")).toBeTruthy();
    rerender(<EmptyState kind="filtered" />);
    expect(screen.getByText("Nema rezultata za filtre")).toBeTruthy();
    rerender(<EmptyState kind="forbidden" />);
    expect(screen.getByText("Nemate dozvolu")).toBeTruthy();
    rerender(<EmptyState kind="unavailable" />);
    expect(screen.getByRole("alert").textContent).toContain("Podaci trenutno nisu dostupni");
  });
});
