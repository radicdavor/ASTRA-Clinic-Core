# Program 2 Workflow UX Simplification — status matrix

> Historical record. It is not the current product-state source; see the canonical documents in `docs/`.

| Područje | Status | Dokaz / ograničenje |
| --- | --- | --- |
| IA audit | Dovršeno | Phase A |
| Role-aware navigacija | Dovršeno | AppShell testovi |
| Najviše 5 primarnih stavki | Dovršeno | 2–4 stavke po ulozi + Više |
| Rute i deep linkovi | Očuvano | AppRoutes nije brisan; focus alias-i |
| Dashboard 4 stupca | Dovršeno | interaktivni test |
| Filtri i bez skrivenih mutacija | Dovršeno | regression testovi |
| Jedna aktivna faza i sljedeća radnja | Dovršeno | workspace testovi |
| Klinički kontekst i AI sažetak | Dovršeno | details/tabs i ograničene sekcije |
| Fokusirani TypeScript tipovi | Dovršeno | `types/program2.ts` |
| Typecheck / test / build | Dovršeno | 29 testova + 3 contract testa, typecheck, build i smoke prolaze |
| Backend regression suite | Dovršeno | 477 testova prolazi; 9 PostgreSQL testova preskočeno bez `TEST_DATABASE_URL` |
| Alembic prazna baza | Dovršeno | upgrade do `0046`, downgrade na `0045` i ponovni upgrade prolaze |
| Lokalni startup | Dovršeno | backend health, frontend 4178, demo login |
| Vizualni browser review | Dovršeno | administrator i liječnik; standardni i 1024 px prikaz; bez konzolnih grešaka |
| Formalno zatvaranje | Dovršeno | track zatvoren; `STOP AND HOLD` vraćen |
