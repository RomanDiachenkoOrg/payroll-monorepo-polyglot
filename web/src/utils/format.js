const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

export function money(value) {
  if (value === null || value === undefined || value === "") return "-";
  return usd.format(Number(value));
}

export function shortDate(value) {
  if (!value) return "-";
  const d = new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}

export function dateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });
}

export function period(start, end) {
  return `${shortDate(start)} - ${shortDate(end)}`;
}

export function statusLabel(status) {
  return status ? status.charAt(0) + status.slice(1).toLowerCase() : "";
}

const SEVERITY = {
  ACTIVE: "success",
  INACTIVE: "secondary",
  DRAFT: "secondary",
  SUBMITTED: "info",
  APPROVED: "success",
  REJECTED: "danger",
  CALCULATED: "info",
  PAID: "success",
};

export function statusSeverity(status) {
  return SEVERITY[status] ?? "secondary";
}

export function isoToday() {
  return new Date().toISOString().slice(0, 10);
}

export function mondayOf(date = new Date()) {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() - day + 1);
  return d.toISOString().slice(0, 10);
}

export function addDays(iso, days) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function monthRange(offset = 0, now = new Date()) {
  const start = new Date(Date.UTC(now.getFullYear(), now.getMonth() + offset, 1));
  const end = new Date(Date.UTC(now.getFullYear(), now.getMonth() + offset + 1, 0));
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) };
}
