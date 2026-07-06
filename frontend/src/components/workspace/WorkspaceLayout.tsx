import { ReactNode } from "react";

export function WorkspaceLayout({ children }: { children: ReactNode }) {
  return <section className="page workspace-layout">{children}</section>;
}
