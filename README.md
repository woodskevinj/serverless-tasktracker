# Task Tracker

A full-stack task management application for creating projects and tracking tasks within them. Built with React, Express.js, and PostgreSQL, with AWS infrastructure defined in CDK.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Express.js + raw SQL via `pg` |
| Database | PostgreSQL |
| Infrastructure | AWS CDK (Python) — VPC, RDS, EC2 |
| Testing | Vitest (frontend), Jest (backend), pytest (infrastructure) |

## Project Structure

```
tasktracker/
├── frontend/          # React SPA
├── backend/           # Express.js API server
└── infrastructure/    # AWS CDK app (Python)
```

Each directory is self-contained with its own README, dependencies, and tests. See the individual READMEs for detailed setup and usage:

- [Frontend README](frontend/README.md)
- [Backend README](backend/README.md)
- [Infrastructure README](infrastructure/README.md)

## Quick Start

### Prerequisites

- Node.js (v18+)
- Python 3.8+ (for infrastructure only)
- PostgreSQL (optional — the app runs without it)

### Run the app locally

```bash
# Terminal 1 — Backend (port 3001)
cd backend
npm install
node server.js

# Terminal 2 — Frontend (port 5173, proxies /api to backend)
cd frontend
npm install
npm run dev
```

### Run all tests

```bash
# Backend — 16 tests
cd backend && npm test

# Frontend — 17 tests
cd frontend && npx vitest run

# Infrastructure — 7 tests
cd infrastructure && source .venv/bin/activate && pytest
```

## Current Status

- **Phase 1 (complete):** Frontend and backend built with full test suites. The app runs without a live PostgreSQL connection — the backend returns clear JSON error responses and the frontend displays user-friendly error messages.
- **Phase 2 (complete):** AWS infrastructure defined in CDK — VPC, RDS PostgreSQL, EC2, security groups, and stack outputs. All tests passing.

## Next Steps

- **Docker:** Containerize the frontend, backend, and database with Docker Compose for consistent local development
- **Deployment:** Deploy the CDK stack to AWS and connect the application to the provisioned RDS instance
