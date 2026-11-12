# PrimeCloud Docker deployment

The production image contains both application surfaces in one container:

- Nginx serves the Vite frontend.
- FastAPI runs internally on `127.0.0.1:8000`.
- Nginx proxies `/api/*` and `/health` to FastAPI.
- SQLite is stored under `/app/data` on a persistent disk.

This removes the need for a separate backend service hostname and keeps the
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

## PrimeCloud deployment

Create one PrimeCloud application from the GitHub repository with:

- Build context: repository root
- Dockerfile: `Dockerfile`
- Container port: `8080`
- Persistent disk mount: `/app/data`

Set these PrimeCloud environment variables/secrets:

```text
DATABASE_URL=sqlite:////app/data/jenga_consultants.db
CORS_ORIGINS=*
JENGA_SECRET_KEY=<long-random-production-secret>
PORT=8080
```

The frontend is built with `VITE_API_BASE_URL=/api/v1`, so browser requests
remain on the same PrimeCloud domain. No backend URL or cross-application
hostname is required.

Do not commit production secrets. Set JWT/session secrets, database settings,
and provider credentials in PrimeCloud's secret manager.

## Production storage note

SQLite is suitable for a single backend instance with a persistent disk. For
multiple backend replicas or higher availability, replace `DATABASE_URL` with
a managed PostgreSQL connection string before scaling the application.
