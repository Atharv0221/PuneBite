// Dependency-free horizontal bar chart. data = [{label, value}]
export default function Bars({ data, unit = "", max }) {
  const top = max ?? Math.max(...data.map((d) => d.value), 1);
  return (
    <ul className="bars">
      {data.map((d) => (
        <li key={d.label}>
          <span className="bars-label" title={d.label}>{d.label}</span>
          <span className="bars-track">
            <span className="bars-fill" style={{ width: `${(d.value / top) * 100}%` }} />
          </span>
          <span className="bars-val">{Number.isInteger(d.value) ? d.value : d.value.toFixed(2)}{unit}</span>
        </li>
      ))}
    </ul>
  );
}
