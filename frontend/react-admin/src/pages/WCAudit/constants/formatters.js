// ── Formatters ────────────────────────────────────────────────────────────────
export const fmt = (n) =>
  n == null ? "—" :
  n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` :
  `$${(n / 1_000).toFixed(0)}K`;

export const pct = (n) => `${n ?? 0}%`;

export const money = (n) =>
  n == null ? "—" : `$${Number(n).toLocaleString()}`;