import { useMemo, useState } from "react";
import { api } from "../api/client";
import { ActionButton } from "../components/ActionButton";
import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { ApiKey } from "../types";
import { formatDateTime } from "../utils/date";

type ScopeInfo = { name: string; category: string; description: string };

export function ApiKeys() {
  const keys = useApi<ApiKey[]>("/auth/api-keys", []);
  const scopeCatalog = useApi<ScopeInfo[]>("/auth/api-key-scopes", []);
  const [name, setName] = useState("");
  const [scopes, setScopes] = useState<string[]>(["ai.appointments.create"]);
  const [rawKey, setRawKey] = useState("");
  const [error, setError] = useState("");

  const groupedScopes = useMemo(() => {
    return scopeCatalog.data.reduce<Record<string, ScopeInfo[]>>((groups, scope) => {
      groups[scope.category] = [...(groups[scope.category] ?? []), scope];
      return groups;
    }, {});
  }, [scopeCatalog.data]);
  const hasDangerousScopes = scopeCatalog.data.some((scope) => scope.category === "Dangerous scopes" && scopes.includes(scope.name));

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
      {rawKey && <div className="secret-once"><strong>Novi kljuc prikazan je samo sada:</strong><code>{rawKey}</code><button onClick={() => navigator.clipboard.writeText(rawKey)}>Kopiraj</button></div>}
      <div className="workflow-panel">
        <h2>Novi API kljuc</h2>
        <div className="inline-form">
          <input placeholder="Naziv kljuca" value={name} onChange={(event) => setName(event.target.value)} />
          <ActionButton
            className="primary"
            variant={hasDangerousScopes ? "danger" : "admin"}
            onClick={createKey}
            requiresConfirm
            confirmMessage={hasDangerousScopes ? "Odabrani su opasni scopeovi. Potvrditi kreiranje kljuca?" : "Potvrditi kreiranje API kljuca?"}
            helpTitle="Kreiraj API kljuc"
            help="API kljuc moze koristiti vanjski sustav ili AI agent. Dodijelite najmanji potreban skup scopeova."
          >
            Kreiraj
          </ActionButton>
        </div>
        {Object.entries(groupedScopes).map(([category, entries]) => (
          <div key={category} className={category === "Dangerous scopes" ? "danger-scope" : ""}>
            <h3>{category}</h3>
            <div className="scope-grid">
              {entries.map((scope) => (
                <label key={scope.name} title={scope.description}>
                  <input type="checkbox" checked={scopes.includes(scope.name)} onChange={(event) => setScopes(event.target.checked ? [...scopes, scope.name] : scopes.filter((item) => item !== scope.name))} />
                  {scope.name}
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
      <DataTable rows={keys.data} columns={[
        { header: "Naziv", render: (row) => row.name },
        { header: "Scopeovi", render: (row) => row.scopes.join(", ") },
        { header: "Aktivan", render: (row) => row.active ? "Da" : "Ne" },
        { header: "Zadnja upotreba", render: (row) => formatDateTime(row.last_used_at) },
        { header: "Radnja", render: (row) => row.active ? (
          <ActionButton
            variant="danger"
            onClick={() => deactivate(row)}
            requiresConfirm
            confirmMessage={`Deaktivirati API kljuc "${row.name}"?`}
            helpTitle="Deaktiviraj API kljuc"
            help="Odmah gasi pristup za ovaj kljuc. Postojece integracije koje ga koriste prestat ce raditi."
          >
            Deaktiviraj
          </ActionButton>
        ) : "-" }
      ]} />
    </section>
  );
}
