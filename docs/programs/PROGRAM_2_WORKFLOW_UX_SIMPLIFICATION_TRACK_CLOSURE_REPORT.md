# Program 2 Workflow UX Simplification Track — closure report

Navigacija je reorganizirana oko korisničkih zadataka, dnevna ploča naglašava trenutačno stanje i sljedeću radnju, a radni prostor samo aktualnu fazu. Pozadinske informacije dostupne su progresivnim otkrivanjem. Administrativni alati ostaju dostupni prema ulozi.

Nijedna postojeća jezgrena funkcija nije uklonjena. Backend workflow model nije zamijenjen. Nije dodano autonomno kliničko ponašanje, dijagnoza, terapijska preporuka ili trijaža.

## Architecture Bible compliance

- **Čovjek iznad softvera:** ekran prikazuje jednu sljedeću radnju i uklanja nepotrebno administrativno traženje.
- **Jedan izvor istine i API First:** postojeći PatientJourney i postojeće API rute ostaju mjerodavni; frontend ne uvodi paralelni workflow.
- **Jedan jezik:** korisnički izrazi standardizirani su na Dolazak, Prijem, Pregled, Naplata i Evidencija aktivnosti.
- **AI je suradnik:** AI sadržaj ostaje označen kao prijedlog, source-linked i pod ljudskim pregledom.
- **Sigurnost i audit:** navigacijska vidljivost ne zamjenjuje backend RBAC, a nijedna auditirana mutacija nije premještena u skriveni klik.

- prije: 20 stalnih + 2 demo top-level stavke
- poslije: 2–4 primarne stavke po ulozi i grupirani izbornik Više
- sve postojeće frontend rute ostaju registrirane
- dashboard: četiri stupca, sažeti filtri, bez navigacijskih mutacija
- workspace: jedna aktivna faza, jedna sljedeća radnja, sekundarni klinički kontekst

Implementacija je na holdu **STOP AND EVALUATE WITH USERS**. Formalno zatvaranje nije proglašeno dok korisnik ne završi vizualnu evaluaciju sintetičkih scenarija. Daljnji razvoj zahtijeva izričitu autorizaciju.
