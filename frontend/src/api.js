// All API access lives here. If a response shape differs from what the pages
// expect, fix it in this one file (see unwrap / pick).
export async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try { const j = await res.json(); msg = j.error || j.message || msg; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

// Accepts [..] or { items | restaurants | localities | results | data: [..] }
export function unwrap(d) {
  if (Array.isArray(d)) return d;
  if (!d || typeof d !== "object") return [];
  for (const k of ["items", "restaurants", "localities", "gems", "results", "data"]) {
    if (Array.isArray(d[k])) return d[k];
  }
  return [];
}

// First defined value among several possible field names
export const pick = (o, ...keys) => {
  for (const k of keys) if (o && o[k] !== undefined && o[k] !== null) return o[k];
  return undefined;
};

export const qs = (params) => {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== "" && v != null && p.set(k, v));
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const fmtRating = (r) => (r == null || Number.isNaN(Number(r)) ? "unrated" : Number(r).toFixed(1));
export const fmtCost = (c) => (c == null ? "n/a" : `₹${Number(c).toLocaleString("en-IN")}`);
