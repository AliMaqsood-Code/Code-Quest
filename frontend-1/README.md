# CodeArena – demo frontend
Open `index.html` in a browser (no build, no server needed). Bootstrap 5.3 is bundled in `vendor/`.

- `js/data.js` – ALL demo data (field names mirror the DB schema). Edit here.
- `js/app.js` – router, theme toggle, helpers
- `js/pages/` – one file per module: dashboard, problems (+judge mock), contests, community (discussions/solutions/notifications), learning, teams (teams/groups/invites), profile (achievements/points)
- `css/style.css` – theme variables (light/dark via `data-bs-theme`)

To connect Flask later: replace reads of `DB.*` with `fetch('/api/...')` calls inside each page file.
