import { KeyboardEvent, ReactNode, useRef, useState } from "react";

export type WorkspaceTab = { id: string; label: string; content: ReactNode };

export function WorkspaceTabs({ tabs }: { tabs: WorkspaceTab[] }) {
  const [active, setActive] = useState(tabs[0]?.id ?? "");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const current = tabs.find((tab) => tab.id === active) ?? tabs[0];
  const currentIndex = tabs.findIndex((tab) => tab.id === current?.id);

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const nextIndex = event.key === "Home"
      ? 0
      : event.key === "End"
        ? tabs.length - 1
        : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    setActive(tabs[nextIndex].id);
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <div className="workspace-tabs">
      <div className="workspace-tab-list" role="tablist" aria-label="Sekcije radnog prostora">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            ref={(element) => { tabRefs.current[index] = element; }}
            id={`workspace-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={tab.id === current?.id}
            aria-controls={`workspace-panel-${tab.id}`}
            tabIndex={index === currentIndex ? 0 : -1}
            className={tab.id === current?.id ? "active" : ""}
            onClick={() => setActive(tab.id)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {current && (
        <div
          id={`workspace-panel-${current.id}`}
          role="tabpanel"
          aria-labelledby={`workspace-tab-${current.id}`}
          tabIndex={0}
        >
          {current.content}
        </div>
      )}
    </div>
  );
}
