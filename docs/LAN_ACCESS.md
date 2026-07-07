# ASTRA Clinic Core - lokalni LAN pristup

Ova uputa sluzi za lokalni demo/pilot pristup s drugog uredaja u istoj mrezi.

Ne unositi stvarne podatke pacijenata.

## 1. Pokretanje

Na racunalu na kojem se izvrsava ASTRA pokrenite:

```bash
docker compose up --build
```

Docker Compose objavljuje:

- frontend na svim mreznim suceljima: `0.0.0.0:5173`
- backend API na svim mreznim suceljima: `0.0.0.0:8000`
- PostgreSQL samo lokalno na racunalu: `127.0.0.1:5432`

Time drugi uredaji u LAN-u mogu otvoriti aplikaciju i API, ali baza nije izravno izlozena mrezi.

## 2. Pronadite LAN IP adresu racunala

PowerShell:

```powershell
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -match '^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)' } |
  Select-Object IPAddress,InterfaceAlias
```

Primjer rezultata:

```text
192.168.1.42
```

## 3. Otvaranje s drugog uredaja

Na drugom uredaju u istoj mrezi otvorite:

```text
http://192.168.1.42:5173
```

API dokumentacija je na:

```text
http://192.168.1.42:8000/docs
```

Zamijenite `192.168.1.42` stvarnom IP adresom racunala.

## 4. Firewall

Ako se stranica ne otvara s drugog uredaja, u Windows firewallu dopustite dolazni promet za:

- TCP `5173`
- TCP `8000`

Za zatvoreni lokalni demo preporucuje se dopustiti promet samo na privatnoj mrezi.

## 5. Frontend API adresa

`VITE_API_BASE_URL` treba ostati prazan za LAN demo.

Tada frontend automatski koristi isti hostname na kojem je otvoren u browseru i port `8000`.

Primjer:

- korisnik otvori `http://192.168.1.42:5173`
- frontend zove API na `http://192.168.1.42:8000`

Ne postavljati `VITE_API_BASE_URL=http://localhost:8000` ako aplikaciji pristupate s drugog uredaja, jer bi tada browser na drugom uredaju trazio API na vlastitom `localhostu`.
