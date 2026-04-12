# Backend Rules — Restaurant Management System

## Backend Expectations
- Backend lives only in main_project.
- Do not generate backend code inside lovable_project.

## Authentication — Required Everywhere
- **Every protected route MUST have authentication middleware.** No exceptions.
- Apply auth guards on:
  - All admin pages and dashboard routes
  - All API routes that read or write data
  - Any route that involves user-specific data (orders, reservations, profiles)
- Use role-based access control (RBAC) where different user types exist (e.g. admin, staff, customer).
- Auth tokens must be stored securely (httpOnly cookies preferred over localStorage).
- Always validate the session/token on the server side — never trust client-side auth state alone.
- Add an auth layer to the API service wrapper so every request automatically includes credentials.

## Pre-Commit Checklist (Backend)
Before every commit touching backend code, ALL of the following must pass:

1. **Tests** — `pytest` (no failing tests)
2. **Format check** — `black --check .` (no unformatted files)
3. **Lint** — `flake8` (zero warnings allowed)
