# FactoryPulse Frontend

React and TypeScript operations dashboard for FactoryPulse.

## Features

- JWT-based login
- Production quality overview
- PCB risk prediction
- Prioritized inspection queue
- Model performance metrics
- Feature importance visualization
- Production order monitoring
- Machine inventory and status monitoring
- Protected application navigation
- Responsive dashboard layout

## Routes

| Route | Description |
|---|---|
| `/` | Quality overview |
| `/pcb-risk` | ML risk analysis |
| `/production` | Production orders |
| `/machines` | Machine inventory |

Unknown authenticated routes redirect to the overview page.

## Technology

- React
- TypeScript
- Vite
- React Router
- Axios
- Vitest
- Testing Library
- ESLint

## Development

Install dependencies:

    npm install

Start the development server:

    npm run dev

The frontend runs at:

    http://localhost:5173

API requests use the `/api/v1` path and are proxied to the FastAPI backend.

## Quality Checks

Run the frontend tests:

    npm run test

Run ESLint:

    npm run lint

Create a production build:

    npm run build

Current test suite:

    8 passed

## Production Container

The production build is served by Nginx. Nginx proxies `/api` requests to the backend service and supports client-side routing.