# Program 1 - Clinical Evidence Timeline Contract

## 1. Svrha

Clinical Evidence Timeline je citljiv prikaz odabranih audit dogadjaja vezanih uz klinicke izvore i source-linked znanje pacijenta.

Svrha timelinea je pomoci korisniku razumjeti:

- kada je izvor kreiran ili ucitan
- kada je AI ekstrakcija generirana
- kada je AI ekstrakcija uredjena ili odbijena
- kada je nastao lijecnicki pregled
- kada je generiran draft sazetka pacijenta
- kada je sazetak pacijenta potvrdjen
- utjece li dogadjaj na sluzbeno Patient Clinical Knowledge

Clinical Evidence Timeline nije novi audit sustav. Nije Outcome Evidence object. Nije Task engine. Nije Clinical Readiness Gate. Nije Workflow Engine. Ne mijenja audit povijest. Ne stvara klinicke cinjenice sam po sebi.

## 2. Razlika izmedju Audit Loga i Clinical Evidence Timelinea

### Audit Log

Audit Log je sirovi operativni zapis za rekonstrukciju dogadjaja.

Audit mora odgovoriti:

- tko je napravio radnju
- sto se promijenilo
- kada se dogodilo
- nad kojim objektom
- kakvo je bilo stanje prije i poslije

### Clinical Evidence Timeline

Clinical Evidence Timeline je filtrirani, oznaceni i korisniku citljiv prikaz audit dogadjaja relevantnih za source-linked klinicko znanje.

Timeline ne zamjenjuje Audit Log. On samo pomaze korisniku razumjeti klinicki vazne evidence korake u postojecem audit tragu.

## 3. Kategorije dogadjaja

Timeline koristi ove kategorije:

- `source_created`
- `source_updated`
- `ai_extraction`
- `ai_rejection`
- `physician_review`
- `summary_generation`
- `summary_review`
- `knowledge_visibility`
- `other`

Nepoznati ili genericki dogadjaji smiju ostati `other`.

## 4. Prikazne oznake

Kanonske hrvatske oznake:

- Source created -> `Izvor kreiran`
- Source uploaded -> `Izvor ucitan`
- Source updated -> `Izvor azuriran`
- AI extracted -> `AI prijedlog generiran`
- AI extraction edited -> `AI prijedlog uredjen`
- AI rejected -> `AI prijedlog odbijen`
- Physician reviewed -> `Lijecnicki pregledano`
- Summary draft generated -> `Draft sazetka generiran`
- Summary reviewed -> `Sazetak potvrdjen`
- Other -> `Drugi audit dogadjaj`

UI smije prikazati labelu koju vrati backend, ali ne smije AI dogadjaj prikazati kao sluzbenu klinicku potvrdu.

## 5. Knowledge impact

Timeline dogadjaj moze imati jednu od ovih oznaka utjecaja:

- `no_official_knowledge_impact`
- `may_enable_official_knowledge`
- `removed_from_official_knowledge`
- `summary_view_only`

Pravila:

- Samo lijecnicki pregledani source dokumenti mogu omoguciti sluzbeno Patient Clinical Knowledge.
- AI dogadjaji sami nikada ne omogucuju sluzbeno znanje.
- Odbijanje AI prijedloga uklanja strukturirani prijedlog iz official knowledge toka, ali ne odbija sirovi izvor.
- Patient summary dogadjaji su summary-view dogadjaji, ne source-of-truth dogadjaji.

## 6. Izvan opsega

Ovaj ugovor ne uvodi:

- formalni Outcome Evidence object
- taskove
- resolution workflow
- klinicke odluke
- patient-facing poruke
- episode timeline
- Clinical Readiness Gate
- Workflow Engine
- real AI provider
- real OCR provider
- stvarne pacijentove podatke
- produkcijske ili certifikacijske tvrdnje
