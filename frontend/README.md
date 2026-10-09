# PuneBite frontend (Phase 7)

1. Start the API:      `cd backend && python app.py`   (expects http://127.0.0.1:5000)
2. Start the frontend: `cd frontend && npm install && npm run dev`  -> http://localhost:5173

Vite proxies `/api/*` to Flask, so CORS is not needed. Change the port in `vite.config.js` if needed.
If a page looks empty, open the browser DevTools Network tab, look at the JSON the endpoint returned
and adjust field names in `src/api.js` or the page.
