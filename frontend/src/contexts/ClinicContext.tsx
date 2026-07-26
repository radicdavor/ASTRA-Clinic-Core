import { createContext, useContext, type ReactNode } from "react";
import { getActiveClinicId, getActiveClinicTimezone } from "../api/client";

export type ClinicContextValue = {
  ready: boolean;
  clinicId: string | null;
  timezone: string | null;
};

const ClinicContext = createContext<ClinicContextValue | null>(null);

export function ClinicContextProvider({ value, children }: { value: ClinicContextValue; children: ReactNode }) {
  return <ClinicContext.Provider value={value}>{children}</ClinicContext.Provider>;
}

export function useClinicContext(): ClinicContextValue {
  const value = useContext(ClinicContext);
  if (value) return value;
  return {
    ready: true,
    clinicId: getActiveClinicId(),
    timezone: getActiveClinicTimezone(),
  };
}
