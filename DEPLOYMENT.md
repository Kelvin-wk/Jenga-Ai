# PrimeCloud Docker deployment

The project is packaged as two containers:

- `backend`: FastAPI API with persistent SQLite data.
- `frontend`: Vite production build served by Nginx. Nginx proxies `/api/*` to the backend container.

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

The named `backend-data` volume preserves the SQLite database across container
restarts. Use `docker compose down -v` only when intentionally deleting local
application data.

## PrimeCloud deployment

PrimeCloud can deploy OCI container images or applications from GitHub. Create
two applications from this repository:

### Backend application

- Build context: `backend`
- Dockerfile: `backend/Dockerfile`
- Internal port: `8080`
- Persistent disk mount: `/app/data`
- Required environment:
  - `DATABASE_URL=sqlite:////app/data/jenga_consultants.db`
  - `CORS_ORIGINS=https://<frontend-domain>`
  - `PORT=8080`
  - `JENGA_SECRET_KEY=<long-random-production-secret>`

### Frontend application

- Build context: repository root
- Dockerfile: `Dockerfile`
- Build argument: `VITE_API_BASE_URL=/api/v1`
- Container port: `80`

The frontend Nginx configuration currently points to the Compose service name
`backend`. In a two-application PrimeCloud deployment, set the backend
service's internal hostname in `deploy/nginx.conf` before deploying, or deploy
the Compose stack as one PrimeCloud application if the selected PrimeCloud
plan supports multi-container Compose networking.

Do not commit production secrets. Set JWT/session secrets, database settings,
and any provider credentials in PrimeCloud's secret manager.

## Production storage note

SQLite is suitable for a single backend instance with a persistent disk. For
multiple backend replicas or higher availability, replace `DATABASE_URL` with
a managed PostgreSQL connection string before scaling the backend.
