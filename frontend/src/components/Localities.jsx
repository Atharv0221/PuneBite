import { useEffect, useMemo, useState } from "react";
import { Icon, Reveal, Ring, SectionHead, Star, emojiFor, hueOf, pickOf, rupees } from "../ui.jsx";

const SORTS = [["top", "Top rated"], ["places", "Most places"], ["value", "Best value"], ["gems", "Most gems"]];
const sorters = {
  top: (a, b) => b.avgRating - a.avgRating,
  places: (a, b) => b.total - a.total,
  value: (a, b) => a.medianCost - b.medianCost || b.avgRating - a.avgRating,
  gems: (a, b) => b.gems - a.gems || b.avgRating - a.avgRating,
};

function LocalityCard({ loc, i, avg, onOpen }) {
  const diff = loc.avgRating - avg;
  const pct = Math.max(4, Math.min(100, (loc.avgRating - 3) * 100));
  const avgPct = Math.max(0, Math.min(100, (avg - 3) * 100));
  return (
    <button className="card loc-card" style={{ "--i": i, "--h": hueOf(loc.name) }} onClick={() => onOpen(loc)}>
      <div className="loc-art">
        <span className="loc-emoji">{emojiFor(pickOf(loc.name, [...loc.topCuisines, loc.topType]))}</span>
        <span className="loc-dot d1" /><span className="loc-dot d2" /><span className="loc-dot d3" />
        {loc.gems > 0 && <span className="loc-gem"><Icon name="gem" size={13} /> {loc.gems}</span>}
      </div>
      <div className="loc-body">
        <h3>{loc.name}</h3>
        <p className="muted">{loc.topType}{loc.topCuisines.length ? ` · ${loc.topCuisines.slice(0, 2).join(", ")}` : ""}</p>
        <div className="meter" title="Compared with the Pune average">
          <span style={{ "--w": pct + "%" }} /><i style={{ left: avgPct + "%" }} />
        </div>
        <div className="loc-row">
          <b><Star /> {loc.avgRating.toFixed(2)}</b>
          <span className={diff >= 0 ? "up" : "down"}>{diff >= 0 ? "+" : ""}{diff.toFixed(2)} vs Pune</span>
        </div>
        <div className="loc-row small"><span>{rupees(loc.medianCost)} for two</span><span>{loc.total} places</span></div>
      </div>
    </button>
  );
}

function Drawer({ loc, open, avg, gems, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", onKey); document.body.style.overflow = prev; };
  }, [onClose]);

  const here = gems.filter((g) => g.locality === loc.name).slice(0, 4);
  const diff = loc.avgRating - avg;
  return (
    <div className={`drawer-root ${open ? "open" : ""}`} role="dialog" aria-modal="true" aria-label={`${loc.name} report card`}>
      <div className="backdrop" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-head" style={{ "--h": hueOf(loc.name) }}>
          <button className="icon-btn close" onClick={onClose} aria-label="Close"><Icon name="close" /></button>
          <span className="drawer-emoji">{emojiFor(pickOf(loc.name, [...loc.topCuisines, loc.topType]))}</span>
          <h3>{loc.name}</h3>
          <p>Locality report card</p>
        </div>
        <div className="drawer-body">
          <div className="drawer-score">
            <Ring value={open ? loc.avgRating : 0} max={5} size={132} stroke={11}>
              <b>{loc.avgRating.toFixed(2)}</b><small>avg rating</small>
            </Ring>
            <div>
              <span className={`delta ${diff >= 0 ? "up" : "down"}`}>{diff >= 0 ? "▲" : "▼"} {Math.abs(diff).toFixed(2)} vs Pune ({avg.toFixed(2)})</span>
              <p className="muted">Based on {loc.rated.toLocaleString("en-IN")} rated restaurants out of {loc.total.toLocaleString("en-IN")} listed.</p>
            </div>
          </div>

          <div className="tiles">
            <div><b>{rupees(loc.medianCost)}</b><span>median for two</span></div>
            <div><b>{loc.pctHigh}%</b><span>rated 4.0+</span></div>
            <div><b>{loc.total}</b><span>restaurants</span></div>
            <div><b>{loc.gems}</b><span>hidden gems</span></div>
          </div>

          <h4>Signature flavours</h4>
          <div className="chips">
            {loc.topCuisines.map((c) => <span className="chip-soft" key={c}>{emojiFor(c)} {c}</span>)}
            <span className="chip-soft">{emojiFor(loc.topType)} {loc.topType}</span>
          </div>

          <h4>Hidden gems here</h4>
          {here.length === 0 && <p className="muted">No hidden gems detected in this area yet.</p>}
          <ul className="mini-list">
            {here.map((g) => (
              <li key={g.name}>
                <span className="mini-emoji">{emojiFor(g.cuisines[0] || g.type)}</span>
                <div><b>{g.name}</b><small>{g.type} · {g.votes} reviews · {rupees(g.cost)}</small></div>
                <em><Star size={13} /> {g.rating.toFixed(1)}</em>
              </li>
            ))}
          </ul>
        </div>
      </aside>
    </div>
  );
}

export default function Localities({ localities, gems, overview }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("top");
  const [all, setAll] = useState(false);
  const [sel, setSel] = useState(null);
  const [open, setOpen] = useState(false);

  const list = useMemo(
    () => localities.filter((l) => l.name.toLowerCase().includes(q.trim().toLowerCase())).sort(sorters[sort]),
    [localities, q, sort]
  );
  const shown = all || q ? list : list.slice(0, 9);

  const openDrawer = (loc) => { setSel(loc); requestAnimationFrame(() => requestAnimationFrame(() => setOpen(true))); };
  const closeDrawer = () => { setOpen(false); setTimeout(() => setSel(null), 320); };

  return (
    <section id="localities" className="section">
      <div className="container">
        <SectionHead eyebrow="Where to eat" title="Explore Pune, locality by locality"
          sub="Compare average ratings, prices and flavours. Tap any card for its full report card." />

        <Reveal className="toolbar">
          <label className="search">
            <Icon name="search" size={18} />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search a locality, e.g. Baner" aria-label="Search localities" />
          </label>
          <div className="seg" style={{ "--n": SORTS.length, "--idx": SORTS.findIndex(([k]) => k === sort) }} role="tablist">
            <span className="seg-thumb" />
            {SORTS.map(([k, label]) => (
              <button key={k} role="tab" aria-selected={sort === k} className={sort === k ? "on" : ""} onClick={() => setSort(k)}>{label}</button>
            ))}
          </div>
        </Reveal>

        <div className="loc-grid" key={sort + "|" + q + "|" + all}>
          {shown.map((l, i) => <LocalityCard key={l.name} loc={l} i={i} avg={overview.avgRating} onOpen={openDrawer} />)}
          {shown.length === 0 && <p className="muted empty">No locality matches &ldquo;{q}&rdquo;.</p>}
        </div>

        {!q && list.length > 9 && (
          <div className="center">
            <button className="btn ghost" onClick={() => setAll((a) => !a)}>
              {all ? "Show fewer" : `Show all ${list.length} localities`}
            </button>
          </div>
        )}
      </div>
      {sel && <Drawer loc={sel} open={open} avg={overview.avgRating} gems={gems} onClose={closeDrawer} />}
    </section>
  );
}
