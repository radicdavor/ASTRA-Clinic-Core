import { ReactNode, useState } from "react";

export type WorkspaceTab = { id: string; label: string; content: ReactNode };

export function WorkspaceTabs({ tabs }: { tabs: WorkspaceTab[] }) {
  const [active, setActive] = useState(tabs[0]?.id ?? "");
  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];

  return (
    <div className="workspace-tabs">
      <div className="workspace-tab-list">
        {tabs.map((tab) => (
          <button key={tab.id} className={tab.id === current?.id ? "active" : ""} onClick={() => setActive(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>
      <div>{current?.content}</div>
    </div>
  );
}
