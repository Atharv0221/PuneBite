import { useState } from "react";
import useFetch, { Status } from "./useFetch.jsx";
import { unwrap, qs, fmtRating, fmtCost } from "../api.js";

export default function Gems() {
  const [loc, setLoc] = useState("");
  const [applied, setApplied] = useState("");
  const { data, error, loading } = useFetch(`/api/hidden-gems${qs({ locality: applied })}`);
  const rows = unwrap(data);
  return (
    <>
      <h2>Hidden gems</h2>
      <p className="note">Places rated 4.0+ with only 20 to 150 votes. This is a provisional rule until the trust-adjusted score (Phase 8) replaces it.</p>
      <form className="filters" onSubmit={(e) => { e.preventDefault(); setApplied(loc); }}>
        <input placeholder="Locality (optional)" value={loc} onChange={(e) => setLoc(e.target.value)} />
        <button className="primary">Find gems</button>
      </form>
      <Status loading={loading} error={error} />
      <section className="grid">
        {rows.map((r, i) => (
          <article className="panel gem" key={r.url ?? i}>
            <h3>{r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.name}</a> : r.name}</h3>
            <p>{r.locality} · {r.establishment_type}</p>
            <p><b>{fmtRating(r.rating)}</b> from {r.votes ?? 0} votes · {fmtCost(r.cost_for_two)} for two</p>
            <p className="note">{(r.cuisines || []).slice(0, 4).join(", ")}</p>
          </article>
        ))}
      </section>
      {data && !rows.length && <p className="note">No hidden gems found for this locality.</p>}
    </>
  );
}
