# Program 1 - Glossary and Domain Vocabulary Lock

Status: kanonski rječnik za Program 1, bez implementacije

## 1. Svrha

Ovaj dokument zaključava domenski rječnik za Program 1 - ASTRA Clinical Workflow prije implementacije novih funkcionalnosti.

Rječnik definira kako se pojmovi moraju koristiti u budućim dokumentima, kodu, API imenima, audit događajima i UI labelama.

Ovaj dokument nije implementacija.

Ovaj dokument nije compliance odobrenje.

Ovaj dokument nije produkcijsko odobrenje.

Ovaj dokument ne dopušta stvarne pacijentove podatke.

Ovaj dokument ne certificira ASTRA-u kao EMR.

Ovaj dokument ne certificira ASTRA-u kao medicinski uređaj.

## 2. Vocabulary principles

1. Jedan pojam ima jedno značenje.
2. Sinonimi se ne uvode ako stvaraju drift između dokumentacije, API-ja i UI-ja.
3. Source object se ne smije miješati s interpretiranim findingom.
4. AI suggestion se ne smije miješati s physician-confirmed fact.
5. Operational readiness se ne smije miješati s clinical readiness.
6. Current implemented objects moraju biti jasno odvojeni od future architecture concepts.
7. Hrvatske UI labele smiju postojati, ali kanonski interni arhitektonski pojmovi moraju ostati stabilni.
8. Ako pojam nije u ovom rječniku, budući dokument mora ga definirati prije implementacije.

## 3. Canonical glossary table

| Canonical term | Croatian working label | Definition | Use for | Do not use for | Current / Future / Conceptual | Related terms |
| --- | --- | --- | --- | --- | --- | --- |
| `Patient` | Pacijent | Osoba oko koje se organiziraju klinički, operativni i financijski podaci. | Identitet pacijenta, termini, dokumenti, računi, audit. | Epizodu, termin, račun ili slučaj bez osobe. | Current implemented object | `Patient Workspace`, `Appointment`, `ClinicalDocument` |
| `Patient Workspace` | Radni prostor pacijenta | Primarna objektno-centrična površina za pregled pacijenta. | Pregled identiteta, source-linked knowledge, dokumente, termine, račune, audit. | Generički dashboard ili novi medicinski modul. | Current implemented concept | `Patient`, `Patient Clinical Knowledge`, `Patient Clinical Summary` |
| `Appointment` | Termin | Događaj u vremenu koji povezuje pacijenta, uslugu, providera, sobu i status. | Raspored, dolazak, status, izvedbu usluge, potrošnju materijala. | Kliničku epizodu, dokument ili dijagnozu. | Current implemented object | `Appointment Workspace`, `Service`, `Provider`, `Room` |
| `Appointment Workspace` | Radni prostor termina | Objektno-centrična površina za jedan termin i njegov operativni kontekst. | Status termina, pacijenta, uslugu, sobu, provider, materijal, račun, audit. | Patient Workspace ili Clinical Episode. | Current implemented concept | `Appointment`, `Clinical Readiness Gate`, `Material Consumption` |
| `Reception Workspace` | Recepcijski radni prostor | Operativna dnevna površina za dolazak, identitet i resurse. | Check-in, arrival, raspored, prazne slotove, links prema Patient/Appointment Workspaceu. | Stvaranje kliničke istine ili medicinske odluke. | Current implemented concept | `Appointment`, `Room`, `Provider`, `Operational Readiness` |
| `Service` | Usluga | Katalogizirana usluga s trajanjem, cijenom i potencijalnim workflow/materijalnim zahtjevima. | Naručivanje, raspored, katalog usluga, potrošnju materijala. | Dijagnozu, plan ili epizodu. | Current implemented object | `Appointment`, `Procedure`, `Treatment`, `Material Consumption` |
| `Provider` | Pružatelj usluge | Liječnik ili drugi ovlašteni pružatelj koji sudjeluje u terminu/usluzi. | Raspored, termine, odgovornost, vlasništvo nad budućim planom. | User role bez kliničkog konteksta. | Current implemented object | `Appointment`, `ClinicalPlan`, `Physician Confirmation` |
| `Room` | Soba | Fizički prostor u kojem se održava termin, postupak ili tretman. | Raspored, recepcijski slotovi, konflikt termina. | Kliniku, modul ili uslugu. | Current implemented object | `Appointment`, `Reception Workspace` |
| `ClinicalDocument` | Klinički dokument | Source object koji čuva interni ili vanjski klinički zapis, report, sken, upload metadata ili raw text. | Izvor za patient knowledge, review, AI extraction, source badges. | Finding, summary, diagnosis, official fact. | Current implemented object | `Source Object`, `Finding`, `Patient Clinical Knowledge` |
| `Finding` | Klinička tvrdnja / nalaz | Interpretirana, source-linked klinička tvrdnja izvedena iz jednog ili više ClinicalDocuments ili iz liječničkog unosa. | Ključne nalaze, otvorena pitanja, potvrđene zaključke iz izvora. | Raw document, attachment, AI draft bez reviewa. | Current documentation concept | `ClinicalDocument`, `Source-Linked Statement`, `Physician Review` |
| `Internal ClinicalDocument` | Interni klinički dokument | ClinicalDocument nastao unutar ASTRA-e. | Konzultacije, interne procedure, interne bilješke i procedure reports. | Vanjski nalaz ili skenirani dokument iz druge ustanove. | Current implemented concept | `ClinicalDocument`, `Procedure Report`, `Medical Note` |
| `External ClinicalDocument` | Vanjski klinički dokument | ClinicalDocument nastao izvan ASTRA-e ili uploadan/skeniran kao vanjski izvor. | Vanjsku endoskopiju, patologiju, laboratorij, radiologiju, otpusno pismo, uputnicu. | Interni zaključak bez izvora. | Current implemented concept | `ClinicalDocument`, `Source Object`, `Physician Review` |
| `Patient Clinical Knowledge` | Kliničko znanje o pacijentu | Strukturirano, source-linked tijelo pregledanih kliničkih činjenica i otvorenih pitanja o pacijentu. | Pitanje što znamo, što je nerazriješeno i odakle tvrdnja dolazi. | Sažetak kao izvor istine, epizodu, plan ili dijagnozni registry. | Current implemented concept | `ClinicalDocument`, `Finding`, `Patient Clinical Summary` |
| `Patient Clinical Summary` | Klinički sažetak pacijenta | Sažeti view generiran ili pregledan iz Patient Clinical Knowledgea. | Brzu orijentaciju liječnika u Patient Workspaceu. | Source of truth ili zamjenu za izvorne dokumente. | Current implemented object/concept | `Patient Clinical Knowledge`, `Source-Linked Statement` |
| `Open Question` | Otvoreno pitanje | Source-linked pitanje koje treba kliničku pažnju, ali nije automatska odluka. | Patologija pending, interval nadzora nejasan, kontradiktoran vanjski nalaz. | Task bez potvrde ili dijagnozu. | Current implemented concept | `Unresolved Finding`, `Task`, `Physician Review` |
| `Unresolved Finding` | Nerazriješeni nalaz | Finding koji nakon reviewa ostaje klinički nerazriješen. | Stanja koja zahtijevaju follow-up, pregled, odluku ili monitoring. | Raw document ili AI suspicion bez izvora. | Current documentation concept | `Finding`, `Open Question`, `Outcome Evidence` |
| `Source-Linked Statement` | Tvrdnja povezana s izvorom | Tvrdnja koja ima barem jedan pregledan source object. | Službene stavke patient knowledgea i summary badges. | Unsourced AI output. | Current implemented concept | `ClinicalDocument`, `Official Clinical Fact`, `Audit Evidence` |
| `Physician Review` | Liječnički pregled | Pregled izvora, AI extractiona ili kliničkog zaključka od strane liječnika. | Pretvaranje prijedloga ili dokumenta u eligible official knowledge. | Administrativnu potvrdu identiteta ili naplate. | Current implemented concept | `Physician Confirmation`, `AI Suggestion`, `ClinicalDocument` |
| `Clinical Workflow` | Klinički workflow | Arhitektonski model toka od kliničkog razloga do ishoda, follow-upa ili closurea. | Program 1 tok, ne pojedinačni ekran. | Workflow Engine ili autonomnu automatizaciju. | Current documentation concept | `Patient Journey`, `Clinical Evidence Loop` |
| `Patient Journey` | Put pacijenta | Sekvenca iskustva i skrbi pacijenta od pre-contact faze do ishoda ili nadzora. | Faze kliničkog i operativnog toka. | Jedan termin ili jedan račun. | Current documentation concept | `Clinical Workflow`, `Follow-up`, `Outcome Evidence` |
| `Clinical Episode` | Klinička epizoda | Konkretna pacijentova klinička priča oko problema, cilja, tretmana, nadzora ili follow-upa. | Buduće grupiranje source-linked knowledgea, termina, planova i ishoda. | Dijagnozu, termin, račun, raw document. | Current implemented object but deferred as primary workflow | `Episode-Based Care`, `Episode Closure`, `ClinicalPlan` |
| `Episode-Based Care` | Skrb organizirana oko epizoda | Budući arhitektonski model organizacije skrbi oko Clinical Episodes. | Longitudinalnu skrb nakon stabilnog patient knowledge sloja. | Current primary workflow ili zamjenu za Patient Clinical Knowledge. | Future architecture concept | `Clinical Episode`, `Patient Clinical Knowledge` |
| `ClinicalPlan` | Klinički plan | Klinički smjer skrbi koji može biti AI-drafted ili clinician-confirmed u pacijent/epizoda kontekstu. | Plan što klinički treba uslijediti. | Task, diagnosis, AI suggestion kao službenu odluku. | Deferred concept | `Task`, `AI Suggestion`, `Physician Confirmation` |
| `Task` | Zadatak | Operativna radnja s vlasnikom i rokom koja proizlazi iz plana, findinga, readiness issuea ili workflow koraka. | Tko mora nešto učiniti i kada. | Klinički plan ili službenu kliničku činjenicu. | Future architecture concept | `ClinicalPlan`, `Follow-up`, `Open Question` |
| `Follow-up` | Kontrola / nastavak praćenja | Potreba za sljedećim kliničkim kontaktom, pregledom, dokumentom ili provjerom ishoda. | Kontrolu, recall, ponovni pregled, očekivani sljedeći klinički korak. | Task bez vlasnika ili epizodu samu po sebi. | Current documentation concept | `Task`, `Outcome Evidence`, `Surveillance` |
| `Outcome Evidence` | Dokaz ishoda | Dokumentiran dokaz što se dogodilo nakon plana, tretmana, nalaza ili follow-upa. | Potvrdu eradikacije, pregled patologije, riješenu nuspojavu, status simptoma. | Episode Closure sam po sebi ili audit log bez kliničkog sadržaja. | Future architecture concept | `Finding`, `Episode Closure`, `Clinical Evidence Loop` |
| `Episode Closure` | Zatvaranje epizode | Potvrđena odluka da se epizoda završava, prebacuje u surveillance, referral, lost to follow-up ili administrative closure. | Budući closure događaj s razlogom, dokazima i auditom. | Completed appointment ili brisanje epizode. | Future architecture concept / partially represented by episode status | `Outcome Evidence`, `Surveillance`, `Administrative Closure` |
| `Surveillance` | Nadzor | Stanje u kojem je aktivni problem razriješen ili stabilan, ali je potreban planirani nadzor. | Kolon polyp surveillance, maintenance plan, periodičnu kontrolu. | Aktivni akutni problem ili neodređeni follow-up. | Future architecture concept | `Episode Closure`, `Follow-up`, `Outcome Evidence` |
| `Referral` | Upućivanje | Liječnički potvrđeno usmjeravanje pacijenta prema drugom pružatelju ili ustanovi. | Vanjsku obradu, bolničko liječenje, specijalističku procjenu. | Appointment u ASTRA-i ili administrativni transfer bez kliničkog razloga. | Future architecture concept | `Episode Closure`, `Task`, `Patient Explanation` |
| `Lost to Follow-up` | Izgubljen iz praćenja | Status kada planirani follow-up nije ostvaren unatoč očekivanom nastavku skrbi. | Budući episode status ili outcome state. | Pacijent koji je samo otkazao jedan termin. | Future architecture concept | `Episode Closure`, `Follow-up`, `Audit Evidence` |
| `Administrative Closure` | Administrativno zatvaranje | Closure zbog ne-kliničkog razloga, uz obavezno dokumentiran razlog. | Duplikat, korekciju, napušteni proces bez dostupnog kliničkog nastavka. | Kliničko izlječenje ili surveillance. | Future architecture concept | `Episode Closure`, `Audit Evidence` |
| `Operational Readiness` | Operativna spremnost | Demo/pilot/sistemska spremnost za sljedeću demonstraciju ili pilot odluku. | Pitanje: što blokira sljedeći demo ili pilot. | Spremnost pacijenta za postupak. | Current implemented concept | `ASTRA Readiness Model`, `Operational Evidence Loop` |
| `ASTRA Readiness Model` | ASTRA model operativne spremnosti | Dokumentirani model read-only cockpit provjere demo/pilot rizika. | Release/demo signal, target links, operational blockers/warnings. | Compliance approval, real-data approval, Clinical Readiness Gate. | Current implemented concept | `Operational Readiness`, `Operational Evidence Loop` |
| `Clinical Readiness Gate` | Klinička provjera spremnosti | Procjena je li konkretan pacijent spreman za konkretan planirani klinički čin. | Patient/service/procedure readiness prije konzultacije, postupka ili tretmana. | Demo/pilot readiness ili release readiness. | Future architecture concept | `Ready`, `Not Ready`, `Needs Physician Review` |
| `Ready` | Spreman | Clinical Readiness Gate status da nema poznate prepreke za nastavak. | Pacijent/procedura kontekst. | Demo readiness status bez qualifiera. | Future architecture concept | `Clinical Readiness Gate` |
| `Ready with Warning` | Spreman uz upozorenje | Clinical Readiness Gate status da se može nastaviti uz poznato upozorenje i dokumentiranje. | Nastavak uz oprez i liječničku procjenu. | Potpuno spreman status bez rizika. | Future architecture concept | `Clinical Readiness Gate`, `Physician Confirmation` |
| `Not Ready` | Nije spreman | Clinical Readiness Gate status da postupak ne bi trebao nastaviti bez rješavanja prepreke ili overridea. | Nedostatak uvjeta za planirani klinički čin. | Demo blocker status. | Future architecture concept | `Clinical Readiness Gate`, `Needs Rescheduling` |
| `Needs Physician Review` | Potreban liječnički pregled | Clinical Readiness Gate status koji traži liječničku procjenu prije nastavka. | Antikoagulansi, rizičan nalaz, kontradiktorna dokumentacija. | Običan administrativni zadatak. | Future architecture concept | `Physician Review`, `Clinical Readiness Gate` |
| `Needs Nurse Action` | Potrebna radnja sestre | Clinical Readiness Gate status koji traži sestrinsku pripremu ili provjeru. | Priprema, vitalni podaci, provjera uputa, proceduralna priprema. | Liječničku odluku. | Future architecture concept | `Clinical Readiness Gate`, `Task` |
| `Needs Missing Document` | Nedostaje dokument | Clinical Readiness Gate status da izvor potreban za odluku ili postupak nije dostupan. | Nedostajuću patologiju, uputnicu, pristanak ili vanjski report. | Open Question bez konkretno nedostajućeg izvora. | Future architecture concept | `ClinicalDocument`, `Open Question` |
| `Needs Consent` | Potreban pristanak | Clinical Readiness Gate status da je potreban pristanak prije nastavka. | Endoskopiju, sedaciju, polipektomiju, estetski tretman. | Opći informativni tekst pacijentu. | Future architecture concept | `Consent`, `Clinical Readiness Gate` |
| `Needs Rescheduling` | Potrebno ponovno naručivanje | Clinical Readiness Gate status da trenutni termin treba pomaknuti. | Neadekvatnu pripremu, nedostajuću pratnju, kontraindikaciju za današnji postupak. | Cancellation bez kliničkog razloga. | Future architecture concept | `Appointment`, `Clinical Readiness Gate` |
| `AI Suggestion` | AI prijedlog | AI output koji nema službenu snagu dok ga čovjek ne pregleda/potvrdi. | Predloženi sažetak, finding, plan, explanation ili upozorenje. | Official Clinical Fact ili physician decision. | Current implemented concept | `AI Draft`, `AI Extraction`, `Physician Review` |
| `AI Draft` | AI nacrt | Draft oblik teksta ili strukture koji je pripremio AI. | Nacrt Medical Notea, Patient Explanationa, summaryja ili plana. | Finalizirani dokument. | Current implemented concept | `AI Suggestion`, `Medical Note`, `Patient Explanation` |
| `AI Extraction` | AI ekstrakcija | AI ili placeholder postupak izdvajanja strukture iz ClinicalDocumenta. | Sažetak, key findings, recommendations iz izvora. | Službenu činjenicu bez reviewa. | Current implemented concept | `ClinicalDocument`, `AI Suggestion`, `Physician Review` |
| `AI Confidence` | AI razina sigurnosti | Signal koliko je AI siguran u vlastitu ekstrakciju ili prijedlog. | UI upozorenje i potrebu za ručnim pregledom. | Medicinsku sigurnost ili dokaz istinitosti. | Future architecture concept | `AI Suggestion`, `Physician Review` |
| `Physician Confirmation` | Liječnička potvrda | Liječnička radnja kojom prijedlog, plan, explanation ili klinička tvrdnja postaje službena. | Kliničke odluke i medicinski relevantne potvrde. | Administrativnu potvrdu ili sestrinsku provjeru. | Current documentation concept | `Physician Review`, `Official Clinical Fact` |
| `Human Confirmation` | Ljudska potvrda | Potvrda ovlaštenog čovjeka kada ne mora biti isključivo liječnik. | Administrativne ili operativne potvrde gdje je dopušteno. | Kliničke odluke koje traže liječnika. | Current documentation concept | `Physician Confirmation`, `Task` |
| `Accepted AI Suggestion` | Prihvaćen AI prijedlog | AI Suggestion prihvaćen nakon propisanog human/physician reviewa. | Prihvaćeni sažetak, extraction ili draft. | AI output koji nije pregledan. | Future architecture concept | `AI Suggestion`, `Physician Confirmation` |
| `Rejected AI Suggestion` | Odbijen AI prijedlog | AI Suggestion koji ovlašteni korisnik odbija. | Izbacivanje prijedloga iz official knowledge toka. | Brisanje izvornog dokumenta. | Future architecture concept | `AI Suggestion`, `Audit Evidence` |
| `Deferred AI Suggestion` | Odgođen AI prijedlog | AI Suggestion koji još čeka pregled ili odluku. | Pending review state. | Prihvaćenu ili odbijenu tvrdnju. | Future architecture concept | `AI Suggestion`, `Physician Review` |
| `Superseded AI Suggestion` | Zamijenjen AI prijedlog | AI Suggestion koji je kasnije zamijenjen novijom verzijom ili ljudskom izmjenom. | Povijest prijedloga i audit. | Aktivni službeni zaključak. | Future architecture concept | `AI Suggestion`, `Audit Evidence` |
| `Medical Note` | Medicinska bilješka | Profesionalna klinička dokumentacija namijenjena medicinskom zapisu i liječnicima. | Zaključak pregleda, proceduralni zapis, kliničku dokumentaciju. | Patient-facing objašnjenje. | Future architecture concept | `Patient Explanation`, `Procedure Report` |
| `Patient Explanation` | Objašnjenje pacijentu | Pacijentu razumljivo objašnjenje nalaza, značenja, uputa i alarmnih simptoma. | Pacijent-facing tekst nakon potvrde. | Medical Note ili službeni raw report. | Future architecture concept | `Medical Note`, `Physician Confirmation` |
| `Consent` | Pristanak | Dokumentirana suglasnost ili informirani pristanak potreban za određeni postupak/tretman. | Readiness i procedure/treatment preduvjete. | Patient Explanation ili edukativni tekst. | Current documentation concept | `Clinical Readiness Gate`, `Procedure`, `Treatment` |
| `Procedure Report` | Izvještaj o postupku | Profesionalni zapis o izvedenom medicinskom postupku. | Endoskopiju, biopsiju, polipektomiju ili drugi postupak. | Patient Explanation. | Future architecture concept | `Procedure`, `Medical Note`, `ClinicalDocument` |
| `Treatment Record` | Zapis tretmana | Profesionalni zapis o izvedenom tretmanu, posebno u estetskoj medicini. | Proizvod, regiju, količinu, tehniku, batch/lot i rezultat. | Račun ili opći Patient Explanation. | Future architecture concept | `Treatment`, `Product`, `Batch/Lot` |
| `Audit Evidence` | Audit dokaz | Rekonstruktibilan trag važne radnje, odluke, izvora, prijedloga i potvrde. | Tko, što, kada, zašto, izvor i posljedicu. | UI toast ili neformalnu bilješku. | Current implemented concept | `Clinical Evidence Loop`, `Operational Evidence Loop` |
| `Clinical Evidence Loop` | Klinički evidence loop | Budući klinički nastavak evidence razmišljanja: clinical need/risk -> workspace -> physician-confirmed action -> audit -> outcome evidence. | Program 1 klinički tok i buduće outcome evidence. | Release readiness loop. | Current documentation concept | `Outcome Evidence`, `Audit Evidence` |
| `Operational Evidence Loop` | Operativni evidence loop | Postojeći loop: readiness -> workspace -> action -> audit -> pilot/release evidence. | Demo/pilot operativne rizike i release dokaze. | Klinički outcome dokaz sam po sebi. | Current implemented concept | `Operational Readiness`, `ASTRA Readiness Model` |
| `Source Object` | Izvorni objekt | Objekt koji čuva original ili metadata izvora za tvrdnju. | ClinicalDocument, procedure/treatment report ili budući source record. | Interpretirani finding. | Current implemented concept | `ClinicalDocument`, `Source-Linked Statement` |
| `Official Clinical Fact` | Službena klinička činjenica | Klinička tvrdnja koja je physician-reviewed/confirmed ili direktno unesena od ovlaštenog kliničara. | Službeni patient knowledge. | AI suggestion, draft ili unsourced statement. | Current documentation concept | `Finding`, `Physician Confirmation`, `Patient Clinical Knowledge` |
| `Procedure` | Postupak | Medicinski čin/procedura s tehničkim i kliničkim zapisom. | Gastroskopiju, kolonoskopiju, biopsiju, polipektomiju. | Estetski treatment kada je bolje modeliran kao tretman. | Future architecture concept | `Procedure Report`, `Service`, `Material Consumption` |
| `Treatment` | Tretman | Terapijski ili estetski čin koji dokumentira proizvod, tehniku, regiju i ishod. | Filler, botulinum toxin, biostimulator, mezoterapiju. | Procedure report kada je riječ o medicinskoj proceduri. | Future architecture concept | `Treatment Record`, `Product`, `Batch/Lot` |
| `Material Consumption` | Potrošnja materijala | Evidencija potrošnje zaliha povezana s terminom, postupkom ili tretmanom. | FEFO potrošnju, procedure materials, treatment product usage. | Klinički ishod ili računsku stavku bez stock veze. | Current implemented object/concept | `Inventory Movement`, `Product`, `Batch/Lot` |
| `Product` | Proizvod | Materijal, lijek, filler ili drugi proizvod korišten u postupku/tretmanu. | Inventar, tretmane, batch/lot evidenciju. | Uslugu ili proceduru. | Current implemented object/concept | `Material Consumption`, `Batch/Lot`, `Inventory Movement` |
| `Batch/Lot` | Serija / lot | Identifikator proizvodne serije proizvoda ili materijala. | Traceability, rok trajanja, sigurnost i audit potrošnje. | SKU ili naziv usluge. | Current implemented object/concept | `Product`, `Inventory Movement`, `Treatment Record` |
| `Inventory Movement` | Kretanje inventara | Auditabilna promjena zalihe. | Zaprimanje, potrošnju, korekciju, FEFO trag. | Kliničku odluku ili outcome evidence. | Current implemented object/concept | `Material Consumption`, `Product`, `Batch/Lot` |

### Critical distinctions

#### ClinicalDocument vs Finding

`ClinicalDocument` je source object.

Može biti interni dokument, vanjski dokument, patologija, laboratorij, radiologija, otpusno pismo, uputnica, procedure note, skenirani tekst ili upload metadata.

`Finding` je interpretirana, source-linked klinička tvrdnja izvedena iz jednog ili više ClinicalDocuments ili iz physician-entered clinical act.

Finding nije raw document.

Finding ne smije postati official osim ako je pregledan ili unesen od ovlaštenog kliničara.

#### Patient Clinical Knowledge vs Patient Clinical Summary

`Patient Clinical Knowledge` je strukturirano, source-linked tijelo reviewed clinical facts i open questions o pacijentu.

`Patient Clinical Summary` je generated ili physician-reviewed summary view tog znanja.

Summary nije source of truth.

Underlying reviewed, source-linked knowledge je source of truth.

#### Operational Readiness vs Clinical Readiness Gate

`Operational Readiness` i `ASTRA Readiness Model` odnose se na demo/pilot/system readiness.

Odgovaraju na pitanje:

`Što blokira sljedeći demo ili pilot?`

`Clinical Readiness Gate` odnosi se na patient/service/procedure-specific readiness.

Odgovara na pitanje:

`Je li ovaj pacijent spreman za ovaj planirani klinički čin?`

Ovi pojmovi se ne smiju spajati.

#### AI Suggestion vs Official Clinical Fact

`AI Suggestion` nije služben.

`Official Clinical Fact` postoji samo nakon physician review/confirmation ili direct clinician entry.

AI output mora ostati vidljivo označen dok nije pregledan.

#### ClinicalPlan vs Task

`ClinicalPlan` je clinician-confirmed ili AI-drafted clinical plan za epizodni ili pacijentov kontekst.

`Task` je operativna radnja nastala iz plana, findinga, readiness issuea ili workflow koraka.

Plan objašnjava što se klinički treba dogoditi.

Task dodjeljuje tko mora nešto učiniti i kada.

#### Clinical Episode vs Episode-Based Care

`Clinical Episode` je konkretna pacijentova klinička priča ili problem.

`Episode-Based Care` je budući arhitektonski model organizacije skrbi oko epizoda.

Program 1 smije definirati model, ali implementacija ostaje buduća i ne smije zaobići Patient Clinical Knowledge.

#### Medical Note vs Patient Explanation

`Medical Note` je profesionalna klinička dokumentacija.

`Patient Explanation` je pacijent-facing objašnjenje.

AI smije draftati oba.

Physician ili authorized human confirmation je potreban prije finalizacije/slanja.

#### Outcome Evidence vs Episode Closure

`Outcome Evidence` bilježi što se dogodilo nakon plana ili tretmana.

`Episode Closure` je physician-confirmed ili administratively documented odluka da je epizoda završena, prebačena u surveillance, referral, lost to follow-up ili administrative closure.

Outcome evidence može podržati closure, ali nije isto što i closure.

## 4. Preferred naming rules

- Koristiti `ClinicalDocument` za source documents.
- Koristiti `Finding` samo za interpreted clinical statements.
- Koristiti `Patient Clinical Knowledge` za source-linked reviewed knowledge.
- Koristiti `Patient Clinical Summary` samo za summary view.
- Koristiti `Operational Readiness` za demo/pilot readiness.
- Koristiti `Clinical Readiness Gate` za patient/procedure readiness.
- Koristiti `AI Suggestion` za AI output koji još nije confirmed.
- Koristiti `Physician Confirmation` za clinical confirmation by physician.
- Koristiti `Human Confirmation` samo kada je non-physician confirmation eksplicitno dopuštena.
- Koristiti `Medical Note` za professional documentation.
- Koristiti `Patient Explanation` za patient-facing text.
- Koristiti `Outcome Evidence` za follow-up result evidence.
- Koristiti `Episode Closure` za closure decision/status.

## 5. Terms to avoid or restrict

| Term | Problem | Preferred replacement |
| --- | --- | --- |
| `nalaz` when used ambiguously | Može značiti dokument, finding, report ili zaključak. | `ClinicalDocument` za izvor; `Finding` za interpretiranu tvrdnju. |
| `finding` when used for raw document | Miješa izvor i interpretaciju. | `ClinicalDocument` |
| `readiness` without qualifier | Ne razlikuje demo/pilot readiness od clinical readinessa. | `Operational Readiness` ili `Clinical Readiness Gate` |
| `AI decision` | Sugerira da AI odlučuje. | `AI Suggestion` |
| `AI diagnosis` | Sugerira autonomnu medicinsku odluku. | `AI Suggestion for physician review` |
| `automatic treatment plan` | Sugerira automatsku terapijsku odluku. | `AI Draft ClinicalPlan pending Physician Confirmation` |
| `official AI summary` | Sugerira da AI output može biti služben bez reviewa. | `Physician-reviewed Patient Clinical Summary` |
| `episode engine` when used as current implementation | Može vratiti deferred koncept u primarni workflow. | `Deferred Episode-Based Care` ili `Clinical Episode as deferred workflow` |
| `closure` without closure reason | Ne objašnjava zašto je skrb završena. | `Episode Closure with closure reason` |
| `task` when actually meaning clinical plan | Miješa kliničku namjeru i operativnu radnju. | `ClinicalPlan` |
| `summary` when actually meaning source of truth | Sažetak nije izvor istine. | `Patient Clinical Knowledge` ili `Source-Linked Statement` |

## 6. Current vs future architecture

| Term | Current status | Notes |
| --- | --- | --- |
| `Patient` | Current implemented object | Osnovni objekt sustava. |
| `Patient Workspace` | Current implemented concept | Primarna pacijentova površina. |
| `Appointment` | Current implemented object | Temelj rasporeda i patient flowa. |
| `Appointment Workspace` | Current implemented concept | Detail/workspace pattern postoji. |
| `Reception Workspace` | Current implemented concept | Operativna dnevna površina. |
| `Service` | Current implemented object | Katalog usluga. |
| `Provider` | Current implemented object | Pružatelji usluge. |
| `Room` | Current implemented object | Sobe/resursi rasporeda. |
| `ClinicalDocument` | Current implemented object | Temelj patient knowledge sloja. |
| `Patient Clinical Summary` | Current implemented object/concept | Postoji kao summary/review foundation. |
| `Patient Clinical Knowledge` | Current implemented concept | Prikaz source-linked reviewed znanja. |
| `Finding` | Current documentation concept | Još nije zaključan kao zaseban implementirani objekt. |
| `Open Question` | Current implemented concept | Prikazuje nerazriješene stavke, ali treba daljnji lifecycle. |
| `Operational Readiness` | Current implemented concept | `/readiness` i postojeći model. |
| `ASTRA Readiness Model` | Current implemented concept | Demo/pilot readiness, nije compliance. |
| `Clinical Episode` | Current implemented object but deferred as primary workflow | Postoji kompatibilno, ali nije primarni tok. |
| `Episode-Based Care` | Future architecture concept | Smije doći tek nakon stabilnog patient knowledge sloja. |
| `ClinicalPlan` | Deferred concept | Ne smije se implementirati prije jasnog lifecyclea. |
| `Task` | Future architecture concept | Treba odlučiti generički vs klinički scope. |
| `Clinical Readiness Gate` | Future architecture concept | Odvojeno od Operational Readinessa. |
| `Outcome Evidence` | Future architecture concept | Treba minimalni evidence contract. |
| `Episode Closure` | Future architecture concept / partially represented by episode status | Ne smije se tretirati kao current primary workflow. |
| `AI Suggestion` | Current implemented concept | Placeholder AI extraction postoji; real AI nije implementiran. |
| `Physician Review` | Current implemented concept | ClinicalDocument review foundation postoji. |
| `Physician Confirmation` | Current documentation concept | Treba formalizirati po domenama. |
| `Medical Note` | Future architecture concept | Nije sada implementiran kao formalni output. |
| `Patient Explanation` | Future architecture concept | Nije sada implementiran kao formalni output. |
| `Audit Evidence` | Current implemented concept | Audit log postoji; klinička semantika se mora dalje zaključati. |
| `Material Consumption` | Current implemented object/concept | Postoji kroz inventory/appointment flow. |
| `Inventory Movement` | Current implemented object/concept | Postoji kroz inventar. |

## 7. UI and API terminology implications

Hrvatske UI labele smiju biti prirodne za korisnika, ali arhitektonski dokumenti, API payloadi, route naming i audit event names moraju slijediti kanonske pojmove.

Budući UI/API rad treba poštovati sljedeće:

- UI može prikazati `Klinički dokument`, ali arhitektura i kod trebaju zadržati `ClinicalDocument`.
- API fields ne smiju koristiti dvosmisleno ime `readiness` bez konteksta.
- Budući API treba preferirati nazive poput `clinical_readiness_status` i `operational_readiness_status`.
- Clinical documents ne smiju izložiti AI output kao reviewed facts ako status ne potvrđuje review.
- Patient-facing tekst mora se zvati `Patient Explanation`, ne generički `summary`.
- Summary API ne smije implicirati da je summary source of truth.
- Audit event names trebaju razlikovati `ai_suggestion_created`, `physician_review_completed`, `physician_confirmation_recorded` i `official_clinical_fact_created`.
- Route naming za buduće clinical readiness funkcije mora izbjeći konflikt s postojećim `/readiness`.

Ovaj dokument ne dizajnira točne endpointove.

Ovaj dokument definira naming implications za budući mapping.

## 8. Relationship to future implementation

Budući Codex implementation promptovi za Program 1 moraju koristiti ovaj glossary.

Prije implementacije Program 1 koda budući zadaci trebaju mapirati:

- postojeće backend modele na canonical terms
- postojeće schemas na canonical terms
- frontend labele na canonical terms
- route naming na canonical terms
- audit event names na canonical terms
- readiness nazive na Operational Readiness vs Clinical Readiness Gate
- AI review status names na AI Suggestion / Physician Review / Physician Confirmation lifecycle

Ovaj mapping se ne provodi u kodu u ovom zadatku.

## 9. Open terminology questions

1. Treba li `Finding` kasnije postati zaseban implemented object ili ostati strukturirani output izveden iz `ClinicalDocument`?

   Preporučeni smjer: prvo ga zadržati kao strukturirani, source-linked output; zaseban objekt uvoditi samo ako lifecycle i audit to stvarno zahtijevaju.

2. Treba li `Task` biti generički operativni objekt dijeljen između clinical/admin/inventory područja ili clinical-only workflow objekt?

   Preporučeni smjer: generički operativni objekt s domain contextom, jer ASTRA ima recepciju, inventar, račune i kliničke radnje.

3. Treba li `Outcome Evidence` biti zaseban objekt, tip dokumenta ili dio episode closurea?

   Otvoreno. Preporučeni smjer je prvo definirati minimalni evidence contract prije odluke o implementacijskom obliku.

4. Koje potvrde zahtijevaju liječnika, a koje smiju napraviti sestra ili administracija?

   Otvoreno. Kliničke odluke i patient-facing medicinski zaključci zahtijevaju `Physician Confirmation`; operativne potvrde mogu koristiti `Human Confirmation` ako je pravilo izričito.

5. Treba li `ClinicalPlan` ostati vezan uz epizodu ili kasnije podržati patient-level plan prije episode groupinga?

   Otvoreno. S obzirom da Patient Clinical Knowledge dolazi prije epizoda, treba razmotriti patient-level plan draft, ali official plan treba imati jasan kontekst.

6. Treba li `Patient Explanation` postati vlastiti document type ili se generirati iz Medical Note plus plan?

   Otvoreno. Preporučeni smjer je tretirati ga kao zaseban patient-facing output povezan s Medical Noteom, planom i izvorima.

## 10. Go / No-Go recommendation

Recommendation: Go.

Program 1 je spreman za sljedeći arhitektonski korak:

`Program 1 - Domain Object Mapping`

Taj korak treba mapirati glossary na postojeće backend modele, frontend stranice, API rute i dokumentaciju, i dalje bez implementacije novih workflow funkcionalnosti.

Ovo nije Go za produkciju.

Ovo nije Go za stvarne pacijentove podatke.

Ovo nije Go za certificirani EMR ili medical-device tvrdnje.
