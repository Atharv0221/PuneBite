import { useState } from "react";
import Overview from "./pages/Overview.jsx";
import Explorer from "./pages/Explorer.jsx";
import Localities from "./pages/Localities.jsx";
import Gems from "./pages/Gems.jsx";
import Predict from "./pages/Predict.jsx";
import Chat from "./pages/Chat.jsx";

const PAGES = [
  ["Overview", Overview],
  ["Explorer", Explorer],
  ["Localities", Localities],
  ["Hidden gems", Gems],
  ["Rating predictor", Predict],
  ["Chatbot", Chat],
];

export default function App() {
  const [page, setPage] = useState(0);
  const Page = PAGES[page][1];
  return (
    <div className="shell">
      <header className="top">
        <h1>PuneBite</h1>
        <nav>
          {PAGES.map(([name], i) => (
            <button key={name} className={i === page ? "on" : ""} onClick={() => setPage(i)}>
              {name}
            </button>
          ))}
        </nav>
      </header>
      <main><Page /></main>
    </div>
  );
}
