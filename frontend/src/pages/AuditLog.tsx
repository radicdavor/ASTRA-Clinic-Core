import { DataTable } from "../components/DataTable";
import { useApi } from "../hooks/useApi";
import { AuditLog as AuditLogType } from "../types";

export function AuditLog() {
  const { data } = useApi<AuditLogType[]>("/api/audit-log", []);
  return (
    <section className="page">
      <h1>Audit log</h1>
      <DataTable rows={data} columns={[
        { header: "Vrijeme", render: (row) => new Date(row.created_at).toLocaleString("hr-HR") },
        { header: "Radnja", render: (row) => row.action },
        { header: "Entitet", render: (row) => row.entity_type },
        { header: "ID", render: (row) => row.entity_id ?? "-" },
        { header: "Sažetak", render: (row) => row.summary ?? "-" }
      ]} />
    </section>
  );
}
