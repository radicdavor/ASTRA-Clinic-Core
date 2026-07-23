# Protokol sintetičke human usability provjere

## Status i granice

Ovaj dokument je izvršivi paket za buduću moderiranu ljudsku provjeru. Sama
izrada paketa i automatizirani preflight nisu dokaz da je ljudska evaluacija
provedena.

Koristiti samo jasno sintetičke pacijente. Moderator prekida sesiju ako se
pojavi stvarni identitet, nedopušten klinički sadržaj ili mogućnost rada izvan
scopea. Sesija ne odobrava produkciju, stvarne podatke ni kliničku uporabu.

## Pokretanje

Preduvjeti:

- lokalni PostgreSQL dostupan je na testnom portu prema E2E konfiguraciji;
- backend virtualno okruženje i frontend paketi već su instalirani;
- radno stablo je čisto.

Tehnički preflight:

```powershell
cd frontend
npm run usability:preflight
```

Moderirana sesija:

```powershell
cd frontend
npm run usability:session
```

Runner stvara vlastitu privremenu PostgreSQL bazu, pokreće backend i frontend
na slobodnim izoliranim portovima, učitava sintetičke podatke i ispisuje lokalni
URL te sintetičke pristupne podatke. `Ctrl+C` gasi samo procese koje je runner
pokrenuo i uklanja njegovu privremenu bazu.

Moderator prije prvog zadatka mora potvrditi:

1. zaglavlje jasno označava demo okruženje;
2. odabir `Demo prikaz uloge` nudi svih pet persona;
3. nema stvarnih podataka;
4. evaluator razumije da se ne donose stvarne kliničke odluke.

## Mjerenja

Za svaki zadatak bilježiti:

- uspjeh bez pomoći: `da` / `ne`;
- vrijeme u sekundama;
- broj pogrešnih klikova;
- broj povrataka na prethodni ekran;
- zastajanje dulje od deset sekundi;
- potrebnu moderatorsku pomoć;
- subjektivnu sigurnost u sljedeću radnju od 1 do 5;
- kratku opaženu poteškoću, bez stvarnog PHI-ja.

## Zadaci po personi

### Administrator

1. Pronaći problem spremnosti sustava.
2. Pronaći odbijeni sigurnosni događaj.
3. Otvoriti klinike i osoblje.
4. Potvrditi da klinički editor nije dostupan.

### Tajnica

1. Pronaći sintetičkog pacijenta.
2. Naručiti termin bez konflikta pacijenta, liječnika ili prostorije.
3. Evidentirati dolazak i dovršiti administrativni prijem.
4. Potvrditi da klinički kontekst i sigurnosni audit nisu dostupni.

### Medicinska sestra

1. Provjeriti pripremu sintetičkog dolaska.
2. Evidentirati medical handoff i odstupanje bez donošenja odluke.
3. Pronaći laboratorijsku stavku.
4. Potvrditi da API ključevi nisu dostupni.

### Liječnik 1

1. Pronaći sljedećeg pacijenta Klinike A.
2. Otvoriti i urediti vlastitu skicu.
3. Pronaći dokument koji čeka liječnički pregled.
4. Potvrditi da Clinic B operativni termin nije prikazan kao vlastiti.

### Liječnik 2

1. Otvoriti vlastiti termin Klinike B.
2. Pronaći pregledani institution-wide dokument.
3. Potvrditi da skica Liječnika 1 nije uređiva.
4. Potvrditi da Clinic A termin nije prikazan kao vlastita obveza.

## Obrazac bodovanja

Za svaku osobu kopirati jedan red po zadatku:

| Persona | Zadatak | Bez pomoći | Vrijeme (s) | Pogrešni klikovi | Povratci | Zastajanje | Pomoć | Sigurnost 1–5 | Opažanje |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- |
|  |  |  |  |  |  |  |  |  |  |

Završna moderatorska bilješka:

- najčešća nejasnoća;
- radnja koju evaluator nije mogao pronaći;
- sadržaj koji je djelovao suvišno;
- sadržaj koji je nedostajao za sigurnu odluku;
- svaka uočena povreda role/scope granice kao trenutačni stop-signal.

## Završna odluka

Rezultat ostaje `NIJE PROVEDENO` dok stvarni predstavnici uloga ne završe
moderiranu sesiju i dok se njihovi rezultati zasebno ne pregledaju. Tehnički
gate može samo proglasiti kandidat `READY FOR HUMAN USABILITY REVIEW`.
