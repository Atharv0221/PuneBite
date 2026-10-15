import { useEffect, useMemo, useState } from "react";
import { AMENITY_LABELS, predict } from "../api.js";
import { demoModel } from "../data/demoModel.js";
import { useTween } from "../hooks.js";
import { Icon, Reveal, Ring, SectionHead, Star, emojiFor, rupees } from "../ui.jsx";

const LOCS = [...demoModel.localities].sort();
const verdict = (p) =>
  p >= 0.35 ? ["Strong potential", "great"] : p >= 0.18 ? ["Promising start", "good"] : p >= 0.09 ? ["Average odds", "mid"] : ["Tough start", "low"];

export default function Advisor({ overview }) {
  const [form, setForm] = useState({
    locality: LOCS.includes("Viman Nagar") ? "Viman Nagar" : LOCS[0],
    type: "Casual Dining",
    cost: 700,
    cuisines: ["North Indian"],
    amenities: ["home_delivery"],
  });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const t = setTimeout(async () => {
      const r = await predict(form);
      if (alive) { setRes(r); setLoading(false); }
    }, 320);
    return () => { alive = false; clearTimeout(t); };
  }, [form]);

  const toggle = (key, val) =>
    setForm((f) => ({ ...f, [key]: f[key].includes(val) ? f[key].filter((x) => x !== val) : [...f[key], val] }));

  const p = useTween(res ? res.probability : 0);
  const rating = useTween(res ? res.rating : 0);
  const base = res ? res.baseRate : demoModel.baseRate;
  const [word, tone] = verdict(p);

  const { helps, hurts, maxAbs } = useMemo(() => {
    const c = res ? res.contributions : [];
    return {
      helps: c.filter((x) => x.value > 0.03).slice(0, 4),
      hurts: c.filter((x) => x.value < -0.03).slice(-4).reverse(),
      maxAbs: Math.max(0.2, ...c.map((x) => Math.abs(x.value))),
    };
  }, [res]);

  const fill = ((form.cost - 100) / (3000 - 100)) * 100;

  return (
    <section id="advisor" className="section">
      <div className="container">
        <SectionHead eyebrow="Opening Advisor" title="Planning a restaurant? Test your idea."
          sub="Describe a new restaurant and our model estimates its chance of earning 4.0 stars or more, before a single review exists." />

        <div className="advisor">
          <Reveal className="card form">
            <div className="field">
              <label htmlFor="loc">Locality</label>
              <div className="select">
                <select id="loc" value={form.locality} onChange={(e) => setForm({ ...form, locality: e.target.value })}>
                  {LOCS.map((l) => <option key={l}>{l}</option>)}
                </select>
              </div>
            </div>

            <div className="field">
              <label>Restaurant type</label>
              <div className="chips">
                {demoModel.types.map((t) => (
                  <button key={t} className={`chip-btn ${form.type === t ? "on" : ""}`} onClick={() => setForm({ ...form, type: t })}>
                    {emojiFor(t)} {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="field">
              <label htmlFor="cost">Typical price for two <b className="price">{rupees(form.cost)}</b></label>
              <input id="cost" type="range" min="100" max="3000" step="50" value={form.cost} className="slider"
                     style={{ "--fill": fill + "%" }} onChange={(e) => setForm({ ...form, cost: Number(e.target.value) })} />
              <div className="range-ends"><span>₹100</span><span>₹3,000</span></div>
            </div>

            <div className="field">
              <label>Cuisines</label>
              <div className="chips">
                {demoModel.cuisines.map((c) => (
                  <button key={c} className={`chip-btn ${form.cuisines.includes(c) ? "on" : ""}`} onClick={() => toggle("cuisines", c)}>
                    {emojiFor(c)} {c}
                  </button>
                ))}
              </div>
            </div>

            <div className="field">
              <label>Amenities</label>
              <div className="switches">
                {demoModel.amenities.map((a) => (
                  <button key={a} role="switch" aria-checked={form.amenities.includes(a)}
                          className={`switch ${form.amenities.includes(a) ? "on" : ""}`} onClick={() => toggle("amenities", a)}>
                    <i /><span>{AMENITY_LABELS[a]}</span>
                  </button>
                ))}
              </div>
            </div>
          </Reveal>

          <Reveal delay={120} className={`card result ${tone} ${loading ? "loading" : ""}`}>
            <div className="result-top">
              <Ring value={p} max={1} marker={base} size={190} stroke={16}>
                <b className="big">{Math.round(p * 100)}%</b>
                <small>chance of 4.0★+</small>
              </Ring>
              <div className="result-text">
                <span className={`verdict ${tone}`}><Icon name="spark" size={14} /> {word}</span>
                <p className="est">Expected rating <b><Star size={16} /> {rating.toFixed(2)}</b></p>
                <p className="muted">
                  That is <b>{(Math.max(p, 0.001) / base).toFixed(1)}×</b> the Pune average of {Math.round(base * 100)}% (white dot on the ring).
                </p>
              </div>
            </div>

            <div className="drivers">
              <div>
                <h4>What helps</h4>
                {helps.length === 0 && <p className="muted small">Nothing stands out yet. Try adding amenities.</p>}
                {helps.map((x) => (
                  <div className="driver up" key={x.key}>
                    <span>{x.label}</span>
                    <div className="bar"><i style={{ width: `${(x.value / maxAbs) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
              <div>
                <h4>Weighs against it</h4>
                {hurts.length === 0 && <p className="muted small">No strong negatives.</p>}
                {hurts.map((x) => (
                  <div className="driver down" key={x.key}>
                    <span>{x.label}</span>
                    <div className="bar"><i style={{ width: `${(Math.abs(x.value) / maxAbs) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            </div>

            <p className="note">
              <span className={`pill source ${res && res.source === "live" ? "live" : "demo"}`}><i /> {res ? (res.source === "live" ? "Live" : "Demo") : "…"}</span>
              {res ? res.modelNote : "Loading model…"}. Each factor shows the model’s weighting given your other choices, not a stand-alone effect. Food quality and service are not in the data, so treat this as a guide, not a guarantee.
            </p>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
