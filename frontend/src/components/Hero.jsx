import { useRef } from "react";
import { CountUp, Icon, Star } from "../ui.jsx";
import { HeroThali } from "./Art.jsx";

export default function Hero({ overview, gems, insights }) {
  const ref = useRef(null);
  const gem = gems[0];
  const best = insights.best[0];

  const onMove = (e) => {
    const el = ref.current; if (!el) return;
    const r = el.getBoundingClientRect();
    el.style.setProperty("--mx", ((e.clientX - r.left) / r.width - 0.5).toFixed(3));
    el.style.setProperty("--my", ((e.clientY - r.top) / r.height - 0.5).toFixed(3));
  };

  return (
    <section id="top" className="hero" ref={ref} onMouseMove={onMove}>
      <div className="blob b1" /><div className="blob b2" /><div className="blob b3" />
      <div className="container hero-grid">
        <div className="hero-copy">
          <span className="eyebrow fade-up" style={{ "--i": 0 }}><Icon name="spark" size={14} /> Data science meets dinner</span>
          <h1 className="fade-up" style={{ "--i": 1 }}>
            Find Pune&rsquo;s best bites, <span className="grad-text">ranked honestly.</span>
          </h1>
          <p className="lead fade-up" style={{ "--i": 2 }}>
            We analysed <b>{overview.restaurants.toLocaleString("en-IN")}</b> Zomato listings across {overview.localities} localities
            to show what really drives a great rating &mdash; and to uncover the places hiding in plain sight.
          </p>
          <div className="cta fade-up" style={{ "--i": 3 }}>
            <a className="btn primary" href="#/gems"><Icon name="gem" size={18} /> Discover hidden gems</a>
            <a className="btn ghost" href="#/localities">Explore localities <Icon name="arrow" size={18} /></a>
          </div>
          <dl className="hero-stats fade-up" style={{ "--i": 4 }}>
            <div><dt><CountUp to={overview.rated} /></dt><dd>rated restaurants</dd></div>
            <div><dt><CountUp to={overview.localities} /></dt><dd>localities</dd></div>
            <div><dt><CountUp to={overview.gems} /></dt><dd>hidden gems found</dd></div>
          </dl>
        </div>

        <div className="hero-art fade-up" style={{ "--i": 2 }}>
          <div className="ring-deco" />
          <div className="art-layer far"><HeroThali /></div>
          <div className="chip c1 art-layer near">
            <span className="chip-ico"><Icon name="gem" size={16} /></span>
            <div><b>{gem.name.length > 22 ? gem.name.slice(0, 21) + "…" : gem.name}</b><small>Hidden gem · {gem.locality}</small></div>
            <em><Star size={13} /> {gem.rating.toFixed(1)}</em>
          </div>
          <div className="chip c2 art-layer mid">
            <span className="chip-ico alt"><Icon name="trend" size={16} /></span>
            <div><b>{best.name}</b><small>Top-rated area</small></div>
            <em><Star size={13} /> {best.avg.toFixed(2)}</em>
          </div>
          <div className="chip c3 art-layer mid">
            <span className="chip-ico green"><Icon name="check" size={16} /></span>
            <div><b>Only {overview.pctHigh}%</b><small>reach 4.0 or higher</small></div>
          </div>
        </div>
      </div>
      <a className="scroll-cue" href="#overview" aria-label="Scroll down" onClick={(e) => { e.preventDefault(); document.getElementById("overview")?.scrollIntoView({ behavior: "smooth" }); }}><span /></a>
    </section>
  );
}
