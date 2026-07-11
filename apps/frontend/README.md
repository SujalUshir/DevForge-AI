# 🎨 DevForge AI — Next.js 15 Frontend Portal

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-15+-black?logo=next.js&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-blue?logo=react&logoColor=white" alt="React">
  <img src="https://img.shields.io/badge/Tailwind_CSS-v4-38bdf8?logo=tailwind-css&logoColor=white" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/TypeScript-5-blue?logo=typescript&logoColor=white" alt="TypeScript">
</p>

A responsive, glassmorphic Next.js web application that serves as the visual portal and interactive workspace dashboard for the **DevForge AI** multi-agent engineering swarm.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the dashboard.

> [!IMPORTANT]
> **Backend Pre-requisite:** The Next.js portal requires the FastAPI backend server to be running (typically at `http://127.0.0.1:8000`).
> See [Backend Instructions](../backend/README.md) for backend setup details.

---

## ⚙️ Environment Variables

Configure these variables in a `.env.local` file inside the `apps/frontend/` directory:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Base API URL route handler for backend projects | `http://127.0.0.1:8000/api/projects` |

---

## 🖼️ Application Views

The entire interface is consolidated into an interactive single-page application wrapper located at [page.tsx](src/app/page.tsx):

1. **Idea Entry Portal:** Input fields for Project Name, Tech Stacks (Frontend, Backend, Database), and the User Idea. Features a "Try Sample Project" shortcut for quick prototyping.
2. **Live Swarm Timeline:** A dynamic, Server-Sent Events (SSE) log timeline showing active agent steps, status badges (Pending, Processing, Completed), and live output previews.
3. **Artifact Blueprints Explorer:** A file-tree browser with a syntax-highlighted code editor previewing generated artifacts (`PRD.md`, `architecture.md`, `api_spec.yaml`, `database_schema.sql`, etc.), accompanied by a single-click ZIP archive downloader.

---

## 🛠️ Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Runtime:** React 19 (Client Components)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4 (Vanilla Theme configuration)
- **Icons:** SVG Inline Layout Vector Icons
