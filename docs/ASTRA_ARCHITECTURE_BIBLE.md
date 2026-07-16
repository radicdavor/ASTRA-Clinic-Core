# ASTRA Architecture Bible

Vizija, principi i temeljna arhitektura platforme

Verzija: 1.0 (Founder's Edition)

## Predgovor

ASTRA nije nastala s ciljem da bude još jedan medicinski informacijski sustav.

Nastala je iz želje da liječniku vrati vrijeme za razmišljanje, pacijentu vrati osjećaj da ga netko vodi kroz liječenje, a administraciju pretvori iz prepreke u nevidljivu podršku.

ASTRA nije projekt o računalima.

ASTRA je projekt o ljudima.

Računala su samo alat.

## Misija

Izgraditi inteligentnu platformu koja omogućuje liječnicima, medicinskim sestrama i administraciji da rade jednostavnije, sigurnije i kvalitetnije, uz maksimalnu transparentnost i minimalno administrativno opterećenje.

## Vizija

ASTRA će postati operativni sustav moderne ambulante.

Ne samo elektronički karton.

Ne samo kalendar.

Ne samo program za račune.

Nego platforma koja razumije što se događa u ordinaciji.

## Temeljna filozofija

ASTRA nikada ne donosi medicinsku odluku umjesto liječnika.

ASTRA:

- organizira
- upozorava
- predlaže
- provjerava
- dokumentira
- automatizira

Liječnik odlučuje.

Uvijek.

## Temeljna načela

### 1. Čovjek je iznad softvera

Softver postoji radi korisnika.

Nikada obrnuto.

### 2. Jedan izvor istine

Svaki podatak postoji samo jednom.

Sve ostalo su prikazi tog podatka.

### 3. Jedan jezik

Cijela platforma koristi iste pojmove.

Pacijent znači isto u svakom modulu.

Termin znači isto.

Račun znači isto.

Audit znači isto.

### 4. Modularnost

Svaki modul može se dodati ili ukloniti bez mijenjanja jezgre.

Clinic Core mora ostati stabilan.

### 5. API First

Sve što radi korisnik mora moći napraviti i API.

Ne obrnuto.

### 6. AI je suradnik

AI nije administrator.

AI nije liječnik.

AI nije odgovoran.

AI je pomoćnik.

### 7. Audit svega važnog

Sve bitne promjene moraju biti moguće rekonstruirati.

Tko.

Što.

Kada.

Zašto.

## Što ASTRA nije

ASTRA nije:

- Word dokument
- tablica
- kalendar
- chatbot
- samo EMR
- samo ERP

ASTRA je operativni sustav klinike.

## Temeljni objekti

Platforma se temelji na nekoliko osnovnih objekata.

### Pacijent

Središnja osoba sustava.

Pacijent nije broj.

Svaki drugi objekt postoji zbog pacijenta.

### Termin

Događaj u vremenu.

Povezuje:

- pacijenta
- liječnika
- sobu
- uslugu

### Usluga

Definira:

- trajanje
- cijenu
- potrebne materijale
- workflow

### Epizoda liječenja

Najvažniji budući objekt.

Jedan pacijent može imati više epizoda.

Svaka epizoda povezuje:

- termine
- nalaze
- terapije
- dokumente
- račune

### Inventar

Predstavlja fizičke resurse.

Sve promjene moraju biti auditirane.

### Račun

Financijski prikaz izvršene usluge.

### Audit

Povijest sustava.

Audit se ne briše.

### AI Agent

Kontrolirani korisnik sustava.

Ima najmanje moguće ovlasti.

## Životni ciklus pacijenta

1. Pretraga postojećeg pacijenta.
2. Ako ne postoji: Novi pacijent.
3. Termin.
4. Dolazak.
5. Obrada.
6. Završetak termina.
7. Potrošnja materijala.
8. Nalaz.
9. Račun.
10. Kontrola.

## Pravila dizajna

Svaka akcija pripada jednoj kategoriji.

### Informacija

Ne mijenja podatke.

### Novi objekt

Stvara podatak.

### Izmjena

Mijenja postojeći podatak.

### Kritična akcija

Nepovratna promjena.

Uvijek:

- upozorenje
- potvrda
- audit

### AI akcija

Uvijek označena.

Korisnik zna da je prijedlog došao od AI-ja.

## Kontekstualna pomoć

Svaki važan ekran mora imati ugrađeno objašnjenje.

Ne PDF.

Ne priručnik.

Pomoć je dio sučelja.

Korisnik ne smije tražiti dokumentaciju.

## Identitet pacijenta

Pacijent se identificira pomoću:

- imena
- prezimena
- datuma rođenja
- OIB-a (ako postoji)
- telefona
- e-maila

Nikada se termin ne smije napraviti za "nepoznatog" pacijenta.

## Sigurnost

Default stanje je sigurnost.

Realni podaci su zabranjeni dok projekt nije odobren za produkciju.

Demo uvijek mora biti jasno označen.

## AI filozofija

AI nikada ne smije:

- skrivati nesigurnost
- izmišljati podatke
- donositi medicinske odluke
- mijenjati kritične podatke bez dozvole

AI smije:

- predlagati
- organizirati
- podsjećati
- analizirati
- ubrzavati rad

## Medicinski moduli

Clinic Core mora ostati mali.

Medicina dolazi kroz module.

Primjeri:

- Gastroenterologija
- Endoskopija
- Estetska medicina
- Dermatologija
- Debljina i metabolička medicina
- Putničke bolesti

Svi moduli koriste isti jezik platforme.

## Kvaliteta

Prije svake nove funkcije postaviti pitanje:

> Čini li ovo sustav jednostavnijim ili samo većim?

Ako ga čini samo većim, funkcija ne ulazi u sustav.

## Razvojna filozofija

ASTRA se razvija u tri ciklusa.

### 1. Izgradnja

Dodavanje novih mogućnosti.

### 2. Stabilizacija

Testiranje.

Ispravljanje.

Poliranje.

### 3. Korištenje

Promatranje stvarnih korisnika.

Njihovo ponašanje određuje sljedeći razvoj.

Ne pretpostavke.

## Završna misao

ASTRA neće biti uspješna zato što ima najviše funkcija.

Bit će uspješna ako liječnik nakon radnog dana kaže:

> Danas sam više vremena proveo razmišljajući o pacijentima nego o programu.

Ako ASTRA postigne taj cilj, ispunila je svoju svrhu.

## Pravilo koordiniranog kliničkog dolaska

Jedan fizički dolazak ostaje jedan `PatientJourney`, bez obzira na broj pregleda ili postupaka. Svaki pregled ili postupak je zaseban `JourneyActivity` sa svojim vremenom, prostorijom, liječnikom, pripremom, obrascem, nalazom, materijalom i uzorcima. Zajednički prijem, račun i plaćanje ostaju na razini dolaska. Potpisani klinički sadržaj je nepromjenjiv; ispravak uvijek stvara novu verziju.
