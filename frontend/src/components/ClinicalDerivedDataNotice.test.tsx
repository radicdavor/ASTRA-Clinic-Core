import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ClinicalDerivedDataNotice } from "./ClinicalDerivedDataNotice";

describe("ClinicalDerivedDataNotice", () => {
  it("consolidates the clinical safety boundary in one accessible note", () => {
    render(<ClinicalDerivedDataNotice />);

    const notice = screen.getByRole("note", { name: /Pomoćni klinički prikaz.*Sigurnosna napomena/i });
    expect(notice.textContent).toContain("nisu dijagnoza ni izvor istine");
    expect(notice.textContent).toContain("liječnički pregled ostaje obvezan");
    expect(notice.textContent).toContain("ne stvara zadatak");
    expect(notice.textContent).toContain("ne šalje poruku");
  });

  it("supports a concise contextual message without a noisy live region", () => {
    render(
      <ClinicalDerivedDataNotice level="context" title="AI prijedlog">
        Provjerite tvrdnju u izvornom dokumentu.
      </ClinicalDerivedDataNotice>
    );

    const notice = screen.getByRole("note", { name: /AI prijedlog.*Sigurnosna napomena/i });
    expect(notice.textContent).toContain("Provjerite tvrdnju u izvornom dokumentu.");
    expect(notice.getAttribute("aria-live")).toBeNull();
  });
});
