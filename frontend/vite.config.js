import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server forwards /api/* to Flask, so no CORS setup is needed.
// If your Flask runs on another port, change the target below.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:5000" } },
});
