# Jenga Consultants Product Copilot

A prototype assistant for the engineers and customers of Jenga Consultants, a
fictional industrial-equipment seller. Company accounts and catalogue prices are
demo data. Equipment specifications need traceable source documents.

The repository contains a React frontend, a FastAPI backend, and AI source
validation tools. Text chat and catalogue tools are implemented. Image and audio
inputs are present in the interface, but OCR, transcription, source retrieval and
a complete multimodal answer flow have not been verified.

The assistant provides decision support. It does not replace a manufacturer
manual or a qualified engineer.

## Run locally

The frontend is in `src/` at the repository root. The backend is in `backend/`.
Use Python 3.11 or newer and a Node.js version supported by the installed Vite
release.

From the repository root, create the Python environment and start the backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
$env:PYTHONPATH = "backend"
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal, install the frontend dependencies and set the API address:

```powershell
npm ci
$env:VITE_API_BASE_URL = "http://localhost:8000/api/v1"
npm run dev
```

Open the URL printed by Vite. The API address above matches the backend command;
the frontend's current fallback address uses port 8080.

Health endpoints:

- `GET http://localhost:8000/api/v1/health` checks that the API is running.
- `GET http://localhost:8000/api/v1/ready` checks database connectivity.

The backend seeds demo accounts and products. Use them only for development and
demonstrations. Deployment requires a separate `JENGA_SECRET_KEY`; demo passwords
are not suitable for a public production service.

## Checks

AI source-validation tests use the Python standard library:

```powershell
python -B -m unittest discover -s ai/tests -v
```

Frontend checks:

```powershell
npm run lint
npm run build
```

These checks do not establish model quality or complete application readiness.

## Data and model status

The AI catalogue has 15 candidates across three categories. All remain
unapproved; the source manifest has 19 pending rows and zero approved assets.
Document URLs and hashes are recorded for 13 candidate slots. Rights and
technical review remain pending. See [DATA.md](DATA.md).

LM Studio has served basic chat and embedding probes locally. The backend still
uses the hosted provider when configured; the local-model adapter and authorized
retrieval flow are pending. Model revision, checksum and licence records also
remain incomplete. See the [AI handoff](docs/AI_HANDOFF.md).

## Deployment and team work

[DEPLOYMENT.md](DEPLOYMENT.md) describes the combined Docker deployment for
PrimeCloud and local containers. Its hosted-model configuration describes the
current implementation, not approval to send private or restricted data.

Read [AGENTS.md](AGENTS.md) before contributing. The
[implementation plan](JENGA_CONSULTANTS_MASTER_PLAN.md) records requirements and
task IDs; section 19 records progress. Proposed paths and features in the plan
may differ from the current source tree.
