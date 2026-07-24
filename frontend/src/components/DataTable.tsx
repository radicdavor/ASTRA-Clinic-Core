import { ReactNode } from "react";

type Column<T> = { header: string; render: (row: T) => ReactNode };

export function DataTable<T extends { id: number }>({ rows, columns, empty = "Nema podataka", ariaLabel }: { rows: T[]; columns: Column<T>[]; empty?: string; ariaLabel?: string }) {
  return (
    <div className="table-wrap">
      <table aria-label={ariaLabel}>
        <thead>
          <tr>{columns.map((column) => <th key={column.header}>{column.header}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>{columns.map((column) => <td key={column.header}>{column.render(row)}</td>)}</tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="empty">{empty}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
