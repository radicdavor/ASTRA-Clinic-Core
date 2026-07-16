# Program 2 Phase I — Naplata, materijal i završetak dolaska

## Ishod

Potrošni materijal i stavke računa sada imaju izravno podrijetlo u `JourneyActivity`. Jedan fizički dolazak i dalje stvara jedan koordinirani račun.

## Potrošni materijal

- `StockMovement.related_activity_id` čuva aktivnost na kojoj je materijal korišten.
- Materijal se potvrđuje zasebno za svaku dovršenu aktivnost.
- LOT, serijski broj, nabavna cijena, korisnik i vrijeme ostaju u postojećem sljedivom zapisu zalihe.
- Aktivnost može biti izričito označena kao `not_applicable`.
- Dolazak prelazi naplati tek kada je materijal svih obveznih dovršenih aktivnosti razriješen.

Stari dolasci s jednim kliničkim susretom ostaju kompatibilni: njihova primarna aktivnost koristi se kao izvor materijala.

## Koordinirani račun

`Invoice.journey_id` označava jedan račun dolaska. Svaka automatski izvedena uslužna stavka sadrži:

- `activity_id`
- stabilni `source_key` oblika `activity:{id}:service`
- eksplicitnu uslugu i njezinu katalošku cijenu

Račun uključuje samo eksplicitno dovršene aktivnosti. Ne izvodi naplative postupke iz slobodnog teksta, izmijenjenog obrasca ili naknadno pristiglog patološkog nalaza. Ponovljeni zahtjev za pripremu već izdanog računa vraća postojeći račun i ne udvostručuje stavke.

## Završetak dolaska

Prije završetka moraju biti razriješeni klinički susret, sve obvezne aktivnosti, potrebni potpisani nalazi, materijal, račun i plaćanje ili dokumentirana odgoda. Patologija koja čeka nalaz ne označava pacijenta kao fizički prisutnog i sama po sebi ne blokira završetak istoga dana.

## Migracija i provjera

Migracija `0051_activity_billing` aditivno proširuje postojeće tablice i backfilla podrijetlo gdje ga je moguće jednoznačno povezati s postojećim terminom. Prazna PostgreSQL baza prolazi upgrade, downgrade jedne revizije i ponovni upgrade. Testovi potvrđuju dvije aktivnosti, zasebno razrješenje materijala, dvije aktivnosti na jednom računu i idempotentan ponovljeni zahtjev.
