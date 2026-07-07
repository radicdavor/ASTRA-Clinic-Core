# Program 1 Phase B1 - Clinical Readiness Vocabulary

Status: documentation-only vocabulary lock

## 1. Svrha

Ovaj dokument zakljucava rjecnik za Clinical Readiness prije bilo kakve implementacije.

Ovaj dokument je:

- documentation-only
- bez koda
- bez API-ja
- bez database modela
- bez UI-ja
- bez produkcijskog odobrenja
- bez real-data odobrenja
- bez certified EMR claim
- bez medical-device claim

Svrha je da buduci dokumenti, API ugovori, UI labele i audit dogadaji koriste isti jezik i ne pomijesaju klinicku spremnost s postojecim operativnim readinessom.

## 2. Vocabulary principles

- jedan pojam ima jedno znacenje
- `Clinical Readiness` se nikada ne skracuje u generic `readiness`
- `Operational Readiness` i `Clinical Readiness` ostaju odvojeni modeli
- AI suggestions nisu readiness decisions
- readiness item nije task
- readiness warning nije diagnosis
- readiness override nije automatic clearance
- clinical readiness je patient/service/procedure-specific
- clinical readiness ne zahtijeva Clinical Episode
- clinical readiness smije citati samo reviewed Patient Clinical Knowledge
- Patient Clinical Summary nije source of truth
- Open Question moze postati readiness concern, ali ne automatski task

## 3. Canonical terms

| Term | Croatian working label | Definition | Use for | Do not use for | Current/future status |
| --- | --- | --- | --- | --- | --- |
| `Clinical Readiness Gate` | Klinicka provjera spremnosti | Patient/service/procedure-specific model koji procjenjuje moze li planirani klinicki cin ici dalje. | Buduci klinicki readiness model za appointment/service/procedure kontekst. | Demo/pilot readiness, compliance approval, AI decision. | Documentation-only future concept |
| `Clinical Readiness Status` | Status klinicke spremnosti | Agregirani status gatea iz readiness itema. | Prikaz ukupne spremnosti za konkretan planirani cin. | Appointment status ili release readiness status. | Documentation-only future concept |
| `Clinical Readiness Item` | Stavka klinicke spremnosti | Jedna provjerljiva stavka koja moze biti informacija, upozorenje, blok, nedostajuci dokument ili potrebna potvrda. | Buduce readiness liste i previewe. | Task, diagnosis, clinical fact. | Documentation-only future concept |
| `Clinical Readiness Category` | Kategorija klinicke spremnosti | Grupiranje itema po smislu: identity, medication, consent, preparation itd. | Organizaciju itema i UI grupiranje. | Modul ili specialty engine. | Documentation-only future concept |
| `Clinical Readiness Severity` | Tezina klinicke spremnosti | Tezina itema: info, warning, blocking, critical. | UI ton i prioritet paznje. | Medicinsku dijagnozu ili rizik bez izvora. | Documentation-only future concept |
| `Clinical Readiness Source` | Izvor klinicke spremnosti | Izvor iz kojeg dolazi item ili dokaz. | Source badges, evidence mapping i audit. | Unsourced AI output. | Documentation-only future concept |
| `Clinical Readiness Responsible Role` | Odgovorna uloga | Uloga koja smije rijesiti ili potvrditi item. | Physician, nurse, admin, system boundaries. | RBAC bez klinickog konteksta. | Documentation-only future concept |
| `Clinical Readiness Suggested Action` | Predlozena radnja | Sigurni prijedlog sto korisnik treba pregledati ili uciniti. | Upute korisniku u previewu. | Automatsku odluku ili task bez potvrde. | Documentation-only future concept |
| `Clinical Readiness Block` | Klinicki blok | Stavka koja sprjecava nastavak dok nije rijesena ili overrideana po pravilima. | Buduce blokirajuce iteme. | Generic UI error ili demo blocker. | Documentation-only future concept |
| `Clinical Readiness Warning` | Klinicko upozorenje | Stavka koja trazi paznju, ali ne mora automatski blokirati. | Upozorenja uz source i odgovornu ulogu. | Dijagnozu ili AI zakljucak. | Documentation-only future concept |
| `Clinical Readiness Override` | Override klinicke spremnosti | Ljudski zabiljezena odluka da se ide dalje unatoc warningu/bloku kada je to dozvoljeno. | Kontrolirani override s razlogom i auditom. | Automatic clearance ili AI odluku. | Documentation-only future concept |
| `Clinical Readiness Override Reason` | Razlog overridea | Obavezno obrazlozenje za override. | Audit i rekonstrukciju odluke. | Slobodni komentar bez odgovornosti. | Documentation-only future concept |
| `Clinical Readiness Confirmation` | Potvrda klinicke spremnosti | Ljudska potvrda itema ili ukupnog statusa gdje je to dopusteno. | Physician/nurse/admin potvrde prema ulozi. | AI clear ili automatsku potvrdu. | Documentation-only future concept |
| `Clinical Readiness Preview` | Pregled klinicke spremnosti | Read-only buduci prikaz predlozenih itema i statusa. | Prvu sigurnu implementaciju u Appointment Workspaceu. | Enforcing blocker. | Recommended future first implementation |
| `Clinical Readiness Snapshot` | Snimka klinicke spremnosti | Trenutna zabiljezena slika itema/statusa u odredenom trenutku. | Buducu auditabilnu povijest readiness pregleda. | Outcome Evidence ili clinical decision sam po sebi. | Future candidate |
| `Operational Readiness` | Operativna spremnost | Postojeci demo/pilot readiness model. | `/api/readiness`, Readiness Cockpit, pilot/demo rizike. | Spremnost pacijenta za postupak. | Current implemented concept |
| `Readiness Cockpit` | Kokpit operativne spremnosti | UI za Operational Readiness. | Demo/pilot pregled blokera i upozorenja. | Clinical Readiness Gate UI. | Current implemented concept |
| `Readiness Target Path` | Ciljna putanja spremnosti | Link iz Operational Readiness checka na ekran gdje se rizik pregleda. | Postojeci operational readiness target contract. | Clinical readiness source evidence link bez kvalifikacije. | Current implemented concept |

## 4. Forbidden / restricted terms

| Term | Problem | Preferred replacement |
| --- | --- | --- |
| `readiness` without qualifier | Ne razlikuje operativnu i klinicku spremnost. | `Operational Readiness` ili `Clinical Readiness Gate` |
| `AI readiness decision` | Sugerira da AI donosi odluku. | `AI-suggested readiness concern` |
| `procedure allowed by AI` | Direktno krsi nacelo da lijecnik odlucuje. | `Clinical Readiness Preview pending physician review` |
| `auto-clear` | Sugerira automatsko ciscenje rizika. | `human-confirmed readiness item` |
| `clinical blocker` without source | Blok bez izvora ne moze biti rekonstruiran. | `source-linked clinical readiness block` |
| `task` when meaning readiness item | Mijesa provjeru spremnosti s operativnom radnjom. | `Clinical Readiness Item` |
| `diagnosis` when meaning readiness warning | Readiness warning nije dijagnoza. | `Clinical Readiness Warning` |
| `episode readiness` before Episode-Based Care reactivation | Prerano vraca epizode kao primarni workflow. | `Clinical Readiness for appointment/service/procedure` |
| `production readiness` when meaning clinical readiness | Mijesa produkcijski status i klinicku spremnost pacijenta. | `Clinical Readiness Status` |

## 5. UI naming rules

Buduce UI labele trebaju koristiti jasne kvalifikatore:

- `Klinicka spremnost`
- `Operativna spremnost`
- `Ceka lijecnicki pregled`
- `Potrebna sestrinska provjera`
- `Nedostaje dokument`
- `Potreban pristanak`
- `Spremno uz upozorenje`
- `Nije spremno`
- `Blokirano`
- `Override uz razlog`

UI ne smije prikazati:

- AI prijedlog kao finalnu readiness odluku
- generic `Spremnost` ako na istom proizvodu postoje i Operational i Clinical Readiness
- Open Question kao task
- Patient Clinical Summary kao source of truth

Ovaj dokument ne implementira UI.

