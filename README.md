# Code Quest

A full-stack coding practice platform built with **Python, Flask and Jinja2**. Users can solve problems, submit solutions, compete in contests, follow guided learning paths, and interact with other developers.

> **Note:** Submissions are saved in a `queued` state and reviewed by a reviewer. There is no automatic code execution or judge in this project.

---

## Features

**Practice**
- Problem library with difficulty levels, categories, tags, examples and hints
- Search and filters, and bookmarks
- Code submission page with a line-numbered editor
- Submission history with a status for each submission

**Compete**
- Contests with running, upcoming and ended phases
- Registration, per-contest problems with points, and announcements
- Leaderboard ranked by score, then penalty (time to each accepted solution plus 20 minutes per earlier wrong attempt)

**Learn**
- Learning paths made of ordered steps, each linked to a problem
- Per-user progress tracking (not started, in progress, completed)

**Community**
- Discussions with threaded replies, reactions (like, helpful, insightful), and locking by moderators
- Published solutions with upvotes and downvotes and an "official" mark
- Teams (invite by username) and private groups (invite by username or invite code)
- User profiles with links, followers and following

**Engagement**
- Notifications with per-type preferences
- Points and achievements

**Platform**
- Session-based authentication with CSRF protection and bcrypt password hashing
- Role-based access control (`user`, `moderator`, `admin`) with permissions such as `problem.manage`, `contest.manage`, and `discussion.moderate`
- Light and dark theme

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask 3 |
| Database | SQLite by default, Flask-SQLAlchemy, Flask-Migrate |
| Forms and security | Flask-WTF (CSRF), Flask-Bcrypt |
| Templates | Jinja2 |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5.3 |

---

## Getting started

### Requirements
- Python 3.10 or newer
- git

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/AliMaqsood-Code/Code-Quest.git
cd Code-Quest

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file
cp .env.example .env              # Windows: copy .env.example .env
```

Open `.env` and set a real secret key:

```
SECRET_KEY=change-this-to-a-long-random-string
DATABASE_URL=sqlite:///codequest.db
```

### Create the database and load starter data

```bash
python seed.py
```

This creates the tables, roles and permissions, programming languages, two starter problems, achievements, and an admin account.

### Run the app

```bash
python run.py
```

Open http://127.0.0.1:5000.

---

## Accounts

| Account | Username | Password |
|---|---|---|
| Admin (development only) | `admin` | `Admin@12345` |
| Demo users (after `seed_demo.py`) | `demo_ayesha`, `demo_bilal`, `demo_sara`, ... | `Demo@12345` |

> These passwords are for local development only. Change or remove them before any real deployment.

---

## Demo data (optional)

Three scripts fill the platform with realistic data so every page has something to show. Run them in this order:

```bash
python seed.py              # base data (required first)
python seed_demo.py         # contests, leaderboards, learning paths, demo users
python seed_community.py    # discussions, teams, groups, invitations, notifications
```

| Script | What it adds |
|---|---|
| `seed_demo.py` | 10 extra problems, 8 demo users, 6 contests (2 running, 2 upcoming, 2 finished) with leaderboards calculated by the app's own ranking logic, and 3 learning paths |
| `seed_community.py` | 6 discussions with replies and reactions, the "Code Quest Crew" team, the "Code Quest Community" group (join code `WELCOME2026`), pending invitations, and notifications |

Notes:
- All scripts are safe to run again. Anything that already exists is skipped.
- Contest dates are relative to the moment `seed_demo.py` runs. To reset them, delete the SQLite file and run the three scripts again.
- Run `seed_community.py` after you have registered your own account, since it adds existing users to the team and group and sends them notifications. Run it again later to include new users.

---

## Project structure

```
Code-Quest/
├── app/
│   ├── __init__.py          # Application factory (create_app)
│   ├── config/              # Configuration (reads .env)
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # Blueprints: auth, problems, submissions, contests, ...
│   ├── forms/               # Flask-WTF forms
│   ├── utils/               # Auth helpers, contest logic, notifications, hashing
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS and JavaScript
├── migrations/              # Flask-Migrate (Alembic) migrations
├── frontend-1/              # Static HTML prototype used as the design reference
├── seed.py                  # Base data
├── seed_demo.py             # Demo contests, learning paths, users
├── seed_community.py        # Demo discussions, teams, groups, notifications
├── smoke_test.py            # Backend logic smoke test
├── run.py                   # Development entry point
└── requirements.txt
```

### Pages

| Area | Pages |
|---|---|
| Public | Landing page, problems, problem detail, contests, leaderboards, discussions, learning paths, solutions |
| After login | Dashboard, submissions, teams, groups, achievements, notifications, profile and settings |

---

## Roles and permissions

| Role | Can do |
|---|---|
| `user` | Solve problems, submit, join contests, post discussions, create teams and groups |
| `moderator` | Everything a user can, plus lock threads and remove comments |
| `admin` | Everything, including managing problems, contests and users |

---

## Status

Done:
- Authentication, problems, submissions, contests and leaderboards
- Learning paths, discussions, solutions, teams, groups, profiles, notifications, achievements

Still to build:
- Management pages for admins and reviewers (problem editor, categories and tags, review queue, contest and learning-path editors). The backend routes exist, but their templates are not written yet.
- Automatic code execution and judging

---

## Reference

- Database schema: `online_coding_platform_database_schema.pdf`
- Static design prototype: `frontend-1/`

## License

See the [LICENSE](LICENSE) file.
