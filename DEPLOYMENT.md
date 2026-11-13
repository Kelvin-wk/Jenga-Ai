# Deployment

The recommended low-friction deployment serves the Vite frontend from Vercel
and runs the FastAPI backend as a Python web service on PrimeCloud. Both targets
use this repository root; the root `requirements.txt` delegates to
`backend/requirements.txt`, and the root `Procfile` starts the API from
`backend/`.

## Vercel frontend

Create a Vercel project connected to this GitHub repository and configure:

- Root directory: repository root (leave "Include files outside the root directory" enabled if shown)
- Framework preset: Vite
- Build command: `npm run build`
- Output directory: `dist`
- Production and Preview environment variable:
  `VITE_API_BASE_URL=https://<your-primecloud-backend-domain>/api/v1`

`vercel.json` contains the Vite build/output settings and SPA fallback for
client-side routes. The API URL must be the full HTTPS PrimeCloud backend URL
including `/api/v1`; do not include a trailing slash. Set this variable for
each Vercel environment and redeploy after changing it. Never put database or
AI-provider secrets in `VITE_*` variables because they are embedded in browser
assets.

For local frontend development, copy the root `.env.example` to `.env` and set
`VITE_API_BASE_URL` to the local backend or deployed API as needed.

## PrimeCloud backend

Create a Python web application from the same GitHub repository:

- Runtime: Python, using the repository's `.python-version` (`3.11.9`)
- Root/build directory: repository root
- Install requirements: `pip install -r requirements.txt` (or let PrimeCloud
  install the root requirements file)
- Start command: `web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}` from the root `Procfile`
- Health/readiness path: `/ready`

Do not use the combined Docker image for this split deployment. PrimeCloud
provides `PORT`; Uvicorn must bind to `0.0.0.0` and that assigned port.
`/health` checks process liveness, while `/ready` also checks the configured
database and should be used for the platform health check.

Configure these PrimeCloud variables/secrets. A placeholder template is
available at `backend/.env.production.example`; copy it to `backend/.env` for
local testing only, then replace every placeholder. PrimeCloud must receive
the production values through its environment/secrets configuration unless
your service explicitly provides a private `.env` file mechanism.

```text
APP_ENV=production
DATABASE_URL=mysql+pymysql://<user>:<password>@<mysql-host>:3306/<database>
CORS_ORIGINS=https://<your-vercel-project>.vercel.app
JENGA_SECRET_KEY=<long-random-production-secret>
OPENAI_API_KEY=<optional-provider-secret>
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
```

Add your Vercel custom domain as another comma-separated exact origin in
`CORS_ORIGINS`, for example
`https://<your-vercel-project>.vercel.app,https://copilot.example.com`.
Do not use `*` in production. Add a Vercel Preview origin only if you need that
specific preview deployment to call the production backend. The backend accepts
the bearer authorization header and permits the API's GET, POST, and DELETE
methods across the configured origins.

`DATABASE_URL` must use the private PrimeCloud MySQL hostname and database
credentials. URL-encode special characters in the username or password.
Alternatively, the backend supports the documented `MYSQL_HOST`, `MYSQL_PORT`,
`MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` variables. Keep database
credentials, `JENGA_SECRET_KEY`, and `OPENAI_API_KEY` only in PrimeCloud's secret
manager. `OPENAI_API_KEY` is optional for text fallback but required for the
configured hosted AI and attachment/transcription features.

For local backend development, copy `backend/.env.example` to
`backend/.env`. The backend loads that file when present and does not override
environment variables provided by the shell or hosting platform. Real `.env`
files are excluded by `.gitignore`; commit only the `.env.example` templates.

Deployment order:

1. Deploy the backend and database on PrimeCloud, then verify
   `https://<backend-domain>/ready` returns `{"status":"ready"}`.
2. Set `VITE_API_BASE_URL` in Vercel to
   `https://<backend-domain>/api/v1`.
3. Set the exact Vercel production origin in PrimeCloud's `CORS_ORIGINS`.
4. Deploy/redeploy the Vercel frontend and test login, catalogue loading, chat,
   and attachment removal.

## Combined Docker deployment (alternative)

The production Docker image can still serve both application surfaces in one
container:

- Nginx serves the Vite frontend.
- FastAPI runs internally on `127.0.0.1:8000` through a non-privileged startup script.
- Nginx proxies `/api/*`, `/health`, and `/ready` to FastAPI.
- Nginx runs as the non-root `appuser`, sends its startup/error logs to stderr before loading the config, writes access logs to stdout, stores its PID under the writable `/tmp/nginx` directory, and uses sticky, world-writable paths for its PID and temporary files so runtime UID remapping does not block writes.
- The image includes the standard-library `ai/` ingestion validators and `data/` review assets; the build verifies the source manifest and BMS C1 snapshot before publishing the image.
- Only products already in the backend database are exposed to the UI and chat. Proposed catalogue entries with pending evidence or approval are not automatically imported or priced.
- The frontend product browser reads `/api/v1/catalogue/products`; it no longer displays a separate hard-coded product list. Chat requests use the backend `/api/v1/chat/query` contract.
- Each authenticated account reuses one active Product Copilot conversation. Messages and answer citations/warnings are stored in the configured database and are only readable by the owning account.
- Product cards use original local category illustrations and show catalogue identifiers, model numbers, specifications, and prices. These illustrations are representative, not manufacturer product photographs.
- The chat accepts up to two image, PDF, DOCX, TXT, Markdown, CSV, or supported audio attachments per message, capped at 8 MiB each. Images and PDFs are analyzed with the configured multimodal AI provider; text documents are extracted for analysis; microphone voice notes are transcribed before answering. Analysis/transcription requires `OPENAI_API_KEY`. Before sending attachments, users must confirm that they are authorized to send them to the configured AI service; do not send private or restricted information unless its use with that service has been approved.
- Uploaded bytes are stored in the configured database only while pending analysis. They are deleted after successful processing or when the user removes them; pending uploads expire after 24 hours. Pending storage is capped at 64 MiB and 20 files per account.
- PrimeCloud MySQL is used through the `DATABASE_URL` environment variable.

This avoids privileged process management and removes the need for a separate backend service hostname while keeping the
frontend and backend on one PrimeCloud domain.

## Local container validation

From the repository root:

```powershell
docker compose up --build
```

Open `http://localhost:8081`. The backend health endpoint is available through
`http://localhost:8081/health`. Stop the stack with:

```powershell
docker compose down
```

The named `app-data` volume preserves the SQLite database across restarts. Use
`docker compose down -v` only when intentionally deleting local data.

### PrimeCloud Docker configuration

Create one **Docker** application from the GitHub repository with:

- Build context: repository root
- Dockerfile: `Dockerfile`
- Container port: `8080`
- Persistent disk mount: `/app/data`

Do not configure this full-stack deployment as a Python-runtime application.
The root `Procfile` starts Uvicorn directly and does not start the bundled
Nginx or load `deploy/nginx.conf`; in that mode, changing this repository's
Nginx files cannot change the platform-managed Nginx logs or permissions. If
PrimeCloud currently has this service configured with a Python builder, switch
the application to Docker and rebuild from the repository root Dockerfile.

Set these PrimeCloud environment variables/secrets. Use the connection string
provided by the PrimeCloud MySQL service:

```text
DATABASE_URL=mysql+pymysql://<user>:<password>@<mysql-host>:3306/<database>
CORS_ORIGINS=https://<your-primecloud-domain>
JENGA_SECRET_KEY=<long-random-production-secret>
OPENAI_API_KEY=<OpenAI-secret-api-key>
OPENAI_MODEL=gpt-4.1-mini
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
PORT=8080
```

Alternatively, if PrimeCloud exposes separate MySQL variables, set
`MYSQL_HOST` (or `MYSQLHOST`), `MYSQL_PORT` (or `MYSQLPORT`; optional and
defaults to `3306`), `MYSQL_USER` (or `MYSQLUSER`), `MYSQL_PASSWORD` (or
`MYSQLPASSWORD`), and `MYSQL_DATABASE` (or `MYSQLDATABASE`). `DATABASE_URL`
takes precedence over `MYSQL_URL`, which takes precedence over separate
variables. If PrimeCloud provides `MYSQLPORT` as `3306/<database>`, the app
uses the numeric portion as the port and the suffix as the database name
unless `MYSQL_DATABASE`/`MYSQLDATABASE` is explicitly set.
The app does not load `DB_HOST`, `DB_PORT`, `DB_NAME`, or `DB_PASSWORD`; use
the `MYSQL_*` names above or provide `DATABASE_URL`. If a hostname in the
effective URL cannot resolve, verify the database service is running and
linked to this application on PrimeCloud's private network. The app does not
replace or guess database hostnames.
`MYSQL_HOST` must be a hostname or IP address only. If PrimeCloud gives a
combined host such as `host:3306/database`, that form is also accepted; do not
include credentials in the host variable.

The frontend is built with `VITE_API_BASE_URL=/api/v1`, so browser requests
remain on the same PrimeCloud domain. No backend URL or cross-application
hostname is required.

Do not commit production secrets. Set JWT/session secrets, database settings,
and provider credentials in PrimeCloud's secret manager.

The application also accepts a `mysql://...` URL and automatically uses the
PyMySQL SQLAlchemy driver. The local Docker Compose setup continues to use
SQLite for development unless `DATABASE_URL` is overridden.

The backend tests the MySQL connection before creating tables and retries
transient SQLAlchemy connection failures up to three times during startup.
If all attempts fail, startup still fails with safe diagnostics rather than
reporting the database as ready. The
`/ready` endpoint and Docker health check also verify database connectivity.
Production mode exits at startup with a clear error if no database settings
are supplied, instead of silently creating a local SQLite database. The
database tables and seed users/products are created automatically after
connection succeeds.

The backend uses OpenAI's Responses API for general product questions when
`OPENAI_API_KEY` is configured. Add the key as a PrimeCloud secret; never put
it in frontend variables, source files, or Git. `OPENAI_MODEL` is optional and
defaults to `gpt-4.1-mini`. Price lookups remain database-backed, engineer
safety queries keep their existing deterministic response, and customer
access checks run before any AI request. If the key is absent, general chat
uses the existing catalog-only fallback.
