import { ButtonHTMLAttributes, ReactNode } from "react";
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
  async function handleClick() {
    if (requiresConfirm && !window.confirm(confirmMessage ?? "Potvrditi radnju?")) return;
    await onClick?.();
  }

  return (
    <span className="action-with-help">
      <button type={type} className={`action-button action-${variant} ${className}`.trim()} onClick={onClick ? handleClick : undefined} {...props}>
        {children}
      </button>
      {help && <HelpHint title={helpTitle ?? String(children)}>{help}</HelpHint>}
    </span>
  );
}
