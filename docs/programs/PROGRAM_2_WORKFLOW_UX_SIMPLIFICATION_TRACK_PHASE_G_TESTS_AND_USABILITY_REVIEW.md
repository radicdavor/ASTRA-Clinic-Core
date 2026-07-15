# Phase G — Testovi i usability review

Automatski su provjereni role-aware navigacija, najviše četiri primarne stavke prije izbornika Više, uklonjena lažna pretraga, četiri dashboard stupca, zatvoreni dodatni filtri, zabrana POST mutacije pri navigaciji, jedna aktivna faza te klinički kontekst i dokumenti dostupni jednim otvaranjem.

Frontend rezultat nakon implementacije: 5 testnih datoteka i 29 testova prolaze, uz 3 Program 2 contract testa. Dodatni regression test potvrđuje da role-aware navigacija radi i za postojeću prijavu nastalu prije spremanja novog zapisa korisničke uloge.

Puni backend regression suite: 477 testova prolazi, a 9 PostgreSQL testova očekivano je preskočeno bez `TEST_DATABASE_URL`. Zasebna prazna PostgreSQL baza uspješno prolazi cijeli Alembic upgrade do `0046`, downgrade na `0045` i ponovni upgrade do `0046`.

Demo seed sadrži 12 stanja od čekanja dokumenata do plaćanja i završetka. Lokalni backend i sučelje pokrenuti su na `http://127.0.0.1:8000` i `http://127.0.0.1:4178`; health, administratorska i liječnička demo prijava, dnevni API s 12 dolazaka i dohvat kanonskog tijeka prolaze.

Vizualno-klikačka provjera provedena je 15. srpnja 2026. na standardnom i 1024 px prikazu. Provjereni su role-aware navigacija, liječnički scope, dodatni filtri, jedna radnja po retku, fokusirana faza, prebacivanje faza, klinički kontekst, izvorni dokumenti i konzola preglednika. Tijekom provjere pronađeni su i ispravljeni: pad `/api/providers` na legacy demo `.local` adresi, nedostajući naziv stare usluge u zaglavlju tijeka te prelijevanje četvrtog dashboard stupca na 1024 px. Ponovna provjera prošla je bez konzolnih grešaka.
