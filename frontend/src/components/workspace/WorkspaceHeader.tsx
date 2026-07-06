import { ReactNode } from "react";

type WorkspaceHeaderProps = {
  title: ReactNode;
  subtitle?: ReactNode;
  badge?: ReactNode;
  actions?: ReactNode;
};

export function WorkspaceHeader({ title, subtitle, badge, actions }: WorkspaceHeaderProps) {
  return (
    <div className="workspace-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      <div className="workspace-header-side">
        {badge}
        {actions}
      </div>
    </div>
  );
}
