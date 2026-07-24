# Zajednički obrazac operativnog popisa

Status: Faza B — zajedničke UI primitive

Commit polazište: `0941c0d`

## Prije i poslije

Prije su tri popisa zasebno kombinirala zaglavlja, filtre, statuse, prazna
stanja i radnje. Tehnički statusi nisu imali jasnu hijerarhiju, a detalj nije
imao konzistentno dostupno ponašanje.

Poslije se koriste male, kompozicijske primitive:

- `ListPageHeader`
- `ListFilterBar`
- `OperationalRow`
- `StatusSummary`
- `RowPrimaryAction`
- `RowMoreMenu`
- `ProgressiveDetailPanel`
- `EmptyState`

To nije jedna generička tablica s konfiguracijskim propovima. Poslovni ekran i
dalje sam određuje svoje stupce, status i ovlasti.

## Pravila

1. Jedan `h1`, kratka svrha i najviše jedna globalna primarna radnja.
2. Stalno su vidljivi samo najvažniji filtri; napredni su sklopljeni.
3. Red ima jedan status koji sadrži tekst, ikonu i pristupačan opis.
4. Red ima jednu stalno vidljivu primarnu radnju.
5. Sekundarne radnje su u meniju s tri točke.
6. Tehnički detalj učitava se tek nakon otvaranja drawera ili route detaila.
7. Prazno, filtrirano, zabranjeno i nedostupno stanje imaju različite poruke.
8. Frontend vidljivost nije autorizacija; backend ostaje autoritativan.

## List/detail granica

Dokument ostaje zasebna detail ruta jer ima izvor, pregled i klinički kontekst.
Račun može koristiti drawer ako list projekcija ne mora sadržavati stavke i
uplate. Audit koristi read-only drawer nad PHI-safe DTO granicom.

`ProgressiveDetailPanel` osigurava:

- `role="dialog"` i naslov;
- focus trap;
- zatvaranje tipkom Escape;
- povrat fokusa na element koji je otvorio detalj;
- vlastiti loading i error state s `aria-live`;
- čišćenje podataka ostaje odgovornost poslovnog ekrana pri zatvaranju ili
  promjeni scopea.

## Responsive

Na 1024 px identitet, status i radnja ostaju u jednom operativnom retku bez
horizontalnog scrolla cijele stranice. Na uskom zaslonu status prelazi u drugi
red, a primarna i dodatne radnje ostaju uz identitet.

## Odbijene promjene

- nije uveden novi UI framework;
- nije uveden globalni state ili cache;
- nije promijenjen API ili autorizacijski scope;
- nije stvoren univerzalni renderer poslovnih tablica;
- detalji nisu samo skriveni CSS-om;
- boja nije jedini indikator statusa.

## Testni dokaz

Komponentni testovi provjeravaju tekstualni status, jednu primarnu radnju,
tipkovnički meni, sklopljene napredne filtre, četiri različita empty/error
stanja te focus trap, Escape i povrat fokusa u detail draweru.
