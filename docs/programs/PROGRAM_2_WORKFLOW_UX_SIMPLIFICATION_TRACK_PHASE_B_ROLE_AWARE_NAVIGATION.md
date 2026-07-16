# Phase B — Role-aware navigacija

> Historical record. It is not the current product-state source; see the canonical documents in `docs/`.

Glavna navigacija sada prikazuje zadatke **Danas**, **Pacijenti**, **Naručivanje** i, liječniku ili administratoru, **Znanje**. Sekundarne rute ostaju pod **Više**, grupirane u Kliničke alate, Organizaciju rada, Nabavu i zalihe, Financije, Administraciju i Demo.

Recepcija ima 3 primarne stavke, liječnik 4, medicinska sestra/tehničar 3, naplata 2, a administrator 4. Prazne i nedopuštene skupine se ne prikazuju. Prijavljena uloga služi samo prezentaciji; backend RBAC ostaje autoritativan. Sve izvorne rute iz `AppRoutes.tsx` ostaju dostupne kao izravne poveznice.

Nefunkcionalna globalna pretraga uklonjena je iz topbara. Nova command palette nije dodana jer nije potrebna za ovaj uski track.
