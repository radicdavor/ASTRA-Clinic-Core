# Program 1 Phase C83 - Acknowledgment UI Copy State Matrix

Status: UI copy matrix

| State | Safe Croatian label | Safe English label | Helper text | Forbidden wording | User action allowed | Audit implication |
| --- | --- | --- | --- | --- | --- | --- |
| Loading | Ucitavanje zapisa ljudskog pregleda | Loading human review records | Prikaz je read-only. | approval, clearance, override | no | none |
| Empty | Nema zapisa ljudskog pregleda | No human review records | To ne znaci da nema klinickih rizika. | pacijent spreman, cleared | no | none |
| Loaded list | Pregledani savjetodavni signali | Reviewed advisory signals | Zapis pokazuje ljudski pregled signala. | resolved, rijeseno | no | none |
| Detail expanded | Detalji zapisa ljudskog pregleda | Human review record details | Nije klinicko odobrenje i ne mijenja status termina. | postupak odobren | no | none |
| Permission denied | Nemate dozvolu za prikaz zapisa | No permission to view records | Ovo ne mijenja status termina. | clearance denied, blocked | no | none |
| Read error | Zapisi trenutno nisu dostupni | Records unavailable | Ostali dijelovi termina ostaju dostupni. | clearance failure | no | none |
| Stale relation | Kontekst moze biti stariji | Context may be stale | Pregledati izvorni snapshot ili aktualni preview. | resolved | no | none |
| Snapshot missing | Snapshot veza nije dostupna | Snapshot relation unavailable | Acknowledgment ostaje zapis pregleda signala. | invalid, corrected | no | none |
| Advisory signal missing | Signal nije u trenutnom previewu | Signal not in current preview | To ne znaci da je signal rijesen. | rijeseno, cleared | no | none |

## Forbidden Terms

UI must not use:

- odobreno
- clearance
- cleared
- override
- resolved
- rijeseno
- pacijent spreman
- postupak odobren
- task created
- poslano pacijentu

## Zakljucak

All UI states must preserve read-only, no-action semantics.

