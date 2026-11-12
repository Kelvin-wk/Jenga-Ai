
This is copilotProd, a construction-company AI assistant that customers and engineers can ask questions in text, audio, or images.

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

### Deploying the backend to PrimeCloud

Create a Python web application in PrimeCloud connected to the `main` branch of
`kwisdomk/kpp`. The repository includes root-level `requirements.txt`,
`.python-version`, and `Procfile` deployment markers for PrimeCloud's Python
build detection.

Configure:

- **Working directory:** repository root
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health-check path:** `/api/v1/health`
- **Python version:** 3.11 or newer

Set these environment variables in the PrimeCloud dashboard:

```text
JENGA_SECRET_KEY=<long-random-secret>
CORS_ORIGINS=https://your-frontend-domain.example
DATABASE_URL=sqlite:////path/to/persistent/jenga_consultants.db
```

Use the persistent-storage path provided by PrimeCloud for `DATABASE_URL`.
SQLite must not be stored on an ephemeral deployment filesystem; if the selected
PrimeCloud plan does not provide persistent storage, use a managed database and
set `DATABASE_URL` to its SQLAlchemy connection URL before deploying. Verify
`/api/v1/health` after the service starts.

The seeded demo accounts are for development/demo use only. Set a new
`JENGA_SECRET_KEY` for the deployment and do not use the demo passwords for a
public production service.
