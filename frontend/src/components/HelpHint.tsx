import { ReactNode, useState } from "react";

type HelpHintProps = {
  title: string;
  children: ReactNode;
};

export function HelpHint({ title, children }: HelpHintProps) {
  const [open, setOpen] = useState(false);
  return (
    <span className="help-hint" onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        className="help-hint-trigger"
        aria-label={title}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onMouseEnter={() => setOpen(true)}
      >
        ?
      </button>
      {open && (
        <span className="help-hint-popover" role="tooltip">
          <strong>{title}</strong>
          <span>{children}</span>
        </span>
      )}
    </span>
  );
}
