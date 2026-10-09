import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function useFetch(path) {
  const [state, set] = useState({ data: null, error: null, loading: true });
  useEffect(() => {
    let live = true;
    set((s) => ({ ...s, loading: true, error: null }));
    api(path)
      .then((data) => live && set({ data, error: null, loading: false }))
      .catch((e) => live && set({ data: null, error: e.message, loading: false }));
    return () => { live = false; };
  }, [path]);
  return state;
}

export function Status({ loading, error }) {
  if (loading) return <p className="note">Loading…</p>;
  if (error) return <p className="note err">{error}. Check that the Flask API is running on port 5000.</p>;
  return null;
}
