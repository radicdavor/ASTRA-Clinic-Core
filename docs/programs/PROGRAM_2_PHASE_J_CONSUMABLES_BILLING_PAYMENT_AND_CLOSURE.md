# Program 2 — Phase J: potrošni materijal, račun, plaćanje i zatvaranje

Potrošni materijal potvrđuje se izričito nakon postupka. Stvarna potrošnja koristi postojeći FEFO servis i `StockMovement`; putovanje, serija, serijski broj i jedinični trošak čuvaju provenijenciju. Oznaka „nije primjenjivo” također je izričita ljudska radnja.

Račun se izvodi iz postojeće usluge termina i izdaje postojećim billing servisom. Više `PaymentTransaction` zapisa omogućuje djelomično i mješovito plaćanje. Odgoda zahtijeva razlog. Kanonski state machine odbija zatvaranje s nerazriješenim susretom, materijalom, računom, plaćanjem ili blokatorom.

Puni iznos bira se izravno gumbom načina plaćanja; djelomična uplata ostaje dostupna kao sekundarna mogućnost. Nakon izričito evidentirane pune uplate ili odgode, tijek se automatski zatvara samo ako isti korisnik ima `journey.transition` ovlast i svi postojeći closure guardovi prolaze. Time se uklanja zaseban administrativni klik bez zaobilaženja RBAC-a ili sigurnosnih uvjeta.

Ne postoji automatsko fakturiranje nepotvrđenog materijala. Produkcijska fiskalizacija i platni terminal nisu uključeni; postojeći noop provider ostaje jasno označena integracijska granica.
