import { useMemo, useState } from "react";
import { useTilt } from "../hooks.js";
import { Icon, Reveal, SectionHead, Star, emojiFor, hueOf, rupees } from "../ui.jsx";

function GemCard({ g, i }) {
  const tilt = useTilt(7);
  const h = hueOf(g.name);
  return (
    <Reveal delay={(i % 3) * 90} className="gem-wrap">
      <article className="card gem" {...tilt}>
        <div className="gem-photo" style={{ "--h": h }}>
          <span className="gem-emoji">{emojiFor(g.cuisines[0] || g.type)}</span>
          <span className="gem-badge"><Icon name="gem" size={13} /> Hidden gem</span>
          <span className="gem-rating"><Star size={14} /> {g.rating.toFixed(1)}</span>
        </div>
        <div className="gem-body">
          <h3 title={g.name}>{g.name}</h3>
          <p className="muted"><Icon name="pin" size={14} /> {g.locality} · {g.type}</p>
          <div className="chips">
            {g.cuisines.map((c) => <span key={c} className="chip-soft sm">{c}</span>)}
          </div>
          <div className="gem-stats">
            <div><b>{g.votes}</b><span>reviews</span></div>
            <div><b>{rupees(g.cost)}</b><span>for two</span></div>
          </div>
          <div className="beats">
            <div className="beats-bar"><span style={{ "--w": g.beats + "%" }} /></div>
            <small>Beats <b>{g.beats}%</b> of restaurants with a similar number of reviews</small>
          </div>
          {g.url && <a className="link-out" href={g.url} target="_blank" rel="noopener noreferrer">View on Zomato <Icon name="external" size={14} /></a>}
        </div>
        <span className="glare" />
      </article>
    </Reveal>
  );
}

export default function Gems({ gems }) {
  const [loc, setLoc] = useState("All");
  const [count, setCount] = useState(9);

  const chips = useMemo(() => {
    const n = {};
    gems.forEach((g) => { n[g.locality] = (n[g.locality] || 0) + 1; });
    return Object.entries(n).filter(([, c]) => c >= 3).sort((a, b) => b[1] - a[1]).slice(0, 7);
  }, [gems]);
  const filtered = useMemo(() => (loc === "All" ? gems : gems.filter((g) => g.locality === loc)), [gems, loc]);

  return (
    <section id="gems" className="section alt">
      <div className="container">
        <SectionHead eyebrow="Hidden gems" title="Great food that hasn’t gone viral yet"
          sub="Raw star ratings reward popularity. We look for restaurants that are clearly better than others with a similar number of reviews." />

        <Reveal className="how">
          {[["1", "Genuinely good", "Rated 3.8★ or higher"],
            ["2", "Beats its peers", "At least 1.5 standard deviations above restaurants with similar review counts"],
            ["3", "Not famous yet", "Between 20 and 300 reviews, enough to trust, few enough to be a secret"]].map(([n, t, d]) => (
            <div className="how-step" key={n}><span>{n}</span><div><b>{t}</b><small>{d}</small></div></div>
          ))}
        </Reveal>

        <Reveal className="chips filters">
          <button className={`chip-btn ${loc === "All" ? "on" : ""}`} onClick={() => { setLoc("All"); setCount(9); }}>All areas</button>
          {chips.map(([name, c]) => (
            <button key={name} className={`chip-btn ${loc === name ? "on" : ""}`} onClick={() => { setLoc(name); setCount(9); }}>
              {name} <em>{c}</em>
            </button>
          ))}
        </Reveal>

        <div className="gem-grid" key={loc}>
          {filtered.slice(0, count).map((g, i) => <GemCard key={g.name + g.locality} g={g} i={i} />)}
        </div>

        {filtered.length > count && (
          <div className="center">
            <button className="btn ghost" onClick={() => setCount((c) => c + 9)}>Show more gems</button>
          </div>
        )}
      </div>
    </section>
  );
}
