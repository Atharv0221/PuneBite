import { useEffect, useRef, useState } from "react";
import { api, fmtRating, fmtCost } from "../api.js";

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
  text: "Hi! Ask me about Pune restaurants. I understand locality, cuisine, price, rating, veg, amenities and type.",
  chips: [],
  cards: [],
};

function Card({ r }) {
  return (
    <article className="panel gem">
      <h3>
        {r.url ? <a href={r.url} target="_blank" rel="noreferrer">{r.name}</a> : r.name}
        {r.hidden_gem && <span className="chip gemchip">hidden gem</span>}
      </h3>
      <p>{r.locality} · {r.establishment_type}</p>
      <p>
        <b>{fmtRating(r.trust_rating)}</b> trust-adjusted · {fmtRating(r.rating)} from {r.votes ?? 0} votes · {fmtCost(r.cost_for_two)} for two
      </p>
      <p className="note">{(r.cuisines || []).slice(0, 4).join(", ")}</p>
    </article>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages, busy]);

  async function send(text) {
    const message = text.trim();
    if (!message || busy) return;
    setMessages((m) => [...m, { from: "user", text: message }]);
    setInput("");
    setBusy(true);
    try {
      const r = await api("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      setMessages((m) => [...m, { from: "bot", text: r.reply, chips: r.understood || [], cards: r.restaurants || [] }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { from: "bot", text: `${e.message}. Check that the Flask API is running on port 5000.`, chips: [], cards: [], error: true },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h2>Restaurant chatbot</h2>
      <p className="note">
        A keyword-based assistant: it reads your sentence with fixed rules and searches the MongoDB data. Results are ranked by trust-adjusted rating.
      </p>

      <div className="chat-log panel" ref={logRef} role="log" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.from}${m.error ? " err" : ""}`}>
            <p>{m.text}</p>
            {m.chips?.length > 0 && (
              <p className="chips" aria-label="What I understood">
                {m.chips.map((c) => <span className="chip" key={c}>{c}</span>)}
              </p>
            )}
            {m.cards?.length > 0 && <div className="grid chat-cards">{m.cards.map((r, j) => <Card key={r.url ?? j} r={r} />)}</div>}
          </div>
        ))}
        {busy && <div className="bubble bot"><p className="note">Searching…</p></div>}
      </div>

      <div className="examples" aria-label="Example questions">
        {EXAMPLES.map((q) => (
          <button key={q} className="chip btn" onClick={() => send(q)} disabled={busy}>{q}</button>
        ))}
      </div>

      <form className="filters" onSubmit={(e) => { e.preventDefault(); send(input); }}>
        <label className="sr" htmlFor="chat-input">Your question</label>
        <input
          id="chat-input"
          placeholder="e.g. best cheap biryani in Kothrud"
          value={input}
          maxLength={300}
          onChange={(e) => setInput(e.target.value)}
          autoComplete="off"
        />
        <button className="primary" disabled={busy || !input.trim()}>Send</button>
      </form>
    </>
  );
}
