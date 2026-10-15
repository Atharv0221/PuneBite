import { useEffect, useRef, useState } from "react";
import { chat } from "../api.js";
import { Icon, SectionHead, Star, emojiFor, rupees } from "../ui.jsx";

const EXAMPLES = [
  "best cheap biryani in Kothrud",
  "veg restaurants in Baner under 500",
  "hidden gems in Viman Nagar",
  "top 3 cafes with wifi in Koregaon Park",
  "pubs with live music in Baner",
  "how many Chinese places in Hadapsar",
];

const WELCOME = {
  from: "bot",
  text: "Hi! Ask me about Pune restaurants. I understand locality, cuisine, price, rating, veg, amenities and restaurant type.",
};

function ResultCard({ r }) {
  const cuisines = Array.isArray(r.cuisines) ? r.cuisines.slice(0, 3).join(", ") : "";
  const shown = r.trust_rating ?? r.rating;
  const title = r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.name}</a> : r.name;
  return (
    <article className="chat-card">
      <span className="chat-emoji" aria-hidden="true">{emojiFor(`${cuisines} ${r.establishment_type || ""}`)}</span>
      <div>
        <h4>{title} {r.hidden_gem && <span className="chip-soft sm">💎 hidden gem</span>}</h4>
        <p className="muted">{[r.locality, r.establishment_type, cuisines].filter(Boolean).join(" · ")}</p>
        <p className="chat-meta">
          {shown != null && <span><Star size={14} /> <b>{Number(shown).toFixed(1)}</b>{r.trust_rating != null ? " trust-adjusted" : ""}</span>}
          {r.votes != null && <span>{Number(r.votes).toLocaleString("en-IN")} votes</span>}
          {(r.cost_for_two ?? r.cost_capped) != null && <span>{rupees(r.cost_for_two ?? r.cost_capped)} for two</span>}
        </p>
      </div>
    </article>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" }); }, [messages, busy]);

  async function send(text) {
    const message = text.trim();
    if (!message || busy) return;
    setMessages((m) => [...m, { from: "user", text: message }]);
    setInput("");
    setBusy(true);
    try {
      const r = await chat(message);
      setMessages((m) => [...m, { from: "bot", text: r.reply, chips: r.understood || [], cards: r.restaurants || [] }]);
    } catch (e) {
      setMessages((m) => [...m, { from: "bot", text: e.message, error: true }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="section">
      <div className="container chat-wrap">
        <SectionHead
          eyebrow="Chatbot"
          title="Ask PuneBite"
          sub="A keyword-based assistant (no AI model): it reads your sentence with fixed rules and searches the MongoDB data. Results are ranked by trust-adjusted rating."
        />
        <div className="chat-box">
          <div className="chat-log" role="log" aria-live="polite">
            {messages.map((m, i) => (
              <div key={i} className={`bubble ${m.from}${m.error ? " err" : ""}`}>
                <p>{m.text}</p>
                {m.chips?.length > 0 && (
                  <div className="chips" aria-label="What I understood">
                    {m.chips.map((c) => <span className="chip-soft sm" key={c}>{c}</span>)}
                  </div>
                )}
                {m.cards?.length > 0 && <div className="chat-cards">{m.cards.map((r, j) => <ResultCard key={r.url ?? j} r={r} />)}</div>}
              </div>
            ))}
            {busy && <div className="bubble bot"><p className="muted">Searching…</p></div>}
            <div ref={endRef} />
          </div>

          <div className="chips chat-examples" aria-label="Example questions">
            {EXAMPLES.map((q) => (
              <button key={q} className="chip-btn" onClick={() => send(q)} disabled={busy}>{q}</button>
            ))}
          </div>

          <form className="chat-form" onSubmit={(e) => { e.preventDefault(); send(input); }}>
            <label className="sr-only" htmlFor="chat-input">Your question</label>
            <input
              id="chat-input"
              placeholder="e.g. best cheap biryani in Kothrud"
              value={input}
              maxLength={300}
              autoComplete="off"
              onChange={(e) => setInput(e.target.value)}
            />
            <button className="btn primary" disabled={busy || !input.trim()}>Send <Icon name="arrow" size={18} /></button>
          </form>
        </div>
      </div>
    </section>
  );
}
