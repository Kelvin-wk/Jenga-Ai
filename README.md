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

## Backend

The FastAPI backend is in [`backend/`](./backend). It supports the modular `/api/v1`
routes described in the project plan, including authentication, sessions, catalogue
tools, conversations, media validation, chat, and human-review requests.
The account chat accepts up to two images, PDFs, DOCX, TXT, Markdown, CSV, or voice
notes per message (8 MiB each). Image/PDF analysis and voice transcription use the
configured OpenAI API; document text is extracted for NLP analysis. Configure
`OPENAI_API_KEY` to enable those attachment and voice features. Users must confirm
they are authorized to send attachments to the configured AI service; do not send
private or restricted information unless its use with that service is approved.
Uploaded bytes are deleted after successful processing or removal, and pending
uploads expire after 24 hours (64 MiB/20 files maximum per account).

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

## Deployment

[DEPLOYMENT.md](DEPLOYMENT.md) describes the recommended Vercel frontend and
PrimeCloud backend deployment, plus a combined Docker alternative. Its
hosted-model configuration describes the current implementation, not approval
to send private or restricted data.

### Deploying frontend to Vercel and backend to PrimeCloud

Deploy the Vite frontend to Vercel and the FastAPI backend to PrimeCloud as a
Python web application. Configure `VITE_API_BASE_URL` in Vercel and the exact
Vercel origin in PrimeCloud's `CORS_ORIGINS`. See
[`DEPLOYMENT.md`](./DEPLOYMENT.md) for runtime settings, database requirements,
health checks, and deploy order. A combined Docker deployment remains
available as an alternative.

## Team

Thanks to everyone contributing to this project:

- [@De-pilot7127](https://github.com/De-pilot7127) — frontend
- [@Hawamuriuki](https://github.com/Hawamuriuki) — frontend
- [@JavaTheHutt-K](https://github.com/JavaTheHutt-K) — backend
- [@kwisdomk](https://github.com/kwisdomk) — AI/ML

## Contributing

Read [AGENTS.md](AGENTS.md) before contributing. The
[implementation plan](project-plan.md) records requirements and
task IDs; section 19 records progress. Proposed paths and features in the plan
may differ from the current source tree.
