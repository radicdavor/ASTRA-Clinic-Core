import { createContext, useContext, type ReactNode } from "react";

export type ClinicContextStatus =
  | "clinic_context_loading"
  | "clinic_context_ready"
  | "clinic_context_error";

export type ClinicContextValue = {
  status: ClinicContextStatus;
  ready: boolean;
  clinicId: string | null;
  timezone: string | null;
  error: string | null;
};

const ClinicContext = createContext<ClinicContextValue | null>(null);

export function ClinicContextProvider({ value, children }: { value: ClinicContextValue; children: ReactNode }) {
  return <ClinicContext.Provider value={value}>{children}</ClinicContext.Provider>;
}

export function useClinicContext(): ClinicContextValue {
  const value = useContext(ClinicContext);
  if (value) return value;
  return {
    status: "clinic_context_error",
    ready: false,
    clinicId: null,
    timezone: null,
    error: "Clinic context provider is missing.",
  };
}
