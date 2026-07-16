# Phase C — Fokus dnevne ploče

> Historical record. It is not the current product-state source; see the canonical documents in `docs/`.

Dnevna ploča zadržava četiri stupca: vrijeme i pacijent, usluga i liječnik, trenutačno stanje i sljedeća radnja. Sažetak prikazuje samo dolaske, aktivne i dolaske s problemom.

Zadane kontrole su datum, pretraga pacijenta, problem i liječnik kada opseg to dopušta. Klinika, prostorija, usluga i faza nalaze se pod **Dodatni filtri**, uz broj aktivnih dodatnih filtara i **Očisti filtre**.

Klik na pacijenta ili operativnu radnju sada samo otvara odgovarajuću fazu. Uklonjene su skrivene mutacije koje su prije navigacije pokretale prijem ili izrađivale račun. Prikazuje se prvi problem i sažetak broja dodatnih problema.
