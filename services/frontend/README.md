# Threat Intelligence Frontend

React + TypeScript frontend for the Threat Intelligence Monitoring System. Tactical / Palantir style (dark slate, amber/sky accents).

## Stack

- React 18, TypeScript, Vite
- Tailwind CSS (Tactical theme)
- TanStack Query, TanStack Table
- Recharts, react-force-graph-2d
- React Router v6

## Quick Start

```bash
npm install
npm run dev
```

Runs on http://localhost:5173. API calls are proxied to http://localhost:8000 (api-gateway).

## First Login / Bootstrap

- If there are no users yet, open login page and click `No users yet? Create first admin`.
- Fill company + admin data and the UI will create company, first user, and sign in automatically.
- Backend also assigns role `admin` to the first user in a company.

## Structure

See [STRUCTURE.md](./STRUCTURE.md) for folder layout and conventions.

## Build

```bash
npm run build
npm run preview   # preview production build
```
