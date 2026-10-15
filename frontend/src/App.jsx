import { useData, useRoute, useScroll, useTheme } from "./hooks.js";
import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import Kpis from "./components/Kpis.jsx";
import Charts from "./components/Charts.jsx";
import Marquee from "./components/Marquee.jsx";
import Localities from "./components/Localities.jsx";
import Gems from "./components/Gems.jsx";
import Advisor from "./components/Advisor.jsx";
import Insights from "./components/Insights.jsx";
import Footer from "./components/Footer.jsx";

// One page per route (hash based, so it also works on any static host).
const PAGES = {
  "/": (d) => (
    <>
      <Hero overview={d.overview} gems={d.gems} insights={d.insights} />
      <Kpis overview={d.overview} />
      <Charts ratingHist={d.ratingHist} typeShare={d.typeShare} overview={d.overview} />
      <Marquee cuisines={d.cuisines} />
    </>
  ),
  "/localities": (d) => <Localities localities={d.localities} gems={d.gems} overview={d.overview} />,
  "/gems": (d) => <Gems gems={d.gems} />,
  "/advisor": (d) => <Advisor overview={d.overview} />,
  "/insights": (d) => <Insights insights={d.insights} votesCurve={d.votesCurve} overview={d.overview} />,
};

export default function App() {
  const { theme, toggle } = useTheme();
  const { scrolled, progress } = useScroll();
  const data = useData();
  const path = useRoute();
  const page = PAGES[path] ?? PAGES["/"];

  return (
    <>
      <Navbar theme={theme} toggleTheme={toggle} source={data.source} active={PAGES[path] ? path : "/"} scrolled={scrolled} progress={progress} />
      <main key={path} className={`page ${path === "/" ? "page-home" : "page-inner"}`}>{page(data)}</main>
      <Footer />
    </>
  );
}
