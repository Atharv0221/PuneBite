import useFetch, { Status } from "./useFetch.jsx";
import Bars from "../Bars.jsx";

const title = (k) => k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());

// Turns whatever /api/stats/overview returns into tiles + bar charts:
// numbers -> tiles; {label: number} or [{label|name, value|count}] -> bar chart.
function toBars(v) {
  if (Array.isArray(v)) {
    return v
      .map((r) => ({
        label: String(r.label ?? r.name ?? r.bin ?? r.cuisine ?? r.type ?? r.band ?? r.key ?? r._id ?? ""),
        value: Number(r.count ?? r.value ?? 0),
      }))
      .filter((r) => r.label);
  }
  return Object.entries(v)
    .filter(([, n]) => typeof n === "number")
    .map(([label, value]) => ({ label, value }));
}

export default function Overview() {
  const { data, error, loading } = useFetch("/api/stats/overview");
  if (!data) return <Status loading={loading} error={error} />;

  const tiles = Object.entries(data).filter(([, v]) => typeof v === "number");
  const charts = Object.entries(data)
    .filter(([, v]) => v && typeof v === "object")
    .map(([k, v]) => [k, toBars(v).slice(0, 12)])
    .filter(([, b]) => b.length);

  return (
    <>
      <h2>Pune restaurants at a glance</h2>
      <section className="tiles">
        {tiles.map(([k, v]) => (
          <div className="tile" key={k}>
            <b>{k.endsWith("share") ? `${(v * 100).toFixed(1)}%` : Number.isInteger(v) ? v.toLocaleString("en-IN") : v.toFixed(2)}</b>
            <span>{title(k)}</span>
          </div>
        ))}
      </section>
      <section className="grid">
        {charts.map(([k, bars]) => (
          <div className="panel" key={k}>
            <h3>{title(k)}</h3>
            <Bars data={bars} />
          </div>
        ))}
      </section>
    </>
  );
}
