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
- **No password required** — a lightweight identity system remembers who
  you are in the browser after registering, so you can log activities and
  see "My Dashboard" without a full login system. See `DESIGN.md` Section 6
  for the trade-offs of this approach.

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

**Frontend**
```
cd frontend
npm install
npm run dev
```
The app runs at `http://localhost:5173`.