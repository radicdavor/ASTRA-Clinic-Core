# ASTRA Clinic Core V2 workflowi

Ovaj dokument prati implementaciju `CODEX_MASTER_PROMPT_V2.md`.

## Sto je dodano

- Inventory, procurement i billing rute koriste permission actor model.
- API key / AI agent moze raditi samo ono sto mu je izricito dano kroz scope.
- Otpis, korekcija i transfer zalihe imaju zasebne dozvole.
- Kriticne create/update/delete radnje imaju strukturirani audit s before/after snapshotima.
- Narudzbenice imaju linije i podrzavaju djelomicno zaprimanje.
- Zaprimanje narudzbenice stvara `InventoryBatch` i `StockMovement`.
- `InventoryItem.current_stock` se tretira kao cache nad batch ledgerom.
- Dodan je endpoint `POST /api/inventory/recalculate-stock`.
- Racun se moze izraditi iz termina.
- Racuni imaju stavke i payment transakcije.
- Dodano je `FiscalizationProvider` sucelje i `NoopFiscalizationProvider` za kasniju fiskalizaciju.

## Primjeri

Kreiranje narudzbenice:

```bash
PO_ID=$(curl -s -X POST http://localhost:8000/api/purchase-orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"supplier_id":1,"status":"ordered","notes":"Narudzba potrosnog materijala"}' | jq -r .id)
```

Dodavanje stavke narudzbenice:

```bash
LINE_ID=$(curl -s -X POST http://localhost:8000/api/purchase-orders/$PO_ID/lines \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inventory_item_id":1,"quantity_ordered":5,"unit_price":12.50,"vat_rate":25}' | jq -r .id)
```

Djelomicno zaprimanje:

```bash
curl -X POST http://localhost:8000/api/purchase-orders/$PO_ID/receive \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lines":[{"purchase_order_line_id":'$LINE_ID',"quantity_received":2,"lot_number":"LOT-2026-001","expiration_date":"2027-07-01","location_id":1,"purchase_price":12.50}]}'
```

Popravak cachea zalihe:

```bash
curl -X POST http://localhost:8000/api/inventory/recalculate-stock \
  -H "Authorization: Bearer $TOKEN"
```

Nacrt racuna iz termina:

```bash
INVOICE_ID=$(curl -s -X POST http://localhost:8000/api/appointments/1/draft-invoice \
  -H "Authorization: Bearer $TOKEN" | jq -r .id)
```

Evidencija placanja:

```bash
curl -X POST http://localhost:8000/api/invoices/$INVOICE_ID/payments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":220,"method":"cash","reference":"BLAG-1"}'
```
