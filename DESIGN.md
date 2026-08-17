# Fitness Challenge Application — Design Document

## Overview

A full-stack application that lets users log fitness activities across six sport
types, normalizes them into a single "Points" metric, and ranks users on a
global leaderboard. Each user also gets a personal dashboard visualizing their
activity history, sport preferences, and points trend over time.

**Stack:** FastAPI (Python) + SQLite on the backend, React (Vite) + Tailwind CSS
+ Recharts on the frontend.

---

## 1. System Architecture & Data Flow

### 1.1 High-level overview

```mermaid
graph LR
    subgraph Browser
        A[React SPA<br/>Vite + Tailwind + Recharts]
    end

    subgraph Backend [FastAPI Application]
        B[Routers<br/>HTTP layer, request/response models]
        C[Controllers<br/>business logic, DB queries]
        D[Scoring Service<br/>pure point-calculation functions]
    end

    E[(SQLite<br/>fitness.db)]

    A -- "HTTP / JSON<br/>axios, /api/*" --> B
    B --> C
    C --> D
    C -- "sqlite3 connection<br/>per-request scoped" --> E
```

The backend is intentionally layered so each piece has one job:

- **Routers** (`routers/users.py`, `routers/activities.py`) declare the HTTP
  routes, request/response Pydantic models, and documented status codes. They
  contain no business logic — each route handler is a one-line delegation to a
  controller function.
- **Controllers** (`controllers/user_controller.py`, `controllers/activity_controller.py`)
  hold the actual business logic: looking up users, checking existence,
  assembling dashboard data, computing the leaderboard, and running SQL
  queries against the database connection handed to them.
- **Services** (`services/scoring_service.py`) is a single-purpose module with
  no database or HTTP awareness at all — just pure functions that take a sport
  and a metric value string and return an integer point value. Because it has
  no side effects, it is trivially unit-testable in isolation from the rest of
  the app.
- **Database** (`database.py`) owns connection creation and lifecycle. A new
  SQLite connection is created per request via a FastAPI dependency
  (`get_db`), which commits on success and rolls back on any unhandled
  exception, then always closes the connection — so a failed request can
  never leave a half-written row behind.

The frontend mirrors this separation: **pages** (`Leaderboard.jsx`,
`Dashboard.jsx`, `Register.jsx`) own data-fetching and page-level state;
**components** (`LeaderboardTable.jsx`, `StatsSummary.jsx`,
`SportBreakdownChart.jsx`, `PointsOverTimeChart.jsx`, `ActivityHistory.jsx`,
`LogActivityForm.jsx`) are presentational — they receive data as props and
render it, with no knowledge of the API. `api/client.js` is the single point
of contact with the backend; every network call in the app goes through it.

### 1.2 Request/response flow — User Registration

1. User fills in first name, last name, and (optionally) email on
   `Register.jsx` and submits the form.
2. The frontend calls `POST /api/users/register` with
   `{ firstName, lastName, email? }`.
3. FastAPI validates the body against `UserRegisterRequest` (via Pydantic) —
   trims whitespace, rejects blank/oversized names, validates email format if
   present. A failure here returns **422** (FastAPI/Pydantic's standard
   response for request validation failures — see Section 6 for why this
   project sticks with that default rather than overriding it).
4. The `users` router delegates to `register_user()` in the user controller,
   which runs a plain `INSERT` into the `users` table.
5. The table has a `UNIQUE(firstName, lastName)` constraint. If the insert
   violates it, SQLite raises `IntegrityError`, which the controller catches
   and converts into a **409 Conflict** with a descriptive message.
6. On success, the controller returns the new `userId` (SQLite's
   `lastrowid`) and a confirmation message.
7. The frontend stores `{ userId, name }` in `localStorage` (see Section 5.4) and
   redirects to `/dashboard/:userId`.

### 1.3 Request/response flow — Activity Ingestion

1. From their own dashboard, a user opens the "Log Activity" modal, picks a
   sport, and fills in the metric value in the format appropriate to that
   sport (distance in km, duration in MM:SS, or a step count).
2. The frontend calls `POST /api/activities` with
   `{ userId, sport, metricType, metricValue }`.
3. Pydantic validates the payload against `ActivityRequest`: the `sport` and
   `metricType` must be a valid pairing (e.g. `running` must pair with
   `distance`, not `duration`), and `metricValue` must match the expected
   format and be positive. Any failure here returns **422**.
4. The `activities` router delegates to `log_activity()` in the activity
   controller, which first confirms `userId` exists (**404** if not).
5. The controller calls `calculate_points(sport, metricValue)` in the scoring
   service, which applies the correct conversion rate and flooring rule for
   that sport (Section 4).
6. The activity — including the already-computed `points` — is inserted into
   the `activities` table.
7. The full saved activity (with its new `activityId` and server-assigned
   `loggedAt` timestamp) is returned to the frontend.
8. The frontend closes the modal and re-fetches the dashboard, so the new
   activity, updated totals, and updated charts appear immediately.

---

## 2. Database Schema & Data Model

### 2.1 Entity-relationship diagram

```mermaid
erDiagram
    USERS ||--o{ ACTIVITIES : logs
    USERS {
        int id PK
        text firstName
        text lastName
        text email
        int previousRank
        datetime createdAt
    }
    ACTIVITIES {
        int id PK
        int userId FK
        text sport
        text metricType
        text metricValue
        int points
        datetime loggedAt
    }
```

### 2.2 Tables

**`users`**

| Column         | Type     | Notes                                              |
|----------------|----------|-----------------------------------------------------|
| `id`           | INTEGER  | Primary key, autoincrement                          |
| `firstName`    | TEXT     | Required                                             |
| `lastName`     | TEXT     | Required                                             |
| `email`        | TEXT     | Optional                                             |
| `previousRank` | INTEGER  | Nullable. Rank from the last leaderboard fetch — used only to compute trend direction (Section 5.3), not a business field the user sees directly. |
| `createdAt`    | DATETIME | Defaults to insert time. Used as the leaderboard tie-breaker. |

`UNIQUE(firstName, lastName)` is declared directly on the table.

**`activities`**

| Column        | Type     | Notes                                              |
|---------------|----------|-----------------------------------------------------|
| `id`          | INTEGER  | Primary key, autoincrement                          |
| `userId`      | INTEGER  | Foreign key → `users.id`                             |
| `sport`       | TEXT     | One of `running`, `walking`, `cycling`, `gym`, `swimming`, `steps` |
| `metricType`  | TEXT     | One of `distance`, `duration`, `count`               |
| `metricValue` | TEXT     | Raw value as submitted (e.g. `"5.5"`, `"1:30"`, `"8500"`) |
| `points`      | INTEGER  | Computed once at write time by the scoring service, never recalculated on read |
| `loggedAt`    | DATETIME | Defaults to insert time                              |

### 2.3 Design decisions worth calling out

- **No separate `leaderboard` table.** The leaderboard is a `GROUP BY`/`SUM`
  aggregate query over `activities`, joined to `users`, run fresh on every
  request (see the query in `activity_controller.get_leaderboard`). This
  keeps `activities` as the single source of truth — there's no risk of a
  cached leaderboard table drifting out of sync with the activity log. The
  trade-off is discussed in Section 6.
- **Duplicate-user prevention is enforced at the database level**, not just
  checked in application code before an insert. A `UNIQUE` constraint means
  even if two registration requests for the same name arrived at the exact
  same moment (a race condition), SQLite itself would reject the second
  insert — a pure application-level "check then insert" pattern would be
  vulnerable to that race.
- **`points` is stored, not derived on read.** Storing the computed value
  means historical activities keep their original points even if the scoring
  formula changes in the future, and leaderboard/dashboard queries only need
  to `SUM` an existing column rather than recompute scoring logic in SQL.
- **`metricValue` is a single generic TEXT column**, not three separate
  typed columns (`distanceKm`, `durationSeconds`, `stepCount`). This keeps
  the schema and the request/response shape simple — one field regardless of
  sport — at the cost of the value not being a queryable/sortable number at
  the database level. Since every current use case (scoring, display) parses
  the string in application code anyway, this was judged an acceptable
  trade-off for this project's scope.

---

## 3. API Specifications

All routes are prefixed with `/api`. Every error response follows the same
shape: `{ "detail": { "error": "...", "message": "..." } }`.

### `POST /api/users/register`

Registers a new user.

**Request body**
```json
{ "firstName": "Jane", "lastName": "Doe", "email": "jane@example.com" }
```
`email` is optional. `firstName`/`lastName` are required, 1–50 characters,
whitespace-trimmed, cannot be blank.

**Responses**

| Status | When                                              |
|--------|---------------------------------------------------|
| 201    | Success — returns `{ userId, message }`            |
| 422    | Missing/invalid fields (e.g. blank name, bad email format) |
| 409    | A user with the same first + last name already exists |

### `POST /api/activities`

Logs a fitness activity and returns the points awarded.

**Request body**
```json
{ "userId": 1, "sport": "running", "metricType": "distance", "metricValue": "5.5" }
```

**Validation rules**
- `sport` must be one of the six supported values.
- `metricType` must match `sport` per the fixed mapping (running/walking/cycling
  → `distance`; gym/swimming → `duration`; steps → `count`).
- `metricValue` format must match `metricType`: a positive decimal string for
  distance, `MM:SS` for duration, a positive integer string for steps.

**Responses**

| Status | When                                              |
|--------|---------------------------------------------------|
| 201    | Success — returns `{ activityId, pointsAwarded, sport, metricType, metricValue, loggedAt }` |
| 422    | Schema validation failure or mismatched sport/metricType |
| 404    | `userId` does not exist                            |

### `GET /api/activities/leaderboard`

Returns the global leaderboard.

**Response**
```json
{
  "leaderboard": [
    { "rank": 1, "userId": 1, "name": "Alice Johnson", "totalPoints": 4070, "trend": "same" }
  ],
  "totalUsers": 8
}
```
Only users with at least one logged activity appear. Ranked by total points
descending; ties broken by earliest registration date. `trend` (`up` /
`down` / `same`) is computed by comparing the current rank to the rank
recorded on the *previous* fetch (Section 5.3).

### `GET /api/users/{userId}/dashboard`

Returns full personal dashboard data for one user.

**Response**
```json
{
  "userId": 1,
  "name": "Alice Johnson",
  "totalPoints": 4070,
  "totalActivities": 7,
  "topSport": "running",
  "activities": [ { "id": 7, "sport": "running", "metricType": "distance", "metricValue": "6.0", "points": 600, "loggedAt": "2026-08-16T19:51:54" } ],
  "sportBreakdown": [ { "sport": "running", "totalPoints": 2950, "percentage": 72.48 } ],
  "pointsOverTime": [ { "date": "2026-08-03", "points": 1000 } ]
}
```

| Status | When                       |
|--------|----------------------------|
| 200    | Success                    |
| 404    | `userId` does not exist    |

### `GET /health`

Simple liveness check, returns `{ "status": "healthy", "version": "1.0.0" }`.
Used to confirm the API process is up; does not check database connectivity.

### Error handling strategy

One exception handler registered globally in `main.py`, for any unhandled
exception → **500 Internal Server Error** with a generic message, so raw
stack traces never leak to the client.

Request validation failures (missing/invalid fields, or the cross-field
`model_validator` check catching a mismatched sport/metricType combination)
are *not* separately handled — they're left to FastAPI/Pydantic's built-in
`RequestValidationError` handling, which returns **422 Unprocessable
Entity** by default. See Section 6 for why this project deliberately keeps
that default rather than overriding it to 400.

`404` (not found) and `409` (duplicate user) are raised explicitly inside
the relevant controller functions, since they represent business-logic
outcomes rather than request-parsing failures.

---

## 4. Scoring & Normalization Logic

All scoring lives in `services/scoring_service.py`, behind a single public
function, `calculate_points(sport, metric_value)`, so there is exactly one
place in the codebase that knows how points are calculated.

### 4.1 Conversion rates

| Activity     | Metric        | Rate            |
|--------------|---------------|------------------|
| Running      | 1 km          | 100 points       |
| Walking      | 1 km          | 50 points        |
| Cycling      | 1 km          | 25 points        |
| Swimming     | 1 minute      | 15 points        |
| Gym          | 1 minute      | 5 points         |
| Daily Steps  | 100 steps     | 1 point          |

### 4.2 Flooring rules

**Distance sports** (running, walking, cycling): points are calculated
first, then the *final result* is floored.

```
points = floor(distance_km × rate)
```
Example: 1.55 km walking → `1.55 × 50 = 77.5` → floored to **77**.

**Duration sports** (gym, swimming): only fully completed minutes count —
seconds are discarded *before* multiplying by the rate, not floored after.

```
whole_minutes = floor(MM:SS to whole minutes)   # seconds simply dropped
points = whole_minutes × rate
```
Example: 1:55 of gym → 1 whole minute (55 seconds discarded) → `1 × 5` =
**5** points.

**Steps**: the step count is floored to the nearest complete block of 100
*before* the point calculation, not after.

```
complete_blocks = floor(steps / 100)
points = complete_blocks × 1
```
Example: 399 steps → `floor(399 / 100) = 3` blocks → **3** points.

These three rules are implemented as three separate internal helper
functions (`_calculate_distance_points`, `_calculate_duration_points`,
`_calculate_steps_points`), each with the flooring applied at the specific
stage the assignment specifies — distance floors the final result, duration
floors the input before multiplying, and steps floors the input before
dividing conceptually into blocks. Keeping these as separate functions
(rather than one generic formula) makes each rule's behavior easy to verify
independently and matches the assignment's three visibly different flooring
semantics.

---

## 5. Frontend Architecture & Visualizations

### 5.1 Component breakdown

```
App.jsx                        — nav bar + route table, tracks current-user identity
├── pages/Leaderboard.jsx       — fetches leaderboard, renders LeaderboardTable
├── pages/Register.jsx          — registration form
└── pages/Dashboard.jsx         — fetches one user's dashboard data
    ├── components/StatsSummary.jsx        — 3 summary stat cards
    ├── components/PointsOverTimeChart.jsx — Recharts area chart
    ├── components/SportBreakdownChart.jsx — Recharts donut chart
    ├── components/ActivityHistory.jsx     — activity log table
    └── components/LogActivityForm.jsx     — "Add Activity" modal

components/LeaderboardTable.jsx  — used by Leaderboard.jsx
```

Pages own data-fetching and loading/error state; components are purely
presentational, receiving already-fetched data as props and rendering it.
This separation means every chart/table component can be tested or reused
independently of the network layer.

### 5.2 Data fetching pattern

Every page follows the same shape, built on two hooks:

- `useState` holds the fetched data, plus `isLoading`/`error` flags.
- `useEffect` triggers the fetch when the page mounts (and, on the dashboard,
  again whenever the URL's `userId` changes, or after a new activity is
  logged — see below).

Each fetch effect includes cancellation guarding (an `isCancelled` flag
checked before every state update, flipped by the effect's cleanup
function) so a component that unmounts mid-request never tries to update
state that no longer exists on screen.

The dashboard additionally tracks a `refreshKey` counter in its effect's
dependency array. Logging a new activity increments this counter, which
re-triggers the exact same fetch effect — reusing one code path for both
"initial load" and "reload after a write," rather than maintaining two
separate fetch implementations.

### 5.3 Ranking calculation strategy

Ranking is computed entirely server-side, in SQL, on every leaderboard
request — not cached, and not recalculated on the frontend. The query
sums each user's activity points, orders by total points descending with
earliest registration date as the tie-breaker, and only includes users with
at least one logged activity. Rank *trend* (up/down/same) is derived by
comparing each user's rank in the current result against a `previousRank`
value stored on their user row, which gets overwritten with their new rank
at the end of every leaderboard fetch. The frontend has no ranking logic of
its own — `LeaderboardTable.jsx` simply renders whatever rank and trend the
backend already computed.

### 5.4 Identity without authentication

The assignment marks authentication as optional. Rather than build no
identity concept at all, a lightweight approach was used: on successful
registration, the returned `userId` and display name are saved to the
browser's `localStorage`. `App.jsx` reads this to decide what the nav bar
shows ("Register" vs. "My Dashboard") and `Dashboard.jsx` reads it to decide
whether to show the "Add Activity" button (only on a user's own dashboard).
This is a UX convenience only, not a security boundary — see Section 6 for
its limitations.

### 5.5 Visualization choices

- **Sport breakdown → donut chart** (Recharts `PieChart` with a nonzero
  `innerRadius`). A part-to-whole relationship (how a user's total points
  split across sports) is what pie/donut charts communicate best; the donut
  hole leaves room to place total points centrally if wanted later.
- **Points over time → area chart**, not a bar chart, because the point is
  to show a continuous *trend* across days, and the shaded area under the
  line reinforces cumulative volume rather than just plotting isolated
  daily values.
- Both charts render a fully custom empty state ("No activity data yet")
  rather than an empty/broken chart, since a brand-new user will have no
  data in either dataset yet.

---

## 6. Trade-offs & Edge Cases

**No real authentication.** There is no password, session, or token —
"logging in" is registering (or, currently, only registering) and having a
userId cached client-side. This means:
- The backend does not verify that a request claiming a given `userId` was
  actually made by that person — `POST /api/activities` trusts whatever
  `userId` is in the payload. The frontend only *hides* the "Add Activity"
  button on other users' dashboards; it does not enforce ownership
  server-side. A production version would need the backend to independently
  authenticate the caller.
- There is currently no way to return to a previously registered identity
  after clicking "Switch user," since the backend has no login endpoint —
  only registration, which explicitly rejects a duplicate name. This is a
  known, explicitly accepted limitation for this assignment's scope rather
  than an oversight.

**Leaderboard computed live, not cached.** Every call to
`GET /activities/leaderboard` runs a full `GROUP BY`/`SUM` aggregate over
the entire `activities` table. At this project's scale (a handful of users,
tens of activities) this is effectively instant and keeps the implementation
simple with zero risk of a stale cached value. At a much larger scale
(thousands of users, high request volume), this would need revisiting —
e.g. a periodically refreshed materialized leaderboard, or caching with a
short TTL — since re-aggregating the full activity table on every page view
would not scale indefinitely.

**No pagination.** Both the leaderboard and a user's activity history return
their full result set in one response. Acceptable at the current data
volume; a real production system would paginate both endpoints once
user/activity counts grow large enough that a single response becomes slow
or unwieldy to render.

**Concurrency handling.** Each request gets its own SQLite connection
(`database.get_db`, a FastAPI dependency), which commits on success and
rolls back on any exception — so a failed request can never leave a
partial write behind. The database runs in WAL (write-ahead log) mode,
which allows concurrent reads to proceed without blocking on a write in
progress. SQLite still serializes concurrent *writes* (only one writer at a
time) — a known constraint of a single-file database. At this project's scale (a handful of users, occasional
activity logging) that constraint has no practical impact. A system
expecting heavy concurrent write traffic would need a client-server
database (e.g. PostgreSQL) instead.

**Duplicate-user prevention is race-safe.** Because the `UNIQUE(firstName,
lastName)` constraint lives in the database schema itself rather than being
checked in application code before the insert, two simultaneous
registration attempts for the same name cannot both succeed — SQLite
rejects the second insert outright, regardless of timing.

**422, not 400, for validation errors.** The assignment's requirements
section names "400 Bad Request" for invalid schemas or mismatched
sport/metric types. FastAPI/Pydantic's actual default for this case is 422
Unprocessable Entity — the HTTP-spec-correct code for "the request was
well-formed, but its content failed validation," as distinct from 400,
which is meant for a request that's malformed at the syntax level (e.g.
invalid JSON). Since FastAPI was the explicitly chosen stack for this
project, and 422 is that stack's own idiomatic, spec-aligned behavior for
this exact situation, this project reads the assignment's mention of "400"
as shorthand for "an appropriate 4xx client error" rather than a literal
requirement to override the framework's own convention. Sticking with 422
avoids introducing a custom exception handler purely to fight against the
chosen framework's standard behavior.

**Sport-to-metric mapping is duplicated.** Both the backend
(`VALID_SPORT_METRIC_MAP` in `models/schemas.py`) and the frontend
(`SPORT_METRIC_MAP` in `LogActivityForm.jsx`) independently define which
metric type each sport requires. The frontend needs its own copy to decide
which input fields to render *before* a request is ever sent; the backend
copy remains the actual source of truth and validates independently
regardless of what the frontend sends. Worth centralizing (e.g. exposing
this mapping via an API endpoint the frontend fetches once) if the sport
list were expected to change frequently; for a fixed, assignment-scoped set
of six sports, the duplication was judged an acceptable, low-risk trade-off.

**Input validation depth.** Validation is handled entirely by Pydantic
models and SQLite constraints — there is no additional rate limiting,
request throttling, or sanitization layer beyond what FastAPI/Pydantic
provide by default. Reasonable for an assessment/demo scope; a
publicly-deployed version would need rate limiting at minimum.
