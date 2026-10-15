import { useState } from "react";
import { Icon } from "../ui.jsx";
import { Logo } from "./Art.jsx";

export const NAV = [
  ["/", "Home"],
  ["/localities", "Localities"],
  ["/gems", "Hidden Gems"],
  ["/advisor", "Opening Advisor"],
  ["/insights", "Insights"],
];

export default function Navbar({ theme, toggleTheme, source, active, scrolled, progress }) {
  const [open, setOpen] = useState(false);
  return (
    <header className={`nav ${scrolled ? "scrolled" : ""}`}>
      <div className="progress" style={{ transform: `scaleX(${progress})` }} />
      <div className="container nav-inner">
        <a className="brand" href="#/" aria-label="PuneBite home">
          <Logo /> <span>Pune<b>Bite</b></span>
        </a>

        <nav className={`nav-links ${open ? "open" : ""}`} aria-label="Primary">
          {NAV.map(([id, label]) => (
            <a key={id} href={`#${id}`} className={active === id ? "active" : ""} onClick={() => setOpen(false)}>
              {label}
            </a>
          ))}
        </nav>

        <div className="nav-actions">
          <span className={`pill source ${source}`} title={source === "live" ? "Connected to the Flask API" : "Showing demo data built from the project dataset"}>
            <i /> {source === "live" ? "Live API" : "Demo data"}
          </span>
          <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle dark mode">
            <span className={`swap ${theme}`}>
              <Icon name="sun" className="i-sun" /><Icon name="moon" className="i-moon" />
            </span>
          </button>
          <button className="icon-btn menu-btn" onClick={() => setOpen((o) => !o)} aria-label="Menu" aria-expanded={open}>
            <Icon name={open ? "close" : "menu"} />
          </button>
        </div>
      </div>
    </header>
  );
}
