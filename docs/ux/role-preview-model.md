# Model demo prikaza uloga

## Svrha

Demo prikaz uloga služi isključivo za usporedbu sintetičkih radnih tokova.
Odabir uloge mora promijeniti stvarnu browser session i zatim koristiti
postojeći backend RBAC, članstva klinike, ustanovu, pružatelja i vlasništvo
objekta. Frontend skrivanje poveznica nije dokaz autorizacije.

## Baseline

Repozitorij već ima:

- revocable `UserSession` s httpOnly session kolačićem;
- session-bound CSRF token;
- `User → Role → Permission` autorizacijski lanac;
- `ClinicMembership`, `Clinic.institution_id` i aktivni `X-Clinic-Id` kontekst;
- `Provider.email`, kojim se liječnički korisnik povezuje s pružateljem;
- role-aware navigaciju s najviše pet ulaza prve razine;
- sintetički E2E skup s dvije klinike iste ustanove, dva liječnika, zajedničkim
  pacijentom, terminima, dokumentima, skicama i računom.

Postojeći `backend/app/demo/seed.py` ima administratora, tajnicu, sestru i samo
jednog liječnika. Svim demo korisnicima daje članstvo u obje demo klinike, pa
nije dovoljan za dokaz razlike između institution-wide kliničkog čitanja i
clinic-scoped operacija.

## Kanonske persone

| Ključ | Naziv | Uloga | Stručna kategorija | Zadani kontekst |
| --- | --- | --- | --- | --- |
| `admin` | Administrator | `admin` | administrativna | administrativni demo kontekst |
| `receptionist` | Tajnica | `receptionist` | administrativna | Klinika A |
| `nurse` | Medicinska sestra | `nurse` | `medical_staff` | Klinika A / Ustanova A |
| `physician_1` | Liječnik 1 | `physician` | `medical_staff` | Klinika A / Ustanova A / Provider A |
| `physician_2` | Liječnik 2 | `physician` | `medical_staff` | Klinika B / Ustanova A / Provider B |

Tajnica i medicinska sestra ostaju različiti stvarni korisnici. Liječnici
dijele istu ulogu i stručnu kategoriju, ali ne dijele zadanu kliniku, pružatelja,
raspored ni vlasništvo skice.

## Odabrani session model

Koristit će se kontrolirani endpoint za izdavanje nove demo browser session,
a ne impersonation header.

Razlozi:

1. svi kasniji zahtjevi prolaze neizmijenjeni postojeći auth dependency;
2. nema trajnog posebnog headera koji bi mogao procuriti kroz proxy ili klijent;
3. novi CSRF token prirodno je vezan uz novu session;
4. frontend ne dobiva lozinke ni identifikatore proizvoljnih korisnika;
5. opoziv stare session sprječava paralelno korištenje prethodnog konteksta.

Endpoint prihvaća samo pet kanonskih ključeva. Zahtijeva postojeću autoriziranu
demo evaluator/admin session i CSRF. U bazi pronalazi allowlisted sintetičkog
korisnika, opoziva kontrolnu session, izdaje novu session i auditira prijelaz.
Proizvoljan user ID, e-pošta ili uloga nikada nisu ulaz.

## Konfiguracijska granica

Funkcija smije biti dostupna samo kada istodobno vrijedi:

```text
APP_ENV != production
DEMO_MODE == true
REAL_DATA_ALLOWED == false
DEMO_PERSONA_SWITCHER_ENABLED == true
```

Produkcijska konfiguracija sa switcherom mora zaustaviti startup. Isključen
switcher vraća fail-closed odgovor i ne mijenja session.

## Čišćenje konteksta

Nakon uspješne promjene frontend mora:

1. prekinuti vlastite aktivne requestove promjenom session generacije;
2. ukloniti spremljenog korisnika, aktivnu kliniku i vremensku zonu;
3. prihvatiti novu session i ponovno dohvatiti klinike;
4. postaviti zadanu kliniku nove persone;
5. zatvoriti otvorene modalne prikaze promjenom rute i remountom aplikacije;
6. navigirati na početnu rutu te prikazati novu personu i kontekst.

Ovo ne uvodi globalni cache framework. Potpuni same-origin reload nakon
kontrolirane zamjene session namjerno je jednostavna sigurnosna granica.

## Inventura usporednog skupa

Postojeći E2E seed već dokazuje velik dio potrebnog skupa:

- Klinika A i Klinika B pripadaju Ustanovi A;
- zajednički pacijent povezan je s obje klinike;
- postoji pacijent samo u Klinici B te pacijenti Klinike A;
- postoje Provider A i Provider B, njihovi termini i aktivnosti;
- postoji pregledani klinički dokument s institution provenanceom;
- postoje vlastite i tuđe skice za provjeru autorstva;
- postoji račun Klinike A;
- postoje operativni i sigurnosni audit događaji.

Demo seed za ručnu evaluaciju mora taj model uskladiti stabilnim, jasno
sintetičkim personama i dodati nedostajući račun Klinike B te reprezentativne
zadatke tajnice i sestre. Ne smije sadržavati stvarne identitete ni podatke.

## Sigurnosne invarijante

- Administrator bez `medical_staff` kategorije ne dobiva institution clinical
  read samo zbog administrativne uloge.
- Tajnica ne dobiva klinički kontekst.
- Liječnik 2 ne dobiva operativne termine Klinike A kao vlastite.
- Institution-wide pregledani dokument može biti čitljiv liječnicima iste
  ustanove prema postojećoj politici.
- Liječnik 2 ne može uređivati skicu Liječnika 1.
- Promjena persone ne mijenja kanonske role/permission definicije.
- Svaka promjena persone stvara PHI-safe audit događaj
  `demo_persona_switched`.

## Trenutačne praznine nakon baselinea

- nema eksplicitne `DEMO_PERSONA_SWITCHER_ENABLED` postavke;
- nema kontroliranog endpointa za zamjenu demo session;
- `/api/public-config` ne objavljuje dostupnost switchera;
- AppShell nema jasno odvojen demo kontrolni element;
- demo seed nema dvije clinic-scoped liječničke persone;
- nema end-to-end dokaza promjene persone i čišćenja stale konteksta.

Ove praznine pripadaju sljedećim fazama. Baseline ne mijenja kliničko,
financijsko ni sigurnosno ponašanje.
