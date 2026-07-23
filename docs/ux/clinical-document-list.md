# Klinički dokumenti — operativni popis

Status: Faza C

## Prije

- osam jednako važnih stupaca;
- tri odvojena statusa: klasifikacija, pregled i AI ekstrakcija;
- sirovi `Patient ID` kao filter i fallback u retku;
- nepotreban patient-search request pri svakom mountu;
- generičko prazno stanje i za zabranu pristupa;
- pretraga je slala request za svaku promjenu znaka.

## Poslije

- šest stupaca: Pacijent, Dokument, Datum, Tip, Status, Radnja;
- jedan operativni status s tekstom, ikonom i `aria-labelom`;
- patient autocomplete umjesto sirovog ID-a;
- jedan primarni CTA: `Otvori`, `Pregledaj` ili `Dovrši klasifikaciju`;
- izvor je napredni filter, a provenance i AI metadata ostaju na detail ruti;
- aktivni filtri vidljivi su kao chipovi i mogu se očistiti jednom radnjom;
- razlikuju se `Nema dokumenata`, filtrirano, `Nemate dozvolu` i nedostupnost;
- tekstualna pretraga ima 250 ms debounce, a `useApi` prekida zastarjeli request.

## Request ponašanje

Početno otvaranje sada šalje jedan request popisa. Patient autocomplete ne
šalje ništa prije dva znaka i ništa nakon odabira pacijenta. Više nema
`q=__no_patient__` requesta. Dokument detail i njegove podcjeline ne dohvaćaju
se dok korisnik ne otvori detail rutu.

List endpoint i dalje vraća postojeći kompatibilni DTO. U baseline demo skupu
dokument ruta je vratila `403`, pa nije dokazan payload dobitak za neprazan
skup i zato u ovoj fazi nije uveden novi javni endpoint ili projection.

## Statusni prioritet

1. odbijeno;
2. čeka klasifikaciju;
3. čeka liječnički pregled;
4. potpisano ili pregledano;
5. zamijenjeno;
6. izvor zaprimljen.

AI status je sekundaran samo kada njegova iznimka pomaže ljudskoj radnji. Ne
prikazuje se kao zaseban jednako naglašen stupac.

## Sigurnost i uloge

Frontend ne proširuje clinic/institution scope. Backend ostaje autoritativan.
`403` se prikazuje kao zabrana umjesto praznog rezultata. Nedostupan patient
objekt više se ne zamjenjuje sirovim internim ID-em. Detail ruta, source
document, signed-report i review pravila nisu promijenjeni.

## Responsive

Na 1024 px ostaje šest ključnih stupaca umjesto osam. Naslov može prikazati
izvor kao sekundarni red bez dodatnog stupca. Wrapper zadržava eventualni
unutarnji overflow, ali stranica ne dobiva dodatnu širinu zbog tehničkih
stupaca.

## Testovi

Komponentni testovi pokrivaju primarne stupce, jedan status i CTA, patient
autocomplete, odsutnost eager detail requesta i dummy patient requesta,
statusnu radnju, razlikovanje `403` i praznog rezultata te debounce/abort
ponašanje.
