# Current security model

Ovo je kanonski sažetak trenutačnog sigurnosnog modela. Detaljne odluke nalaze
se u ADR-ovima i sigurnosnim matricama.

## Identitet i session

Browser koristi opozivu httpOnly `UserSession` i session-bound CSRF kolačić
čiji se hash provjerava protiv iste session. Produkcijski ugovor je jedan HTTPS origin.
Bearer i tenant-scoped API key ostaju odvojeni ne-browser tokovi.

## Autorizacija i scope

Backend `Role → Permission` provjera je autoritativna. Clinic operacije i
billing zahtijevaju aktivnu kliniku. Medicinski djelatnik s eksplicitnim
pravom može čitati dopušten klinički zapis unutar ustanove; to ne proširuje
clinic-scoped operacije. Globalni administrator bez medicinske kategorije ne
dobiva PHI samo zbog administratorske uloge.

## Klinički integritet

`ClinicalDocument.institution_id` i clinic provenance određuju read scope.
Nerazrijeđeni legacy provenance odbija se po defaultu. Skicu uređuje vlasnik,
potpisani nalaz je nepromjenjiv, a addendum se veže uz točnu verziju izvora.
Originalni dokument ostaje izvor istine.

## Audit

Važne mutacije i osjetljivi pristupi auditiraju se PHI-safe projekcijom.
Nevaljana browser session zapisuje se zasebnom kratkom transakcijom, bez
commita poslovne transakcije i bez pohrane tokena, kolačića ili kliničkog teksta.

## Demo persona preview

Preview izdaje novu stvarnu session allowlisted sintetičkog korisnika. Zahtijeva
autoriziranu demo controller session i CSRF te je dostupan samo kada su demo
sigurnosni uvjeti istodobno zadovoljeni. Produkcija s uključenim previewom ne
smije pokrenuti aplikaciju.
