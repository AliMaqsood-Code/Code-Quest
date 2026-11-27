# CodeArena – demo frontend

Open `index.html` in a browser (no build, no server needed). Bootstrap 5.3 is bundled in `vendor/`.

**Demo login:** `ada_dev` / `demo1234` — or click "Create an account" to register (stored in your browser's localStorage).
To reset everything: DevTools → Application → Clear storage.

- `js/data.js` – seed demo data (field names mirror the DB schema)
- `js/store.js` – localStorage "backend": register, login, logout, per-user data
- `js/app.js` – router, auth guard, theme, helpers
- `js/pages/` – auth, dashboard, problems, contests, community, learning, teams, profile
- Submissions are not judged: they are saved as "queued" with "result within 24 hours".

To connect Flask later: replace `Store` calls with `fetch('/api/...')`.
