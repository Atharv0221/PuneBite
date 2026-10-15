import { Reveal, Ring, SectionHead } from "../ui.jsx";
import { useReveal } from "../hooks.js";

function VotesLine({ data }) {
  const [ref, vis] = useReveal(0.3);
  const W = 420, H = 200, p = { l: 34, r: 14, t: 16, b: 34 };
  const lo = 2.9, hi = 4.3;
  const pts = data.map((d, i) => [p.l + (i / (data.length - 1)) * (W - p.l - p.r), p.t + (1 - (d.avg - lo) / (hi - lo)) * (H - p.t - p.b)]);
  const path = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  return (
    <div ref={ref} className={`viz ${vis ? "in" : ""}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Average rating rises with the number of votes">
        {[3, 3.5, 4].map((v) => {
          const y = p.t + (1 - (v - lo) / (hi - lo)) * (H - p.t - p.b);
          return <g key={v}><line x1={p.l} x2={W - p.r} y1={y} y2={y} className="grid-line" /><text x="4" y={y + 4} className="axis">{v.toFixed(1)}</text></g>;
        })}
        <path d={path} pathLength="1" className="line-path" />
        {pts.map(([x, y], i) => (
          <g key={i}>
            <circle cx={x} cy={y} r="4.5" className="line-dot" style={{ transitionDelay: `${600 + i * 70}ms` }} />
            {(i === 0 || i === data.length - 1 || i === 5) && <text x={x} y={H - 12} textAnchor={i === 0 ? "start" : i === data.length - 1 ? "end" : "middle"} className="axis">{data[i].band}</text>}
          </g>
        ))}
      </svg>
      <small className="muted">Average rating by number of reviews</small>
    </div>
  );
}

function PairBars({ rows }) {
  const [ref, vis] = useReveal(0.3);
  const lo = 3.0, hi = 4.1;
  return (
    <div ref={ref} className={`viz pairs ${vis ? "in" : ""}`}>
      {rows.map((r, ri) => (
        <div className="pair" key={r.title}>
          <span className="pair-title">{r.title}</span>
          {[["With", r.a, "a"], ["Without", r.b, "b"]].map(([l, v, k], i) => (
            <div className="hbar" key={l}>
              <em>{l}</em>
              <div><span className={k} style={{ "--w": `${((v - lo) / (hi - lo)) * 100}%`, transitionDelay: `${(ri * 2 + i) * 120}ms` }} /></div>
              <b>{v.toFixed(2)}</b>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function LocBars({ best, worst, avg }) {
  const [ref, vis] = useReveal(0.3);
  const lo = 3.0, hi = 3.9;
  const rows = [...best.map((x) => ({ ...x, k: "a" })), ...worst.slice().reverse().map((x) => ({ ...x, k: "b" }))];
  return (
    <div ref={ref} className={`viz locbars ${vis ? "in" : ""}`}>
      {rows.map((r, i) => (
        <div className="hbar" key={r.name}>
          <em>{r.name}</em>
          <div><span className={r.k} style={{ "--w": `${((r.avg - lo) / (hi - lo)) * 100}%`, transitionDelay: `${i * 80}ms` }} /><i style={{ left: `${((avg - lo) / (hi - lo)) * 100}%` }} /></div>
          <b>{r.avg.toFixed(2)}</b>
        </div>
      ))}
    </div>
  );
}

export default function Insights({ insights, votesCurve, overview }) {
  const { outdoor, booking, best, worst, auc, r2 } = insights;
  const cards = [
    {
      tag: "Popularity", title: "Reviews change the rating you see",
      text: "Places with only a handful of votes sit near 3.0, while heavily reviewed ones average above 4. A star rating is only half the story without the review count.",
      viz: <VotesLine data={votesCurve} />,
    },
    {
      tag: "Confounding", title: "Outdoor seating? Not so fast.",
      text: `Outdoor seating looks linked to higher ratings overall, but the gap vanishes once we compare restaurants with 50+ votes. Table booking, by contrast, stays strongly linked to quality.`,
      viz: <PairBars rows={[
        { title: "Outdoor seating · all restaurants", a: outdoor.overall[0], b: outdoor.overall[1] },
        { title: "Outdoor seating · 50+ votes", a: outdoor.popular[0], b: outdoor.popular[1] },
        { title: "Table booking · 50+ votes", a: booking.popular[0], b: booking.popular[1] },
      ]} />,
    },
    {
      tag: "Location", title: "Where you open matters",
      text: "A statistical test confirms that locality and rating tier are related. The best and weakest areas differ by about half a star on average.",
      viz: <LocBars best={best} worst={worst} avg={overview.avgRating} />,
    },
    {
      tag: "Prediction", title: "Predicting a newcomer is hard",
      text: "With review counts, our model separates top-rated places well. Without them (a brand-new restaurant) it can rank, but not guarantee. Food and service quality are invisible to the data.",
      viz: (
        <div className="viz rings">
          <div><Ring value={auc.withVotes} size={116} stroke={11}><b>{auc.withVotes.toFixed(2)}</b></Ring><span>AUC with votes</span></div>
          <div><Ring value={auc.noVotes} size={116} stroke={11} from="#8B5CF6" to="#E8336D"><b>{auc.noVotes.toFixed(2)}</b></Ring><span>AUC for new restaurants</span></div>
        </div>
      ),
    },
  ];
  return (
    <section id="insights" className="section alt">
      <div className="container">
        <SectionHead eyebrow="What the data says" title="Four things we learned" sub="Short stories from the statistics and machine-learning notebooks behind this dashboard." />
        <div className="grid-2 insight-grid">
          {cards.map((c, i) => (
            <Reveal key={c.title} delay={(i % 2) * 120} className="card insight">
              <span className="tag">{c.tag}</span>
              <h3>{c.title}</h3>
              <p>{c.text}</p>
              {c.viz}
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
