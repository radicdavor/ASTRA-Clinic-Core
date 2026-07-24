# ASTRA Clinic Core

ASTRA je modularna operativna jezgra poliklinike. Povezuje pacijenta,
naručivanje, jedan fizički dolazak, kliničke aktivnosti, dokumente, materijal,
račun, plaćanje i audit bez autonomnog donošenja medicinskih odluka.

## Trenutačni status

Projekt je lokalni, kontrolirani **synthetic/demo** sustav. Nije autoriziran za
stvarne podatke pacijenata, produkciju ili rad klinike. Kanonsko stanje:

- [proizvod](docs/CURRENT_PRODUCT_STATE.md)
- [arhitektura](docs/CURRENT_ARCHITECTURE.md)
- [sigurnost](docs/CURRENT_SECURITY_MODEL.md)
- [operativna ograničenja](docs/CURRENT_OPERATIONAL_LIMITATIONS.md)

## Glavne mogućnosti

- globalni identitet pacijenta uz clinic/institution scope;
- termini i dnevna ploča s jednim blokom po fizičkom dolasku;
- više aktivnosti, prostorija i liječnika unutar istog dolaska;
- prijem, priprema, klinički obrasci i potpisani nalazi;
- izvorni dokumenti, pregled i source-linked izvedeni sažeci;
- potrošni materijal, račun, plaćanje i audit;
- role-aware navigacija i demo-only pregled pet sintetičkih persona.

## Lokalno pokretanje

```bash
docker compose up -d --build
docker compose exec backend python -m app.demo.seed
```

Web sučelje: `http://localhost:5173`

Demo seed ispisuje lokalne razvojne podatke za prijavu. Nemoj ih koristiti u
drugom okruženju niti unositi stvarne podatke.

## Sigurnosna ograničenja

- Backend RBAC, aktivna klinika i institution provenance autoritativni su;
  skrivena frontend radnja nije sigurnosna kontrola.
- Browser koristi httpOnly session, session-bound CSRF i same-origin ugovor.
- Potpisani nalazi su nepromjenjivi; ispravak je nova verzija/addendum.
- Originalni dokument je izvor istine; OCR i AI sadržaj su izvedeni i traže
  ljudski pregled.
- Demo persona switcher radi samo uz eksplicitnu sigurnu lokalnu konfiguraciju
  i nikada ne prihvaća proizvoljan user ID.

## Testiranje

```bash
python scripts/run_test_gate.py fast
python scripts/run_test_gate.py integration
python scripts/run_test_gate.py full

cd frontend
npm ci
npm run typecheck
npm test -- --run
npm run smoke
npm run build
```

DB-backed Playwright i PostgreSQL integracija zahtijevaju pripremljeno
sintetičko testno okruženje. Ne predstavljati preskočen test kao prolaz.

## Dokumentacija

Početna točka je [docs/index.md](docs/index.md). Arhitekturni autoritet je
[ASTRA Architecture Bible](docs/ASTRA_ARCHITECTURE_BIBLE.md). ADR-ovi
objašnjavaju odluke; phase i closure dokumenti povijesni su dokaz, a ne
trenutačni izvor istine.
