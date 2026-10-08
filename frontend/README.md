# Frontend

This folder now contains a React + Vite frontend for the Nexus Commerce Intelligence dashboard.

## Development

```powershell
cd frontend
npm install
npm run dev
```

The app calls the FastAPI backend at `http://127.0.0.1:8000` by default, so start the backend first with:

```powershell
python -m uvicorn backend.app.main:app --reload
```

## Production build

```powershell
cd frontend
npm run build
```

The backend can also serve the built React app from `frontend/dist` once it is created.
