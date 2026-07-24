# Navigacija prema ulozi

## Cilj

Navigacija usmjerava korisnika na njegov svakodnevni posao, bez izlaganja cijelog
registra aplikacijskih stranica. Ovo je informacijska hijerarhija, a ne
autorizacijski mehanizam. Backend RBAC i aktivni kontekst klinike ostaju
mjerodavni za svaki zahtjev.

## Prije

- četiri ista primarna ulaza bila su filtrirana širokim popisima uloga;
- gotovo sve ostale funkcije nalazile su se pod jednim izbornikom `Više`;
- administrator je pod `Više` dobivao šest nevezanih skupina;
- zaglavlje je razlikovalo samo `Administratorski prikaz` i `Operativni prikaz`;
- promjena klinike odmah je ponovno učitavala stranicu, bez upozorenja o
  otvorenim skicama.

Takav raspored prisiljavao je korisnika da poznaje strukturu sustava umjesto
vlastitog radnog zadatka.

## Poslije

Svaka ljudska uloga ima najviše pet ulaza prve razine. Grupirani ulaz ima samo
jednu dodatnu razinu i nazvan je prema poslu koji sadrži.

| Uloga | Prva razina |
| --- | --- |
| Administrator | Danas; Operacije; Nabava i financije; Administracija; Sigurnost |
| Liječnik | Danas; Pacijenti; Klinički rad; Zadaci; Naručivanje |
| Medicinska sestra/tehničar | Danas; Pacijenti; Zadaci; Klinička podrška; Raspored i zalihe |
| Tajnica/administratorica | Danas; Pacijenti; Naručivanje; Prijem; Dokumenti |
| Naplata | Danas; Pacijenti; Računi |
| Voditelj zaliha | Inventar; Dobavljači; Narudžbenice |
| Pregledavatelj dokumenata | Danas; Pacijenti; Dokumenti |

Demo stranice prikazuju se samo administratoru u demo okruženju i ostaju unutar
skupine `Administracija`. Ne stvaraju šesti primarni ulaz.

## Zaglavlje i kontekst klinike

Zaglavlje prikazuje:

- ulogu jasnim hrvatskim nazivom;
- aktivnu kliniku;
- upozorenje kada korisnik mora odabrati kliniku.

Promjena aktivne klinike prvo otvara kontrolirani dijalog. Dijalog jasno navodi
novu kliniku i upozorava korisnika da spremi otvorene skice. Tek izričitom
potvrdom mijenjaju se lokalni identifikator klinike i vremenska zona te se ista
smislena ruta ponovno učitava u novom kontekstu.

Podatak o ustanovi nije dodan u korisničko sučelje jer ga postojeći
`/auth/me/clinics` ugovor ne vraća. Naziv ustanove ne smije se nagađati iz naziva
klinike. Može se prikazati tek nakon zasebnog, autoriziranog proširenja ugovora.

## Sigurnosne granice

- Skrivena poveznica nije sigurnosna kontrola.
- Postojeće rute ostaju registrirane kako bi duboke poveznice i radni tijekovi
  nastavili raditi.
- Backend `require_permission` i `require_active_clinic` ostaju jedina
  autorizacijska granica.
- Ova faza ne mijenja RBAC, session/CSRF, audit, institution scope ni klinička
  pravila.
- Uloga s nepoznatim nazivom dobiva samo minimalni ulaz `Danas`; time frontend
  ne pretpostavlja šire ovlasti.

## Provjere

Frontend testovi provjeravaju:

- najviše pet primarnih ulaza za svaku ljudsku ulogu;
- točne ulaze za recepciju, liječnika, sestru, naplatu, zalihe i pregled
  dokumenata;
- odsutnost administrativnih i kliničkih odluka u recepcijskoj navigaciji;
- samo dvije razine grupirane navigacije;
- jasan hrvatski naziv uloge u zaglavlju;
- kontrolirani dijalog prije promjene klinike;
- da odustajanje ne mijenja aktivni kontekst klinike.
