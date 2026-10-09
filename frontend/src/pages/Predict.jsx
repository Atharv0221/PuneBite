import { useState } from "react";
import useFetch, { Status } from "./useFetch.jsx";
import { api } from "../api.js";

const label = (a) => a.replace(/_/g, " ");

export default function Predict() {
  const opts = useFetch("/api/meta/options");
  const [f, setF] = useState({ cost: 800, type: "Casual Dining", locality: "Baner", cuisines: ["North Indian", "Chinese"], amenities: ["table_booking_recommended", "live_music"], accepts_cards: true });
  const [out, setOut] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const o = opts.data;

  const toggle = (key) => (v) =>
    setF({ ...f, [key]: f[key].includes(v) ? f[key].filter((x) => x !== v) : [...f[key], v] });

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      const body = { ...f, cost: Number(f.cost), accepts_digital: f.accepts_cards };
      setOut(await api("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }));
    } catch (x) { setErr(x.message); setOut(null); }
    setBusy(false);
  }

  const prob = out?.high_rated_probability;
  const Checks = ({ name, items }) => (
    <fieldset>
      <legend>{name}</legend>
      <div className="checks">
        {items.map((a) => (
          <label className="check" key={a}>
            <input type="checkbox" checked={f[name.toLowerCase()].includes(a)} onChange={() => toggle(name.toLowerCase())(a)} />
            {label(a)}
          </label>
        ))}
      </div>
    </fieldset>
  );

  return (
    <>
      <h2>Rating predictor</h2>
      <p className="note">For someone planning a new restaurant. The model has no vote or food-quality data, so treat the result as a rough guide.</p>
      <Status loading={opts.loading} error={opts.error} />
      {o && (
        <div className="split">
          <form className="panel stack" onSubmit={submit}>
            <label>Cost for two (₹)<input type="number" min="1" value={f.cost} onChange={(e) => setF({ ...f, cost: e.target.value })} /></label>
            <label>Establishment type
              <select value={f.type} onChange={(e) => setF({ ...f, type: e.target.value })}>{o.types.map((t) => <option key={t}>{t}</option>)}</select>
            </label>
            <label>Locality
              <select value={f.locality} onChange={(e) => setF({ ...f, locality: e.target.value })}>
                {o.localities.map((t) => <option key={t}>{t}</option>)}<option>Other</option>
              </select>
            </label>
            <label className="check"><input type="checkbox" checked={f.accepts_cards} onChange={(e) => setF({ ...f, accepts_cards: e.target.checked })} />Accepts cards and digital payment</label>
            <Checks name="Cuisines" items={o.cuisines} />
            <Checks name="Amenities" items={o.amenities} />
            <button className="primary" disabled={busy}>{busy ? "Predicting…" : "Predict rating"}</button>
          </form>
          <div className="panel result">
            {err && <p className="note err">{err}</p>}
            {!out && !err && <p className="note">Fill in the form and predict to see the result.</p>}
            {out && (
              <>
                <p className="big">{(prob * 100).toFixed(1)}%</p>
                <p>chance of a 4.0+ rating</p>
                <div className="meter"><span style={{ width: `${prob * 100}%` }} /></div>
                <p>Predicted rating: <b>{out.predicted_rating.toFixed(2)}</b></p>
                <p>Highly rated: <b>{out.predicted_high_rated ? "Yes" : "No"}</b> <span className="note">(threshold {out.decision_threshold})</span></p>
                <p className="note">{out.note}</p>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
