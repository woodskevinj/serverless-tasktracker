# Task Tracker

A full-stack task management application for creating projects and tracking tasks within them. Built with React, Express.js, and PostgreSQL, with AWS infrastructure defined in CDK.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React (Vite) + Tailwind CSS |
| Backend | Express.js + raw SQL via `pg` |
| Database | PostgreSQL |
| Infrastructure | AWS CDK (Python) — VPC, RDS, ECS, ECR, ALB |
| Testing | Vitest (frontend), Jest (backend), pytest (infrastructure) |

## Project Structure

```
tasktracker/
├── frontend/          # React SPA
├── backend/           # Express.js API server
├── infrastructure/    # AWS CDK app (Python)
└── deploy.sh          # Build, push, and deploy to ECS
```

Each directory is self-contained with its own README, dependencies, and tests. See the individual READMEs for detailed setup and usage:

- [Frontend README](frontend/README.md)
- [Backend README](backend/README.md)
- [Infrastructure README](infrastructure/README.md)

## Quick Start

### Prerequisites

- Node.js (v18+)
- Python 3.8+ (for infrastructure only)
- Docker (for building and deploying)
- AWS CLI (configured with credentials)
- `jq` (for the deploy script)

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

## Deploy to AWS

The CDK stack provisions the infrastructure (VPC, RDS, ECS cluster, ECR repos, ALB). The `deploy.sh` script builds the app containers, pushes them to ECR, and updates the ECS service.

```bash
# 1. Deploy infrastructure (first time only)
cd infrastructure
cdk deploy

# 2. Build images and deploy to ECS
cd ..
./deploy.sh
```

The script will:
1. Discover ECS cluster/service names from CloudFormation
2. Log in to ECR
3. Build and push the frontend and backend Docker images
4. Register a new ECS task definition revision with the ECR image URIs
5. Update the ECS service with `--force-new-deployment`

On subsequent deploys, just run `./deploy.sh` again.

## Current Status

- **Phase 1 (complete):** Frontend and backend built with full test suites. The app runs without a live PostgreSQL connection — the backend returns clear JSON error responses and the frontend displays user-friendly error messages.
- **Phase 2 (complete):** AWS infrastructure defined in CDK — VPC, RDS PostgreSQL, ECS, ECR, ALB, and stack outputs. All tests passing.
- **Phase 3 (complete):** Dockerized frontend and backend with deploy script for building, pushing, and deploying to ECS.
