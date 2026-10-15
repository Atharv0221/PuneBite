import { useMemo } from "react";
import { useData, useScroll, useScrollSpy, useTheme } from "./hooks.js";
import Navbar, { NAV } from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import Kpis from "./components/Kpis.jsx";
import Charts from "./components/Charts.jsx";
import Marquee from "./components/Marquee.jsx";
import Localities from "./components/Localities.jsx";
import Gems from "./components/Gems.jsx";
import Advisor from "./components/Advisor.jsx";
import Insights from "./components/Insights.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  const { theme, toggle } = useTheme();
  const { scrolled, progress } = useScroll();
  const data = useData();
  const ids = useMemo(() => NAV.map(([id]) => id), []);
  const active = useScrollSpy(useMemo(() => ["top", ...ids], [ids]));

  return (
    <>
      <Navbar theme={theme} toggleTheme={toggle} source={data.source} active={active} scrolled={scrolled} progress={progress} />
      <main>
        <Hero overview={data.overview} gems={data.gems} insights={data.insights} />
        <Kpis overview={data.overview} />
        <Charts ratingHist={data.ratingHist} typeShare={data.typeShare} overview={data.overview} />
        <Marquee cuisines={data.cuisines} />
        <Localities localities={data.localities} gems={data.gems} overview={data.overview} />
        <Gems gems={data.gems} />
        <Advisor overview={data.overview} />
        <Insights insights={data.insights} votesCurve={data.votesCurve} overview={data.overview} />
      </main>
      <Footer />
    </>
  );
}
