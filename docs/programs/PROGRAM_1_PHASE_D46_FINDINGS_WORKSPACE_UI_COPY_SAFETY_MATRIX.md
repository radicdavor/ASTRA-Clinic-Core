# Program 1 Phase D46 - Findings Workspace UI Copy Safety Matrix

Status: safety copy matrix added during D55-D65 usability hardening

## Purpose

D46 introduced the read-only workspace surface but this matrix was missing from the repository. D55-D65 adds it as the canonical copy reference for the existing panel.

## Matrix

| State | Safe Label | Helper Text | Forbidden Wording | User Action |
| --- | --- | --- | --- | --- |
| Panel title | `Nalazi povezani s izvorom` | `Ovo su source-linked zapisi za pregled.` | diagnosis confirmed, approved, cleared, resolved | None |
| Helper | `Nalaz nije dijagnoza bez lijecnicke potvrde.` | `Za klinicku interpretaciju odgovoran je lijecnik.` | automatic diagnosis, treatment started | None |
| Empty | `Nema prikazanih source-linked finding zapisa.` | Empty does not mean no risk or completed care. | patient safe, patient ready | None |
| Error | `Nalazi trenutno nisu dostupni.` | Error does not mean no open clinical questions. | clinical check failed, blocked | None |
| Permission denied | `Nemate dozvolu za prikaz source-linked nalaza.` | Other workspace data remains available by permission. | approval denied, clearance denied | None |
| Source fallback | `Izvor nije dovoljno specificiran - provjeriti originalni dokument.` | Missing source metadata requires source review. | official truth, confirmed diagnosis | None |

## Boundary

The findings workspace remains read-only. It must not expose review, approve, clear, resolve, task, outcome evidence or patient messaging actions.

