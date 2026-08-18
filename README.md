# Fitness Challenge App

A full-stack fitness tracking application that gamifies physical activity
and fosters friendly competition through a global leaderboard.

Users log activities across six different sports — running, walking,
cycling, gym, swimming, and daily steps — each tracked with the metric that
makes sense for it (distance, duration, or a step count). Behind the scenes,
every activity is normalized into a single "Points" score using a fixed
conversion system, so someone who swims can compete fairly on the same
leaderboard as someone who runs, even though the two sports are measured
completely differently.

## Features

- **User registration** — sign up with a first and last name (email
  optional). Duplicate name registrations are rejected.
- **Activity logging** — log an activity for any of the six supported
  sports; points are calculated automatically the moment it's saved, using
  the flooring rules described in [`DESIGN.md`](./DESIGN.md).
- **Global leaderboard** — every registered user with at least one logged
  activity is ranked by total points, with an indicator showing whether
  their rank moved up, down, or stayed the same since the last time the
  leaderboard was viewed.
- **Personal dashboard** — for each user: total points, total activities,
  their top sport, a breakdown of points by sport (donut chart), a points-
  over-time trend (area chart), and a full activity history table.
- **Password-based login, enforced server-side** — registration requires a
  password (hashed with bcrypt before storage), and returns a signed JWT
  access token immediately. Logging an activity requires that token in an
  `Authorization: Bearer <token>` header; the backend derives *who's*
  logging the activity from the verified token itself, never from a
  client-supplied id — so one user genuinely cannot log activities as
  another. See [`DESIGN.md`](./DESIGN.md) Section 5.4 for how this works
  and Section 6 for its remaining trade-offs.

> **Note:** this branch (`feature/auth`) adds authentication on top of the
> core assignment, which did not require it. The `main` branch reflects the
> assignment's original requirements exactly, unmodified.

## Tech Stack
- **Backend:** Python, FastAPI, SQLite
- **Frontend:** React, Recharts, TailwindCSS

## Documentation

See [`DESIGN.md`](./DESIGN.md) for the full system architecture, database
schema, API specifications, scoring logic, frontend breakdown, and known
trade-offs/edge cases.

## Setup Instructions

**Backend**
```
cd backend
python -m venv venv
venv\Scripts\activate        # Windows — use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
python seed.py                # optional: populates demo users and activities
python main.py
```
The API runs at `http://localhost:8000` (interactive docs at `/docs`).

You'll also need a `backend/.env` file with a `JWT_SECRET_KEY` set — this is
gitignored and not included in the repo, since it's a secret. Generate one
yourself, e.g. `python -c "import secrets; print(secrets.token_hex(32))"`,
and add it as:
```
JWT_SECRET_KEY=<your generated value>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Every user created by `seed.py` shares the password `Password123!` — handy
for logging in as any demo user (e.g. first name `Alice`, last name
`Johnson`) without registering a fresh account.

**Frontend**
```
cd frontend
npm install
npm run dev
```
The app runs at `http://localhost:5173`.