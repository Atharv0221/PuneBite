import { useState } from "react";
import useFetch, { Status } from "./useFetch.jsx";
import Bars from "../Bars.jsx";
import { unwrap, pick, fmtRating, fmtCost } from "../api.js";

function ReportCard({ name }) {
  const { data, error, loading } = useFetch(`/api/localities/${encodeURIComponent(name)}`);
  if (!data) return <Status loading={loading} error={error} />;
  const cuisines = (pick(data, "top_cuisines", "cuisines") || []).map((c) =>
    typeof c === "string" ? { label: c, value: 1 } : { label: c.cuisine ?? c.name ?? c.label, value: c.count ?? c.value ?? 1 });
  return (
    <div className="panel card">
      <h3>{name}</h3>
      <div className="tiles small">
        <div className="tile"><b>{pick(data, "count", "n_restaurants", "restaurants") ?? "–"}</b><span>Restaurants</span></div>
        <div className="tile"><b>{fmtRating(pick(data, "avg_rating"))}</b><span>Avg rating</span></div>
        <div className="tile"><b>{fmtCost(pick(data, "avg_cost", "avg_cost_for_two"))}</b><span>Avg cost for two</span></div>
        <div className="tile"><b>{data.high_rated_share != null ? `${(data.high_rated_share * 100).toFixed(0)}%` : "–"}</b><span>Rated 4.0+</span></div>
      </div>
      {data.best_restaurants?.length > 0 && (<><h4>Best rated (20+ votes)</h4><ul>{data.best_restaurants.map((r) => <li key={r.url ?? r.name}>{r.name} · {fmtRating(r.rating)} ({r.votes} votes)</li>)}</ul></>)}
      {cuisines.length > 0 && (<><h4>Top cuisines</h4>{typeof (pick(data, "top_cuisines", "cuisines") || [])[0] === "string"
        ? <p>{cuisines.map((c) => c.label).join(", ")}</p> : <Bars data={cuisines.slice(0, 8)} />}</>)}
    </div>
  );
}

export default function Localities() {
  const { data, error, loading } = useFetch("/api/localities");
  const [sel, setSel] = useState("");
  const [min, setMin] = useState(20);
  const rows = unwrap(data)
    .map((l) => ({ ...l, _n: pick(l, "count", "n_restaurants") ?? 0, _name: pick(l, "name", "locality", "_id") }))
    .filter((l) => l._n >= min)
    .sort((a, b) => (b.avg_rating ?? 0) - (a.avg_rating ?? 0));

  return (
    <>
      <h2>Locality report cards</h2>
      <Status loading={loading} error={error} />
      {data && (
        <div className="split">
          <div className="panel">
            <label className="inline">Minimum restaurants
              <input type="number" min="1" value={min} onChange={(e) => setMin(Number(e.target.value) || 1)} />
            </label>
            <h3>Average rating by locality</h3>
            <ul className="pick">
              {rows.slice(0, 25).map((l) => (
                <li key={l._name}>
                  <button className={sel === l._name ? "on" : ""} onClick={() => setSel(l._name)}>
                    <span>{l._name}</span><span className="num">{fmtRating(l.avg_rating)} · {l._n}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
          {sel ? <ReportCard name={sel} /> : <p className="note">Pick a locality to see its report card.</p>}
        </div>
      )}
    </>
  );
}
