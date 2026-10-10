# Moving PuneBite to MongoDB Atlas (free M0 cluster)

The data is small (about 12k documents, a few MB), so the free M0 tier is enough.

1. **Create the cluster.** Sign in at https://cloud.mongodb.com, create a project, then *Create* a cluster and pick **M0 Free** (choose a region near you, for example Mumbai).
2. **Create a database user.** *Security > Database Access > Add New Database User*: username + password, role *Read and write to any database*. Use a password without special characters (or URL-encode them), and do not reuse a real password.
3. **Allow network access.** *Security > Network Access > Add IP Address*. For development use *Add Current IP Address*. If the API will be hosted online (Render, Railway, ...), you must also allow its IP, or use `0.0.0.0/0` (allows everywhere, so keep a strong password).
4. **Get the connection string.** *Database > Connect > Drivers > Python*. Copy the `mongodb+srv://...` string.
5. **Put it in `.env`** in the project root (copy `.env.example`):
   ```
   MONGO_URI=mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   DB_NAME=punebite
   ```
   `.env` is in `.gitignore`. Never paste the real string into code, notebooks, chat or GitHub.
6. **Install the new dependencies and load the data.**
   ```
   pip install -r backend/requirements.txt
   python backend/load_data.py
   python backend/app.py
   ```
   `load_data.py` prints the target host and "Inserted 12,134 documents". Check `http://127.0.0.1:5000/api/health`, and look at the collection in Atlas under *Browse Collections* (or in Compass using the same string).
7. **Hosting the API online (optional).** Deploy `backend/` to a host such as Render, set `MONGO_URI` and `DB_NAME` as environment variables there (not in the repo), run the app with `gunicorn backend.app:app`-style start command, and point the React app's API base URL at the deployed address.

Troubleshooting
- `ServerSelectionTimeoutError` / timeout: your IP is not in *Network Access*, or the network blocks port 27017.
- `Authentication failed`: wrong user/password, or special characters not URL-encoded.
- `The DNS query name does not exist`: the cluster name in the URI is wrong; copy it again.
- Collections appear empty: make sure `DB_NAME` matches the database you are browsing.
