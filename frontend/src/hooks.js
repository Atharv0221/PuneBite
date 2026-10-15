import { useCallback, useEffect, useRef, useState } from "react";
import { loadData } from "./api.js";
import * as demo from "./data/demoData.js";

const reduced = () =>
  typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** True once the element has scrolled into view (fires once). */
export function useReveal(threshold = 0.15) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window)) { setVisible(true); return; }
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold, rootMargin: "0px 0px -6% 0px" }
    );
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);
  return [ref, visible];
}

/** Counts from 0 to `target` when `start` becomes true. */
export function useCountUp(target, { start = true, duration = 1400, decimals = 0 } = {}) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!start) return;
    if (reduced()) { setVal(target); return; }
    let raf, t0;
    const tick = (t) => {
      if (t0 === undefined) t0 = t;
      const p = Math.min(1, (t - t0) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(target * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, start, duration]);
  return decimals > 0 ? val.toFixed(decimals) : Math.round(val).toLocaleString("en-IN");
}

/** Smoothly animates a number whenever `value` changes. */
export function useTween(value, duration = 650) {
  const [v, setV] = useState(value);
  const from = useRef(value);
  useEffect(() => {
    if (reduced()) { setV(value); from.current = value; return; }
    const start = from.current, delta = value - start;
    let raf, t0;
    const tick = (t) => {
      if (t0 === undefined) t0 = t;
      const p = Math.min(1, (t - t0) / duration);
      const e = 1 - Math.pow(1 - p, 3);
      const cur = start + delta * e;
      from.current = cur;
      setV(cur);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return v;
}

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem("pb-theme");
      if (saved) return saved;
    } catch (e) { /* storage unavailable */ }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("pb-theme", theme); } catch (e) { /* ignore */ }
  }, [theme]);
  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  return { theme, toggle };
}

/** Scroll progress (0..1) and "scrolled" flag, throttled with rAF. */
export function useScroll() {
  const [s, setS] = useState({ progress: 0, scrolled: false });
  useEffect(() => {
    let raf = 0;
    const update = () => {
      raf = 0;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setS({ progress: max > 0 ? window.scrollY / max : 0, scrolled: window.scrollY > 12 });
    };
    const onScroll = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => { window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); cancelAnimationFrame(raf); };
  }, []);
  return s;
}

/** Tiny hash router: "#/gems" -> "/gems". Scrolls to the top on every page change. */
export function useRoute() {
  const read = () => (window.location.hash.replace(/^#/, "") || "/");
  const [path, setPath] = useState(read);
  useEffect(() => {
    const onHash = () => { setPath(read()); window.scrollTo({ top: 0, behavior: "instant" }); };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return path;
}

/** 3D tilt + glare following the pointer. Spread the result on the element. */
export function useTilt(max = 8) {
  const onMouseMove = useCallback((e) => {
    if (reduced()) return;
    const el = e.currentTarget, r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    el.style.setProperty("--ry", `${(x - 0.5) * max * 2}deg`);
    el.style.setProperty("--rx", `${(0.5 - y) * max * 2}deg`);
    el.style.setProperty("--gx", `${x * 100}%`);
    el.style.setProperty("--gy", `${y * 100}%`);
  }, [max]);
  const onMouseLeave = useCallback((e) => {
    const el = e.currentTarget;
    el.style.setProperty("--ry", "0deg");
    el.style.setProperty("--rx", "0deg");
  }, []);
  return { onMouseMove, onMouseLeave };
}

/** Demo data shows instantly; live API data replaces it if the backend answers. */
export function useData() {
  const [data, setData] = useState({ ...demo, source: "demo" });
  useEffect(() => {
    let alive = true;
    loadData().then((live) => { if (alive && live) setData((d) => ({ ...d, ...live })); });
    return () => { alive = false; };
  }, []);
  return data;
}
