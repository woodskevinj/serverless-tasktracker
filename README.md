# Task Tracker

A full-stack task management application for creating projects and tracking tasks within them. Built with React, Express.js, and PostgreSQL.

## Tech Stack

- **Frontend:** React (Vite) + Tailwind CSS
- **Backend:** Express.js with raw SQL queries via the `pg` library
- **Database:** PostgreSQL
- **Testing:** Jest + Supertest (backend), Vitest + React Testing Library (frontend)

## Project Structure

```
tasktracker/
├── backend/
│   ├── app.js              # Express app setup (middleware, routes)
│   ├── server.js           # Entry point — starts the server
│   ├── db.js               # PostgreSQL connection pool
│   ├── schema.sql          # Database table definitions
│   ├── .env                # Database connection config (gitignored)
│   ├── routes/
│   │   ├── projects.js     # Project CRUD routes
│   │   └── tasks.js        # Task CRUD routes
│   └── __tests__/
│       ├── projects.test.js
│       └── tasks.test.js
└── frontend/
    ├── vite.config.js       # Vite + Tailwind + API proxy config
    └── src/
        ├── api.js           # API client functions
        ├── App.jsx          # Router setup
        ├── pages/
        │   ├── ProjectList.jsx
        │   ├── CreateProject.jsx
        │   └── ProjectDetail.jsx
        ├── components/
        │   ├── Navbar.jsx
        │   ├── ProjectCard.jsx
        │   ├── TaskCard.jsx
        │   └── TaskForm.jsx
        └── __tests__/
```

## Features

- Create and view projects (name, description)
- Create tasks under a project (title, description, status, due date)
- Task statuses: To Do, In Progress, Done
- Update task status inline via dropdown
- Delete tasks
- Graceful error handling when the database is unavailable

## Getting Started

### Prerequisites

- Node.js (v18+)
- PostgreSQL (optional for Phase 1 — the app runs without it)

### Backend

```bash
cd backend
npm install
node server.js     # Starts on port 3001
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Starts on port 5173, proxies /api to backend
```

The Vite dev server proxies all `/api` requests to the Express backend, so both servers need to be running during development.

### Database Setup (when PostgreSQL is available)

1. Create a database:
   ```sql
   CREATE DATABASE tasktracker;
   ```
2. Run the schema:
   ```bash
   psql -d tasktracker -f backend/schema.sql
   ```
3. Configure `backend/.env` with your connection details:
   ```
   DB_USER=xxxxxx
   DB_PASSWORD=xxxxxx
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=tasktracker
   PORT=3001
   ```

### Running Tests

```bash
# Backend — 16 tests (mocked DB, no PostgreSQL needed)
cd backend && npm test

# Frontend — 17 tests (mocked API, no backend needed)
cd frontend && npx vitest run
```

## API Routes

| Method | Route                            | Description              |
| ------ | -------------------------------- | ------------------------ |
| GET    | `/api/projects`                  | List all projects        |
| GET    | `/api/projects/:id`              | Get a single project     |
| POST   | `/api/projects`                  | Create a project         |
| GET    | `/api/projects/:projectId/tasks` | List tasks for a project |
| POST   | `/api/projects/:projectId/tasks` | Create a task            |
| PATCH  | `/api/tasks/:id/status`          | Update task status       |
| DELETE | `/api/tasks/:id`                 | Delete a task            |

## Current Status

**Phase 1 (complete):** Full frontend and backend built with tests. The application runs without a live PostgreSQL connection — the backend returns clear error responses and the frontend displays user-friendly error messages.

## Next Steps

- **Database provisioning:** Stand up a PostgreSQL instance and run `schema.sql` to enable full end-to-end functionality
- **Docker:** Containerize the frontend, backend, and database with Docker Compose for consistent local development
- **Infrastructure (Python):** Build out deployment infrastructure with Python tooling (tests via pytest)
