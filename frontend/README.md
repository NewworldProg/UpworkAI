# Frontend (React)

This folder will contain a React app that consumes the Django API at /api/.

Planned features:
- Project list and filters
- Modal with details and cover letter generation
- Send to Monday button

Quickstart (Windows PowerShell):

1. Install dependencies:

```powershell
cd frontend; npm install
```

2. Run dev server:

```powershell
npm run dev
```

By default the frontend expects the backend API to be available at the same host under /api/. In development you can set up a proxy in Vite or run the frontend and backend on separate ports and configure CORS in Django.

