# PrimeCloud Docker deployment

The production image contains both application surfaces in one container:

- Nginx serves the Vite frontend.
- FastAPI runs internally on `127.0.0.1:8000` through a non-privileged startup script.
- Nginx proxies `/api/*` and `/health` to FastAPI.
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

## PrimeCloud deployment

Create one PrimeCloud application from the GitHub repository with:

- Build context: repository root
- Dockerfile: `Dockerfile`
- Container port: `8080`
- Persistent disk mount: `/app/data`

Set these PrimeCloud environment variables/secrets. Use the connection string
provided by the PrimeCloud MySQL service:

```text
DATABASE_URL=mysql+pymysql://<user>:<password>@<mysql-host>:3306/<database>
CORS_ORIGINS=*
JENGA_SECRET_KEY=<long-random-production-secret>
PORT=8080
```

The frontend is built with `VITE_API_BASE_URL=/api/v1`, so browser requests
remain on the same PrimeCloud domain. No backend URL or cross-application
hostname is required.

Do not commit production secrets. Set JWT/session secrets, database settings,
and provider credentials in PrimeCloud's secret manager.

The application also accepts a `mysql://...` URL and automatically uses the
PyMySQL SQLAlchemy driver. The local Docker Compose setup continues to use
SQLite for development unless `DATABASE_URL` is overridden.

The database tables and seed users/products are created automatically when the
application starts. For production, use the PrimeCloud database's private
hostname and keep the database credentials in environment variables.
