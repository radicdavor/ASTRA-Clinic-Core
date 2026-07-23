import type { ReactNode } from "react";

type ClinicalDerivedDataNoticeProps = {
  children?: ReactNode;
  level?: "global" | "context";
  title?: string;
};

const defaultMessages = {
  global: "AI i drugi izvedeni podaci nisu dijagnoza ni izvor istine. Provjerite povezani izvorni dokument; liječnički pregled ostaje obvezan. Ovaj prikaz sam ne mijenja status, ne stvara zadatak i ne šalje poruku.",
  context: "Ovaj pomoćni prikaz ne donosi kliničku odluku. Provjerite povezani izvor prije potvrde."
};

export function ClinicalDerivedDataNotice({
  children,
  level = "global",
  title = "Pomoćni klinički prikaz"
}: ClinicalDerivedDataNoticeProps) {
  return (
    <aside
      aria-label={`${title}. Sigurnosna napomena.`}
      className={`clinical-derived-data-notice clinical-derived-data-notice-${level}`}
      role="note"
    >
      <strong>{title}</strong>
      <p>{children ?? defaultMessages[level]}</p>
    </aside>
  );
}
