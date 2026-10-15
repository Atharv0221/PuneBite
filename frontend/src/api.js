// All talking to the Flask backend lives here. If the API is not running, the app
// silently falls back to demo data generated from the real project dataset.
import { demoModel } from "./data/demoModel.js";

// Set VITE_API_URL in frontend/.env (for example VITE_API_URL=http://127.0.0.1:5000).
// An empty string turns the network off completely (demo mode).
const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:5000";

async function request(path, options = {}, timeout = 2500) {
  if (!BASE) throw new Error("API disabled");
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  try {
    const res = await fetch(BASE + path, { ...options, signal: ctrl.signal });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

const pick = (o, keys, fallback) => {
  for (const k of keys) if (o && o[k] !== undefined && o[k] !== null) return o[k];
  return fallback;
};

// ---- adapters: accept a few common key spellings so the UI survives small API changes
export const normLocality = (x) => ({
  name: pick(x, ["name", "locality", "_id"], "Unknown"),
  total: pick(x, ["total", "count", "n_restaurants", "restaurants"], 0),
  rated: pick(x, ["rated", "rated_count", "n_rated"], 0),
  avgRating: Number(pick(x, ["avgRating", "avg_rating", "average_rating"], 0)),
  medianCost: Math.round(Number(pick(x, ["medianCost", "median_cost", "avg_cost", "median_price"], 0))),
  pctHigh: Number(pick(x, ["pctHigh", "pct_high", "share_high_rated"], 0)),
  topCuisines: pick(x, ["topCuisines", "top_cuisines"], []),
  topType: pick(x, ["topType", "top_type", "establishment_type"], "Restaurant"),
  gems: pick(x, ["gems", "n_gems", "gem_count"], 0),
});

export const normGem = (x) => ({
  name: pick(x, ["name"], "Restaurant"),
  locality: pick(x, ["locality"], ""),
  rating: Number(pick(x, ["rating"], 0)),
  votes: Number(pick(x, ["votes"], 0)),
  cost: Math.round(Number(pick(x, ["cost", "cost_capped", "cost_for_two"], 0))),
  type: pick(x, ["type", "primary_type", "establishment_type"], "Restaurant"),
  cuisines: pick(x, ["cuisines"], []),
  beats: Math.min(99, Math.round(Number(pick(x, ["beats", "peer_percentile"], 95)))),
  url: pick(x, ["url", "web_link"], ""),
});

export async function loadData() {
  const out = {};
  try {
    const locs = await request("/api/localities");
    const list = Array.isArray(locs) ? locs : pick(locs, ["localities", "data", "items"], []);
    if (list.length) { out.localities = list.map(normLocality).filter((l) => l.avgRating > 0); out.source = "live"; }
  } catch (e) { /* offline: keep demo data */ }
  try {
    const g = await request("/api/hidden-gems?limit=120");
    const list = Array.isArray(g) ? g : pick(g, ["gems", "data", "items"], []);
    if (list.length) { out.gems = list.map(normGem); out.source = "live"; }
  } catch (e) { /* offline */ }
  try {
    const o = await request("/api/stats/overview");
    if (o && typeof o === "object") {
      out.overview = {
        restaurants: pick(o, ["restaurants", "total", "n_restaurants"], undefined),
        rated: pick(o, ["rated", "n_rated"], undefined),
        localities: pick(o, ["localities", "n_localities"], undefined),
        avgRating: pick(o, ["avgRating", "avg_rating"], undefined),
        pctHigh: pick(o, ["pctHigh", "pct_high"], undefined),
        gems: pick(o, ["gems", "n_gems"], undefined),
      };
      Object.keys(out.overview).forEach((k) => out.overview[k] === undefined && delete out.overview[k]);
    }
  } catch (e) { /* offline */ }
  return out.source ? out : null;
}

// ---- Opening Advisor ---------------------------------------------------------
export const AMENITY_LABELS = {
  outdoor_seating: "Outdoor seating",
  home_delivery: "Home delivery",
  free_parking: "Free parking",
  full_bar_available: "Full bar",
  table_booking_recommended: "Table booking",
  valet_parking_available: "Valet parking",
  live_music: "Live music",
  wifi: "Wi-Fi",
};

const sigmoid = (z) => 1 / (1 + Math.exp(-z));
const clamp = (x, a, b) => Math.min(b, Math.max(a, x));

/** Runs the small demo model in the browser (used when the API is not available). */
export function demoPredict(f) {
  const m = demoModel;
  const feats = {};
  feats.logcost = (Math.log(Math.max(50, f.cost)) - m.logcost.mu) / m.logcost.sd;
  if (m.types.includes(f.type)) feats["type:" + f.type] = 1;
  if (m.localities.includes(f.locality)) feats["loc:" + f.locality] = 1;
  f.cuisines.forEach((c) => m.cuisines.includes(c) && (feats["cuis:" + c] = 1));
  f.amenities.forEach((a) => m.amenities.includes(a) && (feats["am:" + a] = 1));

  let z = m.clf.intercept, r = m.reg.intercept;
  const contributions = [];
  for (const [k, v] of Object.entries(feats)) {
    const c = (m.clf.coef[k] ?? 0) * v;
    z += c;
    r += (m.reg.coef[k] ?? 0) * v;
    contributions.push({ key: k, value: c, label: describe(k, v) });
  }
  contributions.sort((a, b) => b.value - a.value);
  return {
    probability: sigmoid(z),
    rating: clamp(r, 2.4, 4.8),
    contributions,
    baseRate: m.baseRate,
    source: "demo",
    modelNote: `Demo model in your browser (AUC ${m.auc})`,
  };
}

function describe(key, v) {
  if (key === "logcost") return v >= 0 ? "Higher price point" : "Lower price point";
  const [kind, name] = key.split(":");
  if (kind === "type") return `Type: ${name}`;
  if (kind === "loc") return `Location: ${name}`;
  if (kind === "cuis") return `Serves ${name}`;
  if (key.startsWith("am:")) return AMENITY_LABELS[key.slice(3)] || key.slice(3);
  return key;
}

/** Tries the Flask API first (POST /api/predict), then the in-browser demo model. */
export async function predict(f) {
  try {
    const res = await request(
      "/api/predict",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          locality: f.locality,
          primary_type: f.type,
          cost_capped: f.cost,
          cuisines: f.cuisines,
          amenities: f.amenities,
        }),
      },
      3000
    );
    const p = pick(res, ["probability", "probability_high", "proba", "prob_high"], null);
    const r = pick(res, ["predicted_rating", "rating"], null);
    if (p !== null) {
      const local = demoPredict(f); // reuse local explanation of what helps/hurts
      return { ...local, probability: Number(p), rating: r !== null ? Number(r) : local.rating, source: "live", modelNote: "Live model from the PuneBite API" };
    }
  } catch (e) { /* fall through to demo */ }
  return demoPredict(f);
}
