import { ReactNode } from "react";

export function WorkspaceSection({ title, children, actions }: { title: ReactNode; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="workflow-panel workspace-section">
      <div className="page-header">
        <h2>{title}</h2>
        {actions}
      </div>
      {children}
    </section>
  );
}
