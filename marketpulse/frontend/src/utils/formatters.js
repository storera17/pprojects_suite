export function titleCase(value) {
  return String(value || "")
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase());
}

export function truncate(value, max = 220) {
  const text = String(value || "").trim();

  if (text.length <= max) {
    return text;
  }

  return `${text.slice(0, Math.max(0, max - 3)).trimEnd()}...`;
}

export function formatStamp(value) {
  if (!value) {
    return "not recorded";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

export function num(value, digits = 2) {
  const n = Number(value);

  if (!Number.isFinite(n)) {
    return "—";
  }

  return n.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  });
}

export function money(value) {
  const n = Number(value);

  if (!Number.isFinite(n)) {
    return "—";
  }

  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

export function signed(value, digits = 3) {
  const n = Number(value);

  if (!Number.isFinite(n)) {
    return "—";
  }

  return `${n >= 0 ? "+" : ""}${n.toFixed(digits)}`;
}

export function pct(value, digits = 2) {
  const n = Number(value);

  if (!Number.isFinite(n)) {
    return "—";
  }

  return `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`;
}

export function age(value) {
  const n = Number(value);

  if (!Number.isFinite(n)) {
    return "—";
  }

  if (n < 60) {
    return `${n.toFixed(1)} min`;
  }

  if (n < 1440) {
    return `${(n / 60).toFixed(1)} hr`;
  }

  return `${(n / 1440).toFixed(1)} days`;
}