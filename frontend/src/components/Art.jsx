// Hand-drawn SVG artwork (no external image files needed).

export function Logo({ size = 34 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <defs>
        <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FF9A3C" /><stop offset="1" stopColor="#E8336D" />
        </linearGradient>
      </defs>
      <rect width="40" height="40" rx="12" fill="url(#lg)" />
      <path d="M13 11v8a3 3 0 0 0 3 3v7M16 11v8M19 11v8a3 3 0 0 1-3 3" stroke="#fff" strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M26 11c-3 2-3 8 0 10v8" stroke="#fff" strokeWidth="2" strokeLinecap="round" fill="none" />
    </svg>
  );
}

// tiny deterministic pseudo-random so the rice grains never change between renders
const rng = (seed) => () => (seed = (seed * 16807) % 2147483647) / 2147483647;

export function HeroThali() {
  const R = 130, cx = 250, cy = 250;
  const bowls = [
    { a: -90, color: "#E8590C", swirl: "#FFD8A8" },   // curry
    { a: -18, color: "#F2B01E", swirl: "#FFF3BF" },   // dal
    { a: 54, color: "#2F9E44", swirl: "#B2F2BB" },    // palak
    { a: 126, color: "#C92A2A", swirl: "#FFC9C9" },   // tomato gravy
    { a: 198, color: "#F1F3F5", swirl: "#CED4DA" },   // raita
  ];
  const rand = rng(42);
  const grains = Array.from({ length: 70 }, () => {
    const t = rand() * Math.PI * 2, d = Math.sqrt(rand()) * 46;
    return { x: cx + d * Math.cos(t), y: cy + d * Math.sin(t), r: rand() * 40 };
  });

  return (
    <svg className="thali" viewBox="0 0 500 500" role="img" aria-label="Illustration of an Indian thali">
      <defs>
        <radialGradient id="plate" cx="50%" cy="40%" r="70%">
          <stop offset="0" stopColor="#FFFFFF" /><stop offset="1" stopColor="#DCE3EC" />
        </radialGradient>
        <linearGradient id="steel" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#F8FAFC" /><stop offset="1" stopColor="#AEB8C5" />
        </linearGradient>
        <radialGradient id="rice" cx="40%" cy="35%" r="70%">
          <stop offset="0" stopColor="#FFFFFF" /><stop offset="1" stopColor="#F3EBD8" />
        </radialGradient>
        <filter id="soft" x="-20%" y="-20%" width="140%" height="150%">
          <feDropShadow dx="0" dy="14" stdDeviation="14" floodColor="#7a3410" floodOpacity="0.28" />
        </filter>
      </defs>

      {/* decorations that stay still around the plate */}
      <g>
        <g transform="translate(432 96)">
          <circle r="30" fill="#FFD43B" /><circle r="25" fill="#FFE066" />
          {[0, 60, 120, 180, 240, 300].map((d) => (
            <path key={d} d="M0 0 L0 -23" stroke="#FFF3BF" strokeWidth="2.5" transform={`rotate(${d})`} />
          ))}
        </g>
        <g transform="translate(62 410) rotate(-30)">
          <path d="M0 0c14-18 40-14 52 6-18 6-38 8-52-6z" fill="#2F9E44" />
          <path d="M6 2c14-4 28-2 40 4" stroke="#8CE99A" strokeWidth="2" fill="none" />
        </g>
        <g transform="translate(78 92) rotate(20)">
          <path d="M0 0c14-18 40-14 52 6-18 6-38 8-52-6z" fill="#40C057" />
        </g>
        <path d="M418 428c22-4 36 8 40 26-18 4-36-6-40-26z" fill="#E03131" />
        <path d="M418 428c-6-8-4-14 2-18" stroke="#2F9E44" strokeWidth="3" fill="none" strokeLinecap="round" />
      </g>

      <g className="thali-spin" filter="url(#soft)">
        <circle cx={cx} cy={cy} r="212" fill="url(#plate)" />
        <circle cx={cx} cy={cy} r="196" fill="none" stroke="#C5CDD8" strokeWidth="2" />
        <circle cx={cx} cy={cy} r="186" fill="#EEF2F7" />

        {bowls.map((b, i) => {
          const x = cx + R * Math.cos((b.a * Math.PI) / 180), y = cy + R * Math.sin((b.a * Math.PI) / 180);
          return (
            <g key={i} transform={`translate(${x} ${y})`}>
              <circle r="56" fill="url(#steel)" />
              <circle r="47" fill="#8C97A6" />
              <circle r="43" fill={b.color} />
              <path d={`M-22 6c8-18 30-18 38 0`} stroke={b.swirl} strokeWidth="5" strokeLinecap="round" fill="none" opacity=".7" />
              <path d={`M-12 20c6-8 18-8 24 0`} stroke={b.swirl} strokeWidth="4" strokeLinecap="round" fill="none" opacity=".55" />
              <ellipse cx="-16" cy="-22" rx="14" ry="6" fill="#fff" opacity=".35" transform="rotate(-30 -16 -22)" />
            </g>
          );
        })}

        <circle cx={cx} cy={cy} r="62" fill="url(#rice)" stroke="#E7DDC4" strokeWidth="2" />
        {grains.map((g, i) => (
          <ellipse key={i} cx={g.x} cy={g.y} rx="5" ry="2" fill="#E9DFC6" transform={`rotate(${g.r * 4.5} ${g.x} ${g.y})`} />
        ))}
        <path d="M236 232c8-14 26-14 34-2-10 10-26 14-34 2z" fill="#37B24D" />
        <path d="M242 232c8-4 16-4 24 0" stroke="#B2F2BB" strokeWidth="2" fill="none" />
      </g>
    </svg>
  );
}

export function Skyline() {
  const b = [
    [0, 50, 60], [50, 40, 95], [90, 55, 70], [145, 36, 120], [181, 60, 80], [241, 46, 105], [287, 70, 64],
    [357, 40, 130], [397, 56, 88], [453, 44, 108], [497, 64, 72], [561, 40, 118], [601, 58, 92], [659, 48, 70],
    [707, 62, 112], [769, 44, 84], [813, 56, 126], [869, 48, 76], [917, 60, 100], [977, 44, 68], [1021, 62, 114], [1083, 50, 82], [1133, 67, 96],
  ];
  const domes = [145, 413, 707, 1021];
  return (
    <svg className="skyline" viewBox="0 0 1200 170" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity=".28" /><stop offset="1" stopColor="currentColor" stopOpacity=".06" />
        </linearGradient>
      </defs>
      <path d="M0 150 C150 90 260 130 380 110 S620 70 760 105 S1040 80 1200 120 V170 H0Z" fill="currentColor" opacity=".08" />
      {b.map(([x, w, h], i) => (
        <g key={i}>
          <rect x={x} y={170 - h} width={w} height={h} fill="url(#sky)" />
          {domes.includes(x) && <path d={`M${x + 4} ${170 - h} a${(w - 8) / 2} ${(w - 8) / 2} 0 0 1 ${w - 8} 0z`} fill="url(#sky)" />}
          {domes.includes(x) && <rect x={x + w / 2 - 1} y={170 - h - w / 2 - 14} width="2" height="14" fill="currentColor" opacity=".3" />}
        </g>
      ))}
    </svg>
  );
}
