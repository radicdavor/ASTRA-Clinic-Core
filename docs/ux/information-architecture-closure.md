# Informacijska arhitektura — završni dokaz kandidata

## Implementirano

- role-aware navigacija s najviše pet primarnih ulaza;
- fokusirani karton pacijenta i tijek dolaska;
- lazy klinički kontekst bez ponovnog nepotrebnog dohvata;
- operativne liste dokumenata, računa i evidencije s jednim statusom i jednom
  primarnom radnjom;
- clinic-local računanje dana;
- stvarne demo session persone i jasno označen topbar switcher;
- kanonski hrvatski pojmovi i sažeta safety microcopy.

## Odbijene promjene

- frontend-only promjena uloge, jer ne dokazuje autorizaciju;
- arbitrary user-ID impersonation;
- novi globalni state/cache framework;
- ručna permission matrica kao drugi izvor istine u runtimeu;
- eager dohvat detalja radi ukrasnih brojila;
- novi role-specific dashboard bez backend projekcije.

## Tehnička odluka

Puni backend, PostgreSQL, frontend, OpenAPI, Compose, Playwright, timezone i
persona/session gateovi provedeni su na sintetičkim podacima. Konačni tehnički
izvještaj nalazi se u
[role-ia-technical-closure.md](role-ia-technical-closure.md).

Odluka je **READY FOR HUMAN USABILITY REVIEW**.

Human usability nije proveden. Produkcija, stvarni podaci i vanjski provider
nisu autorizirani.
