# DevForge AI — Frontend

Next.js 15 web application providing the DevForge AI workspace portal.

## Quick Start

```bash
cd apps/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the workspace.

> **Requires the backend to be running** at `http://127.0.0.1:8000`.  
> See `apps/backend/README.md` for backend setup instructions.

## Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Override the backend API base URL | `http://127.0.0.1:8000/api/projects` |

## Application Views

The entire UI is contained in a single Next.js Client Component at `src/app/page.tsx`:

1. **Landing Portal** — Project name, idea, and tech stack inputs. Includes a "Try Sample Project" shortcut to quickly demo the system.
2. **Live Workspace Dashboard** — Real-time SSE-driven department timeline showing each agent's activity as the pipeline progresses.
3. **Blueprint Explorer** — File tree and syntax-highlighted viewer for all generated artifacts (`PRD.md`, `architecture.md`, `api_spec.yaml`, `database_schema.sql`). Includes a one-click ZIP download.

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **Runtime:** React 19
