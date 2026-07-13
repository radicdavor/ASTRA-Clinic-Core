# Program 2 — Phase J: potrošni materijal, račun, plaćanje i zatvaranje

Potrošni materijal potvrđuje se izričito nakon postupka. Stvarna potrošnja koristi postojeći FEFO servis i `StockMovement`; putovanje, serija, serijski broj i jedinični trošak čuvaju provenijenciju. Oznaka „nije primjenjivo” također je izričita ljudska radnja.

Račun se izvodi iz postojeće usluge termina i izdaje postojećim billing servisom. Više `PaymentTransaction` zapisa omogućuje djelomično i mješovito plaćanje. Odgoda zahtijeva razlog. Kanonski state machine odbija zatvaranje s nerazriješenim susretom, materijalom, računom, plaćanjem ili blokatorom.

Ne postoji automatsko fakturiranje nepotvrđenog materijala. Produkcijska fiskalizacija i platni terminal nisu uključeni; postojeći noop provider ostaje jasno označena integracijska granica.
