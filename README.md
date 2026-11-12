
This is copilotProd, a construction-company AI assistant that customers and engineers can ask questions in text, audio, or images.

## Frontend

The React/Vite frontend is in the repository root.

1. Install [Node.js](https://nodejs.org/).
2. Install dependencies:

   ```bash
   npm install
   ```

3. Set `VITE_API_BASE_URL` in a `.env` file. For example:

   ```env
   VITE_API_BASE_URL=http://localhost:8080/api
   ```

4. Start the development server:

   ```bash
   npm run dev
   ```

5. Open the local URL printed in the terminal.

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

### Deploying the full application to PrimeCloud

Deploy this repository as a **Docker application**, not as a Python-runtime
application. The root [`Dockerfile`](./Dockerfile) builds the frontend and
backend together and includes the Nginx configuration and startup script.
Selecting Python-runtime deployment runs the [`Procfile`](./Procfile) directly
and bypasses the repository's Nginx configuration, so the bundled Nginx
permission fix will not apply.

Use the repository root as the build context and `Dockerfile` as the Dockerfile.
Configure PrimeCloud to expose port `8080`, mount persistent storage at
`/app/data`, and use `/ready` as the health-check path. See
[`DEPLOYMENT.md`](./DEPLOYMENT.md) for the full setup and required production
environment variables.

The seeded demo accounts are for development/demo use only. Set a new
`JENGA_SECRET_KEY` for the deployment and do not use the demo passwords for a
public production service.
