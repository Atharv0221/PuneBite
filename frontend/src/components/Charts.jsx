import { useState } from "react";
import { Reveal, SectionHead } from "../ui.jsx";
import { useReveal } from "../hooks.js";

function RatingHistogram({ data, pctHigh }) {
  const [ref, vis] = useReveal(0.25);
  const [hover, setHover] = useState(null);
  const W = 560, H = 270, pad = { l: 8, r: 8, t: 20, b: 38 };
  const max = Math.max(...data.map((d) => d.count));
  const bw = (W - pad.l - pad.r) / data.length;
  const x4 = pad.l + data.findIndex((d) => d.lo >= 4) * bw;

  return (
    <div className={`chart-wrap ${vis ? "in" : ""}`} ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} className="hist" role="img" aria-label="Distribution of restaurant ratings">
        <defs>
          <linearGradient id="barHi" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#FF9A3C" /><stop offset="1" stopColor="#E8336D" /></linearGradient>
        </defs>
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line key={f} x1={pad.l} x2={W - pad.r} y1={H - pad.b - f * (H - pad.b - pad.t)} y2={H - pad.b - f * (H - pad.b - pad.t)} className="grid-line" />
        ))}
        {data.map((d, i) => {
          const h = (d.count / max) * (H - pad.b - pad.t);
          const x = pad.l + i * bw + 3, y = H - pad.b - h;
          const hi = d.lo >= 4;
          return (
            <g key={i} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <rect className="bar-hit" x={pad.l + i * bw} y={pad.t} width={bw} height={H - pad.t - pad.b} fill="transparent" />
              <rect className={`bar ${hi ? "hi" : ""} ${hover === i ? "hot" : ""}`} x={x} y={y} width={bw - 6} height={h} rx="5"
                    fill={hi ? "url(#barHi)" : undefined} style={{ "--i": i, transformOrigin: `${x + (bw - 6) / 2}px ${H - pad.b}px` }} />
              {i % 2 === 0 && <text x={pad.l + i * bw + bw / 2} y={H - 14} textAnchor="middle" className="axis">{d.lo.toFixed(1)}</text>}
            </g>
          );
        })}
        <line x1={x4} x2={x4} y1={pad.t - 6} y2={H - pad.b} className="mark-line" />
        <text x={x4 + 8} y={pad.t + 6} className="mark-text">4.0+ · only {pctHigh}%</text>
      </svg>
      {hover !== null && (
        <div className="tip" style={{ left: `${((pad.l + hover * bw + bw / 2) / W) * 100}%` }}>
          <b>{data[hover].count.toLocaleString("en-IN")}</b> restaurants<br />
          rated {data[hover].lo.toFixed(1)}–{data[hover].hi.toFixed(1)}
        </div>
      )}
    </div>
  );
}

const PALETTE = ["#FF5A36", "#FF9A3C", "#F5B301", "#1FA971", "#2F9BE8", "#8B5CF6", "#9AA4B2"];

function TypeDonut({ data }) {
  const [ref, vis] = useReveal(0.25);
  const [hover, setHover] = useState(null);
  const total = data.reduce((s, d) => s + d.count, 0);
  const r = 74, C = 2 * Math.PI * r;
  let acc = 0;
  return (
    <div className="donut-box" ref={ref}>
      <div className="donut">
        <svg viewBox="0 0 200 200" role="img" aria-label="Share of restaurant types">
          <circle cx="100" cy="100" r={r} fill="none" className="ring-track" strokeWidth="26" />
          {data.map((d, i) => {
            const len = (d.count / total) * C;
            const off = -acc; acc += len;
            return (
              <circle key={d.name} cx="100" cy="100" r={r} fill="none" stroke={PALETTE[i % PALETTE.length]} strokeWidth={hover === i ? 32 : 26}
                      strokeDasharray={`${vis ? Math.max(0, len - 2) : 0} ${C}`} strokeDashoffset={off} transform="rotate(-90 100 100)"
                      className="seg" style={{ transitionDelay: `${i * 90}ms`, opacity: hover === null || hover === i ? 1 : 0.35 }}
                      onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} />
            );
          })}
        </svg>
        <div className="donut-center">
          <b>{hover === null ? total.toLocaleString("en-IN") : data[hover].count.toLocaleString("en-IN")}</b>
          <span>{hover === null ? "restaurants" : data[hover].name}</span>
        </div>
      </div>
      <ul className="legend">
        {data.map((d, i) => (
          <li key={d.name} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} className={hover === i ? "on" : ""}>
            <i style={{ background: PALETTE[i % PALETTE.length] }} />
            <span>{d.name}</span>
            <em>{Math.round((d.count / total) * 100)}%</em>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Charts({ ratingHist, typeShare, overview }) {
  return (
    <section className="section tight">
      <div className="container">
        <SectionHead eyebrow="The big picture" title="How Pune rates its restaurants"
          sub="Most ratings crowd into a narrow band, and the very best places are rare. That is exactly why a smarter ranking matters." />
        <div className="grid-2 charts">
          <Reveal className="card chart-card">
            <h3>Rating distribution</h3>
            <p className="muted">Number of restaurants in each 0.2-star band</p>
            <RatingHistogram data={ratingHist} pctHigh={overview.pctHigh} />
          </Reveal>
          <Reveal delay={120} className="card chart-card">
            <h3>What kind of places are they?</h3>
            <p className="muted">Share of listings by restaurant type</p>
            <TypeDonut data={typeShare} />
          </Reveal>
        </div>
      </div>
    </section>
  );
}
