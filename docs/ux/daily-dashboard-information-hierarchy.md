# Dnevna ploča — vidljiv naručeni pregled ili pretraga

Status: ciljani inkrement informacijske hijerarhije

Datum: 23. 07. 2026.

## Korisnički zadatak

Tajnica, sestra/tehničar ili liječnik na zaslonu „Danas u poliklinici” mora bez
otvaranja pacijenta odgovoriti:

1. tko dolazi;
2. kada dolazi;
3. na koji je pregled ili pretragu naručen;
4. postoji li problem;
5. koja je sljedeća radnja.

## Prije

Naziv pregleda/pretrage nalazio se u unutarnjem retku aktivnosti. Kod kratkog
termina blok nema dovoljno visine da taj red uvijek bude vidljiv, pa su uz ime
pacijenta ostajali prvenstveno vrijeme i status.

## Poslije

- Uz ime i prezime uvijek se prikazuje naziv naručenog pregleda/pretrage.
- Ako jedan fizički dolazak ima više aktivnosti, prikazuju se svi jedinstveni
  nazivi redoslijedom aktivnosti, primjerice:
  `Prvi gastro pregled · Gastroskopija`.
- Unutarnji retci i dalje prikazuju vrijeme, uslugu i prostoriju kada visina
  bloka to dopušta.
- Dostupni naziv cijelog bloka i zasebni `aria-label` sadrže iste nazive
  usluga.
- Ne dodaje se nova radnja, status ni backend zahtjev.

## Sigurnost i regresije

- Prikazuju se samo aktivnosti koje je postojeći dashboard API već vratio
  ovlaštenom korisniku.
- Clinic/institution scope i filtri nisu promijenjeni.
- Jedan fizički dolazak ostaje jedan povezani pacijentov blok.
- Primarna radnja i sekundarni izbornik ostaju nepromijenjeni.
- Testovi pokrivaju pojedinačni i višestruki pregled/pretragu te dostupni
  tekst.
