# BitElevate PR Review Copilot - Frontend

AI-assisted first-pass code review triage console for Cynbit Technologies' BitElevate mentor team.

## Tech Stack
- **Framework**: React 18
- **Language**: TypeScript (strict mode)
- **Build Tool**: Vite
- **Routing**: React Router v6
- **Server State**: TanStack Query v5
- **Type Generation**: `openapi-typescript` auto-generated from FastAPI OpenAPI schema
- **Testing**: Vitest & React Testing Library
- **Styling**: Modern CSS Design System (Dark Slate, WCAG AA accessible contrast, keyboard hotkeys)

## Commands
```bash
# Install dependencies
npm install

# Generate types from backend OpenAPI schema
npm run generate:api

# Start Vite dev server (proxies /api to http://localhost:8000)
npm run dev

# Run Vitest test suite
npm test

# Production build
npm run build
```
