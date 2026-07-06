export function formatDate(value?: string | null) {
  if (!value) return "-";
  const datePart = value.slice(0, 10);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(datePart);
  if (match) return `${match[3]}/${match[2]}/${match[1]}`;
  return value;
}

export function toDisplayDate(value?: string | null) {
  const formatted = formatDate(value);
  return formatted === "-" ? "" : formatted;
}

export function parseDisplayDate(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return "";
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(trimmed);
  if (!match) return null;
  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);
  const date = new Date(Date.UTC(year, month - 1, day));
  if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) return null;
  return `${match[3]}-${match[2]}-${match[1]}`;
}

export function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return formatDate(value);
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${day}/${month}/${year} ${hours}:${minutes}`;
}
