import { useState } from "react";
import { api } from "../api/client";
import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { ApiKey } from "../types";

const commonScopes = ["ai.patients.create", "ai.appointments.create", "ai.free_slots.read", "patients.read", "appointments.read"];

export function ApiKeys() {
  const keys = useApi<ApiKey[]>("/auth/api-keys", []);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>(["ai.appointments.create"]);
  const [rawKey, setRawKey] = useState("");
  const [error, setError] = useState("");

  async function createKey() {
    setError("");
    try {
      const created = await api<ApiKey & { key: string }>("/auth/api-keys", { method: "POST", body: JSON.stringify({ name, scopes }) });
      setRawKey(created.key);
      keys.setData([created, ...keys.data]);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Greska kod API kljuca");
    }
  }

  async function deactivate(row: ApiKey) {
    const updated = await api<ApiKey>(`/auth/api-keys/${row.id}/deactivate`, { method: "PATCH" });
    keys.setData(keys.data.map((key) => (key.id === updated.id ? updated : key)));
  }

  return (
    <section className="page">
      <div className="page-header"><h1>API kljucevi</h1><p>Koristite najmanji potreban skup scopeova za AI agente i vanjske sustave.</p></div>
      {error && <p className="form-error">{error}</p>}
      {rawKey && <div className="secret-once"><strong>Novi kljuc prikazan je samo sada:</strong><code>{rawKey}</code></div>}
      <div className="workflow-panel">
        <h2>Novi API kljuc</h2>
        <div className="inline-form">
          <input placeholder="Naziv kljuca" value={name} onChange={(event) => setName(event.target.value)} />
          <button className="primary" onClick={createKey}>Kreiraj</button>
        </div>
        <div className="scope-grid">
          {commonScopes.map((scope) => (
            <label key={scope}>
              <input type="checkbox" checked={scopes.includes(scope)} onChange={(event) => setScopes(event.target.checked ? [...scopes, scope] : scopes.filter((item) => item !== scope))} />
              {scope}
            </label>
          ))}
        </div>
      </div>
      <DataTable rows={keys.data} columns={[
        { header: "Naziv", render: (row) => row.name },
        { header: "Scopeovi", render: (row) => row.scopes.join(", ") },
        { header: "Aktivan", render: (row) => row.active ? "Da" : "Ne" },
        { header: "Zadnja upotreba", render: (row) => row.last_used_at ?? "-" },
        { header: "Radnja", render: (row) => row.active ? <button onClick={() => deactivate(row)}>Deaktiviraj</button> : "-" }
      ]} />
    </section>
  );
}
