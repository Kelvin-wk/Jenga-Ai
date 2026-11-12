
This is KopilotProd, a construction-company AI assistant that customers and engineers can ask questions in text, audio, or images.

## Backend

The FastAPI backend is in [`backend/`](./backend). It supports the modular `/api/v1`
routes described in the project plan, including authentication, sessions, catalogue
tools, conversations, media validation, chat, and human-review requests.

### Local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --reload --port 8000
```

Health checks:

- `GET http://localhost:8000/api/v1/health`
- `GET http://localhost:8000/api/v1/ready`

### Deploying the backend to Render

This repository includes [`render.yaml`](./render.yaml) for a Render Blueprint
deployment. In Render:

1. Select **New > Blueprint** and connect `kwisdomk/kpp`.
2. Select the `main` branch and apply `render.yaml`.
3. Set `CORS_ORIGINS` to the exact frontend origin, such as
   `https://your-frontend.onrender.com` (comma-separated for multiple origins).
4. Deploy and verify `/api/v1/health`.

The Blueprint generates `JENGA_SECRET_KEY` server-side and starts the service with
Render's `$PORT`. The service uses SQLite on a mounted Render disk at
`/var/data/jenga_consultants.db`; the disk is required because Render's instance
filesystem is otherwise ephemeral. The current backend is intentionally using the
SQLite architecture required by the master plan. Do not remove the disk or change
`DATABASE_URL` to a local relative path in a deployed environment.

The seeded demo accounts are for development/demo use only. Set a new
`JENGA_SECRET_KEY` if deploying outside the Blueprint-generated environment and do
not use the demo passwords for a public production service.
