# Deployment Guide — Veritas

## Quick Start (Development)

```bash
# 1. Clone
git clone https://github.com/siddhartha0132/uniHack.git
cd uniHack

# 2. Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure (optional)
cp .env.example .env  # edit if needed

# 4. Run backend
uvicorn app.main:app --reload --port 8000

# 5. Frontend (separate terminal)
cd ../frontend
# Option A: Open index.html directly in browser
# Option B: Serve with Python
python -m http.server 5500
# Then open http://localhost:5500
```

---

## Docker Deployment

### Build Images

```bash
# Backend
cd backend
docker build -t veritas-backend:latest .

# Frontend
cd ../frontend
docker build -t veritas-frontend:latest .
```

### Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: veritas
      POSTGRES_USER: veritas
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U veritas"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://veritas:${POSTGRES_PASSWORD}@postgres:5432/veritas
      JWT_SECRET: ${JWT_SECRET}
      JWT_ALGORITHM: HS256
      JWT_EXPIRE_MINUTES: 60
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

```bash
# Create .env for compose
cat > .env <<EOF
POSTGRES_PASSWORD=changeme_secure_password
JWT_SECRET=$(openssl rand -base64 32)
CORS_ORIGINS=http://localhost,https://yourdomain.com
EOF

# Start
docker compose up -d
```

---

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (v1.28+)
- kubectl configured
- Helm 3.x (optional, for Postgres)

### Namespace & Config

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: veritas
```

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: veritas-config
  namespace: veritas
data:
  DATABASE_URL: "postgresql://veritas:$(POSTGRES_PASSWORD)@postgres:5432/veritas"
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRE_MINUTES: "60"
  CORS_ORIGINS: "https://app.yourdomain.com"
```

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: veritas-secrets
  namespace: veritas
type: Opaque
stringData:
  POSTGRES_PASSWORD: "changeme_secure_password"
  JWT_SECRET: "your-32-byte-base64-secret"
  # Optional:
  # NVIDIA_API_KEY: ""
  # OPENAI_API_KEY: ""
```

### Postgres (via CloudNativePG or Helm)

```bash
# Option A: CloudNativePG (recommended for production)
kubectl apply -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.23/releases/cnpg-1.23.0.yaml

cat <<EOF | kubectl apply -f -
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: veritas-postgres
  namespace: veritas
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  storage:
    size: 10Gi
  bootstrap:
    initdb:
      database: veritas
      owner: veritas
      secret:
        name: veritas-postgres-credentials
EOF
```

```bash
# Option B: Helm (Bitnami)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install veritas-postgres bitnami/postgresql \
  --namespace veritas \
  --set auth.database=veritas \
  --set auth.username=veritas \
  --set auth.password=changeme_secure_password \
  --set primary.persistence.size=10Gi
```

### Backend Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: veritas-backend
  namespace: veritas
spec:
  replicas: 3
  selector:
    matchLabels:
      app: veritas-backend
  template:
    metadata:
      labels:
        app: veritas-backend
    spec:
      containers:
      - name: backend
        image: your-registry/veritas-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: veritas-config
        - secretRef:
            name: veritas-secrets
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "1000m"
```

```yaml
# k8s/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: veritas-backend
  namespace: veritas
spec:
  selector:
    app: veritas-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Frontend Deployment

```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: veritas-frontend
  namespace: veritas
spec:
  replicas: 2
  selector:
    matchLabels:
      app: veritas-frontend
  template:
    metadata:
      labels:
        app: veritas-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/veritas-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

```yaml
# k8s/frontend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: veritas-frontend
  namespace: veritas
spec:
  selector:
    app: veritas-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: veritas-ingress
  namespace: veritas
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.yourdomain.com
    - app.yourdomain.com
    secretName: veritas-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: veritas-backend
            port:
              number: 8000
  - host: app.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: veritas-frontend
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all
kubectl apply -f k8s/

# Check status
kubectl get pods -n veritas -w

# View logs
kubectl logs -n veritas -l app=veritas-backend -f

# Scale
kubectl scale deployment veritas-backend -n veritas --replicas=5
```

---

## Cloud Provider Quickstarts

### AWS (ECS Fargate + RDS + ALB)

```bash
# 1. Create RDS Postgres
aws rds create-db-instance \
  --db-instance-identifier veritas-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username veritas \
  --master-user-password changeme \
  --allocated-storage 20

# 2. Build & push images to ECR
aws ecr create-repository --repository-name veritas-backend
aws ecr create-repository --repository-name veritas-frontend

# Tag & push
docker tag veritas-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/veritas-backend:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/veritas-backend:latest

# 3. Create ECS services (use AWS Console or CloudFormation/CDK)
# - Task definition with backend + frontend containers
# - ALB with path-based routing (/api/* → backend, /* → frontend)
# - Secrets in AWS Secrets Manager
```

### Google Cloud (Cloud Run + Cloud SQL)

```bash
# 1. Create Cloud SQL Postgres
gcloud sql instances create veritas-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create veritas --instance=veritas-db
gcloud sql users create veritas --instance=veritas-db --password=changeme

# 2. Deploy to Cloud Run
gcloud run deploy veritas-backend \
  --image=gcr.io/PROJECT_ID/veritas-backend \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=DATABASE_URL="postgresql://veritas:changeme@/veritas?host=/cloudsql/PROJECT_ID:REGION:veritas-db" \
  --set-env-vars=JWT_SECRET="$(openssl rand -base64 32)" \
  --add-cloudsql-instances=PROJECT_ID:REGION:veritas-db

gcloud run deploy veritas-frontend \
  --image=gcr.io/PROJECT_ID/veritas-frontend \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated
```

### Azure (Container Apps + PostgreSQL Flexible Server)

```bash
# 1. Create Postgres
az postgres flexible-server create \
  --resource-group veritas-rg \
  --name veritas-db \
  --database-name veritas \
  --admin-user veritas \
  --admin-password changeme \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 16

# 2. Create Container Apps Environment
az containerapp env create \
  --name veritas-env \
  --resource-group veritas-rg \
  --location eastus

# 3. Deploy backend
az containerapp create \
  --name veritas-backend \
  --resource-group veritas-rg \
  --environment veritas-env \
  --image your-registry/veritas-backend:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars DATABASE_URL="postgresql://veritas:changeme@veritas-db.postgres.database.azure.com/veritas" JWT_SECRET="$(openssl rand -base64 32)"

# 4. Deploy frontend
az containerapp create \
  --name veritas-frontend \
  --resource-group veritas-rg \
  --environment veritas-env \
  --image your-registry/veritas-frontend:latest \
  --target-port 80 \
  --ingress external
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./veritas.db` | SQLAlchemy connection string |
| `JWT_SECRET` | Yes | — | 32+ byte base64 secret for JWT signing |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `JWT_EXPIRE_MINUTES` | No | `60` | Token expiry |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |
| `NVIDIA_API_KEY` | No | — | For LLM extraction fallback |
| `OPENAI_API_KEY` | No | — | Alternative LLM provider |
| `SEARCH_API_KEY` | No | — | For discovery agent |

---

## Database Migrations

```bash
# Install Alembic
pip install alembic

# Initialize (first time)
cd backend
alembic init migrations

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# In production (CI/CD):
alembic upgrade head
```

---

## Monitoring & Observability

### Health Checks
- `GET /api/health` — liveness/readiness

### Structured Logging (add to main.py)
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        })

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().handlers = [handler]
logging.getLogger().setLevel(logging.INFO)
```

### Prometheus Metrics (add prometheus-fastapi-instrumentator)
```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Key Metrics to Alert On
- Request latency (p95 > 2s)
- Error rate (5xx > 1%)
- DB connection pool exhaustion
- Disk space (for SQLite)
- Queue depth (if async workers added)

---

## Backup & Recovery

### Postgres
```bash
# Backup
pg_dump -h localhost -U veritas veritas > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U veritas veritas < backup_20240115.sql
```

### SQLite (dev only)
```bash
# Backup
cp veritas.db veritas.db.backup.$(date +%Y%m%d)

# Restore
cp veritas.db.backup.20240115 veritas.db
```

---

## Security Hardening

- [ ] Rotate `JWT_SECRET` periodically
- [ ] Enable HTTPS everywhere (TLS 1.2+)
- [ ] Set secure cookie flags (if using cookies)
- [ ] Implement rate limiting (per-IP, per-tenant)
- [ ] Add request validation/sanitization
- [ ] Regular dependency updates (`pip-audit`, `npm audit`)
- [ ] Secret scanning in CI/CD
- [ ] Penetration testing before go-live

---

## CI/CD Pipeline (GitHub Actions Example)

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: veritas
          POSTGRES_USER: veritas
          POSTGRES_PASSWORD: test
        ports: [5432:5432]
        options: >-
          --health-cmd "pg_isready -U veritas"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install backend deps
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd backend
          DATABASE_URL=postgresql://veritas:test@localhost:5432/veritas \
          JWT_SECRET=testsecret \
          pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build backend image
        run: docker build -t veritas-backend:${{ github.sha }} ./backend
      - name: Build frontend image
        run: docker build -t veritas-frontend:${{ github.sha }} ./frontend
      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USER }} --password-stdin
          docker push ${{ secrets.REGISTRY }}/veritas-backend:${{ github.sha }}
          docker push ${{ secrets.REGISTRY }}/veritas-frontend:${{ github.sha }}

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          # Update image tags in k8s manifests
          # kubectl set image deployment/veritas-backend backend=${{ secrets.REGISTRY }}/veritas-backend:${{ github.sha }} -n veritas
          # kubectl set image deployment/veritas-frontend frontend=${{ secrets.REGISTRY }}/veritas-frontend:${{ github.sha }} -n veritas
          echo "Deploy step - customize for your cluster"
```

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker logs veritas-backend

# Common issues:
# - DATABASE_URL wrong format
# - JWT_SECRET not set
# - Port 8000 already in use
# - PyMuPDF missing (PDF upload fails)
```

### Frontend can't reach API
- Check `VERITAS_API_BASE` in `frontend/app.js`
- Verify CORS settings in `main.py`
- Check network tab for failed requests

### Database errors
```bash
# Check connection
psql $DATABASE_URL -c "SELECT 1"

# Check migrations
alembic current
alembic heads
```

### PDF extraction fails
```bash
# Install PyMuPDF
pip install pymupdf

# Verify
python -c "import fitz; print(fitz.__version__)"
```

---

## Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| Backend API | Horizontal (stateless), add replicas behind load balancer |
| Database | Read replicas for SELECT-heavy workloads; vertical for writes |
| File uploads | Offload to S3/GCS, process async via queue |
| LLM/VLM calls | Dedicated GPU workers, batch requests |
| Discovery agent | Separate worker pool, rate-limited |

---

## Rollback Procedure

```bash
# Kubernetes
kubectl rollout undo deployment/veritas-backend -n veritas
kubectl rollout undo deployment/veritas-frontend -n veritas

# Docker Compose
docker compose down
docker tag veritas-backend:previous veritas-backend:latest
docker compose up -d

# Database (if migration caused issue)
alembic downgrade -1
```