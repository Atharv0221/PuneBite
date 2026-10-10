# Putting PuneBite online (Render + Atlas)

One free Render web service runs the Flask API **and** serves the built React site, so there is a single link to share.

## Before you start
- Atlas is set up and `python backend/load_data.py` has loaded the data (see `ATLAS_SETUP.md`).
- In Atlas > Network Access allow `0.0.0.0/0` (Render's free tier has no fixed IP). Use a strong database password.
- The code is on GitHub (merge this branch into `master`).

## Steps
1. Sign in at https://render.com with GitHub.
2. *New > Blueprint*, pick the PuneBite repo. Render reads `render.yaml`.
3. When asked for `MONGO_URI`, paste your Atlas connection string (with the real password). It is stored in Render, not in Git.
4. Deploy. The first build takes several minutes (installs Python packages, then builds the React app).
5. Open the `https://punebite-xxxx.onrender.com` link. `/api/health` should report 12,134 restaurants.

## Notes
- The free plan sleeps after ~15 minutes without traffic; the first request afterwards takes about 30-60 seconds. Open the site once before a demo or viva.
- To run it the same way locally: `cd frontend && npm install && npm run build`, then `python backend/app.py` and open http://127.0.0.1:5000.
- If the build fails on `npm`, build the frontend elsewhere and host `frontend/dist` on Netlify/Vercel instead; then the API needs `flask-cors` (already enabled) and the frontend needs its API base URL changed.
- The scikit-learn version is pinned (1.9.1) because the saved models were trained with it.
