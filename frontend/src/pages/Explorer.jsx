import { useState } from "react";
import useFetch, { Status } from "./useFetch.jsx";
import { unwrap, pick, qs, fmtRating, fmtCost } from "../api.js";

export default function Explorer() {
  const [f, setF] = useState({ locality: "", cuisine: "", min_rating: "", max_cost: "", type: "" });
  const [applied, setApplied] = useState(f);
  const [page, setPage] = useState(1);
  const { data, error, loading } = useFetch(`/api/restaurants${qs({ ...applied, page })}`);
  const rows = unwrap(data);
  const pages = data?.pages ?? data?.total_pages;
  const total = data?.total;

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const apply = (e) => { e.preventDefault(); setPage(1); setApplied(f); };

  return (
    <>
      <h2>Restaurant explorer</h2>
      <form className="filters" onSubmit={apply}>
        <input placeholder="Locality (e.g. Baner)" value={f.locality} onChange={set("locality")} />
        <input placeholder="Cuisine (e.g. Biryani)" value={f.cuisine} onChange={set("cuisine")} />
        <input placeholder="Type (e.g. Cafe)" value={f.type} onChange={set("type")} />
        <input type="number" step="0.1" min="0" max="5" placeholder="Min rating" value={f.min_rating} onChange={set("min_rating")} />
        <input type="number" min="0" placeholder="Max cost for two (₹)" value={f.max_cost} onChange={set("max_cost")} />
        <button className="primary">Apply filters</button>
      </form>
      <Status loading={loading} error={error} />
      {data && (
        <>
          <p className="note">{total != null ? `${total.toLocaleString("en-IN")} restaurants` : `${rows.length} shown`}</p>
          <div className="scroll">
            <table>
              <thead>
                <tr><th>Name</th><th>Locality</th><th>Type</th><th>Rating</th><th>Trust-adjusted</th><th>Votes</th><th>Cost for two</th><th>Cuisines</th></tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={pick(r, "url", "_id") ?? i}>
                    <td>{r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.name}</a> : r.name}</td>
                    <td>{r.locality}</td>
                    <td>{r.establishment_type}</td>
                    <td className="num">{fmtRating(r.rating)}</td>
                    <td className="num">{r.trust_rating != null ? fmtRating(r.trust_rating) : "–"}</td>
                    <td className="num">{r.votes ?? 0}</td>
                    <td className="num">{fmtCost(r.cost_for_two)}</td>
                    <td>{(r.cuisines || []).slice(0, 3).join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!rows.length && <p className="note">No restaurants match these filters. Loosen one of them.</p>}
          </div>
          <div className="pager">
            <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <span>Page {page}{pages ? ` of ${pages}` : ""}</span>
            <button disabled={pages ? page >= pages : rows.length === 0} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>
      )}
    </>
  );
}
