import { CountUp, Icon, Reveal } from "../ui.jsx";

export default function Kpis({ overview }) {
  const items = [
    { icon: "store", label: "Restaurants analysed", node: <CountUp to={overview.restaurants} />, note: "after removing duplicates" },
    { icon: "users", label: "With a real rating", node: <CountUp to={overview.rated} />, note: "the rest have no reviews yet" },
    { icon: "trend", label: "Average rating", node: <CountUp to={overview.avgRating} decimals={2} suffix={<span className="gold"> ★</span>} />, note: "across all rated places" },
    { icon: "gem", label: "Rated 4.0 or higher", node: <CountUp to={overview.pctHigh} decimals={1} suffix="%" />, note: "a rare club to join" },
  ];
  return (
    <section id="overview" className="section">
      <div className="container kpis">
        {items.map((k, i) => (
          <Reveal key={k.label} delay={i * 90} className="card kpi">
            <span className="kpi-ico"><Icon name={k.icon} size={22} /></span>
            <strong>{k.node}</strong>
            <span className="kpi-label">{k.label}</span>
            <small>{k.note}</small>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
