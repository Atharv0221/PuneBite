import { Logo, Skyline } from "./Art.jsx";

export default function Footer() {
  return (
    <footer className="footer">
      <Skyline />
      <div className="container foot-grid">
        <div>
          <a className="brand" href="#top"><Logo /> <span>Pune<b>Bite</b></span></a>
          <p className="muted">A data science and machine learning mini-project analysing restaurant ratings across Pune.</p>
        </div>
        <div>
          <h4>Built with</h4>
          <div className="chips">
            {["Python", "scikit-learn", "MongoDB", "Flask", "React"].map((t) => <span className="chip-soft sm" key={t}>{t}</span>)}
          </div>
        </div>
        <div>
          <h4>Data</h4>
          <p className="muted small">Zomato Pune restaurant listings (Kaggle). Ratings are a snapshot in time; statistics show association, not cause.</p>
        </div>
      </div>
      <div className="container copy">PES&rsquo;s Modern College of Engineering · TY B.Tech IT · Data Science &amp; Machine Learning</div>
    </footer>
  );
}
