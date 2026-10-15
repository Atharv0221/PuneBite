import { useId } from "react";
import { useCountUp, useReveal } from "./hooks.js";

export function Reveal({ as: Tag = "div", delay = 0, className = "", style, children, ...rest }) {
  const [ref, vis] = useReveal();
  return (
    <Tag ref={ref} className={`reveal ${vis ? "in" : ""} ${className}`} style={{ "--d": `${delay}ms`, ...style }} {...rest}>
      {children}
    </Tag>
  );
}

export function CountUp({ to, decimals = 0, prefix = "", suffix = "" }) {
  const [ref, vis] = useReveal(0.4);
  const v = useCountUp(to, { start: vis, decimals });
  return <span ref={ref}>{prefix}{v}{suffix}</span>;
}

const PATHS = {
  search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
  sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>,
  moon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />,
  pin: <><path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21z" /><circle cx="12" cy="9.5" r="2.5" /></>,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  close: <path d="M6 6l12 12M18 6L6 18" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  gem: <><path d="M6 3h12l4 6-10 12L2 9z" /><path d="M2 9h20M9 3l-2 6 5 12 5-12-2-6" /></>,
  trend: <><path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" /></>,
  store: <><path d="M3 9l1.5-5h15L21 9" /><path d="M4 9v11h16V9" /><path d="M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0" /></>,
  check: <path d="M5 12l5 5 9-10" />,
  external: <path d="M14 4h6v6M20 4l-9 9M18 14v6H4V6h6" />,
  spark: <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />,
  users: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" /><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14c2.2.6 3.5 2.5 3.5 6" /></>,
};

export function Icon({ name, size = 20, className = "" }) {
  return (
    <svg className={`icon ${className}`} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {PATHS[name]}
    </svg>
  );
}

export function Star({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" className="star-ico">
      <path fill="currentColor" d="M12 2.5l2.9 6.1 6.6.8-4.9 4.6 1.3 6.5L12 17.2 6.1 20.5l1.3-6.5L2.5 9.4l6.6-.8z" />
    </svg>
  );
}

/** Circular gauge. `value`/`max` = filled fraction. `marker` (0..1) draws a small reference dot. */
export function Ring({ value, max = 1, size = 120, stroke = 10, marker, children, from = "#FF9A3C", to = "#FF5A36" }) {
  const gid = "g" + useId().replace(/[^a-zA-Z0-9]/g, "");
  const r = (size - stroke) / 2, c = 2 * Math.PI * r, cx = size / 2;
  const frac = Math.min(1, Math.max(0, value / max));
  let dot = null;
  if (marker !== undefined) {
    const th = marker * 2 * Math.PI - Math.PI / 2;
    dot = <circle className="ring-marker" cx={cx + r * Math.cos(th)} cy={cx + r * Math.sin(th)} r={stroke / 2 + 2} />;
  }
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
        <defs>
          <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={from} />
            <stop offset="100%" stopColor={to} />
          </linearGradient>
        </defs>
        <circle className="ring-track" cx={cx} cy={cx} r={r} strokeWidth={stroke} fill="none" />
        <circle className="ring-bar" cx={cx} cy={cx} r={r} strokeWidth={stroke} fill="none" stroke={`url(#${gid})`}
                strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - frac)}
                transform={`rotate(-90 ${cx} ${cx})`} />
        {dot}
      </svg>
      <div className="ring-center">{children}</div>
    </div>
  );
}

export function SectionHead({ eyebrow, title, sub, align = "left" }) {
  return (
    <Reveal className={`section-head ${align}`}>
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      {sub && <p>{sub}</p>}
    </Reveal>
  );
}

const EMOJI = [
  ["biryani", "🍛"], ["north indian", "🍛"], ["south indian", "🥘"], ["chinese", "🥡"], ["fast food", "🍔"],
  ["street", "🌮"], ["maharashtrian", "🥘"], ["mughlai", "🍢"], ["dessert", "🍰"], ["bakery", "🥐"],
  ["cafe", "☕"], ["café", "☕"], ["italian", "🍝"], ["pizza", "🍕"], ["continental", "🥗"], ["beverage", "🥤"],
  ["seafood", "🦐"], ["ice cream", "🍨"], ["sandwich", "🥪"], ["asian", "🍜"], ["healthy", "🥑"], ["bar", "🍸"],
  ["lounge", "🍹"], ["takeaway", "🥡"], ["delivery", "🛵"], ["food court", "🍱"], ["quick", "🥪"], ["casual", "🍽️"],
];
export const emojiFor = (name = "") => {
  const n = name.toLowerCase();
  const hit = EMOJI.find(([k]) => n.includes(k));
  return hit ? hit[1] : "🍽️";
};

export const rupees = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
// curated warm/jewel hues so every generated card still matches the brand palette
const HUES = [6, 18, 30, 42, 338, 322, 276, 204, 168];
export const hueOf = (s) => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return HUES[h % HUES.length]; };
export const pickOf = (s, list) => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 33 + s.charCodeAt(i)) >>> 0; return list[h % list.length]; };
