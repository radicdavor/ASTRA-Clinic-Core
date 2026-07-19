import { ButtonHTMLAttributes, MouseEvent, ReactNode, useState } from "react";
import { ConfirmActionDialog } from "./ConfirmActionDialog";
import { HelpHint } from "./HelpHint";

type ActionButtonProps = {
  variant: "info" | "create" | "update" | "workflow" | "danger" | "ai" | "admin";
  helpTitle?: string;
  help?: ReactNode;
  requiresConfirm?: boolean;
  confirmMessage?: string;
  children: ReactNode;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onClick"> & {
  onClick?: () => void | Promise<void>;
};

export function ActionButton({ variant, helpTitle, help, requiresConfirm, confirmMessage, children, className = "", onClick, type = "button", ...props }: ActionButtonProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  async function runAction() {
    await onClick?.();
    setConfirmOpen(false);
  }

  async function handleClick(event: MouseEvent<HTMLButtonElement>) {
    if (requiresConfirm) {
      event.preventDefault();
      setConfirmOpen(true);
      return;
    }
    await onClick?.();
  }

  return (
    <>
      <span className="action-with-help">
        <button type={type} className={`action-button action-${variant} ${className}`.trim()} onClick={onClick ? handleClick : undefined} {...props}>
          {children}
        </button>
        {help && <HelpHint title={helpTitle ?? String(children)}>{help}</HelpHint>}
      </span>
      <ConfirmActionDialog
        open={confirmOpen}
        title={helpTitle ?? "Potvrditi radnju"}
        message={confirmMessage ?? "Potvrditi radnju?"}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={runAction}
      />
    </>
  );
}
