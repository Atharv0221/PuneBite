import { emojiFor } from "../ui.jsx";

export default function Marquee({ cuisines }) {
  const row = [...cuisines, ...cuisines];
  return (
    <div className="marquee" aria-label="Most common cuisines in Pune">
      <div className="marquee-track">
        {row.map((c, i) => (
          <span className="cuisine-chip" key={i} aria-hidden={i >= cuisines.length}>
            <span className="emo">{emojiFor(c.name)}</span>
            <b>{c.name}</b>
            <small>{c.count.toLocaleString("en-IN")} places{c.avg ? ` · ${c.avg.toFixed(1)}★` : ""}</small>
          </span>
        ))}
      </div>
    </div>
  );
}
