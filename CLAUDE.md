# Claude Code Instructions

## Project Overview

Solo-developer portfolio manager app. Frontend: React + TypeScript + Vite + TailwindCSS. Backend: Python FastAPI + Supabase. Deployed on Render.

## Git Workflow

This is a solo project. All changes should go to production as fast as possible.

- Always develop on the assigned `claude/*` branch
- When done, commit all changes with a clear message, push, and create a PR targeting `main`
- PRs from `claude/*` branches are auto-approved and auto-merged via GitHub Actions — no manual review needed
- Never leave work uncommitted or unpushed — always finish by pushing and opening a PR so it reaches main

## Development Guidelines

- Keep changes focused and minimal — don't over-engineer
- Frontend is in `frontend/`, backend is in `backend/`
- Backend uses Supabase as the database (see `backend/app/database.py`)
- API routes are in `backend/app/routers/`, business logic in `backend/app/services/`
- Frontend API client is in `frontend/src/api/client.ts`
- React Query hooks are in `frontend/src/hooks/`
