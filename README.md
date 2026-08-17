# Veritas — Industrial Product Intelligence, Verified

> **End-to-end MVP:** Ingest conflicting product data from multiple sources (datasheets, manufacturer websites, distributor ERPs), automatically detect and resolve conflicts with full evidence trails, score data quality, and route low-confidence attributes to human review.

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) | **Start here** — what this is, why it exists, architectural philosophy |
| [STATUS_AND_ROADMAP.md](STATUS_AND_ROADMAP.md) | What's working, what's stubbed, what's next |
| [docs/API.md](docs/API.md) | Complete REST API reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture, module internals, extension points |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker, Kubernetes, cloud provider quickstarts |
| [frontend/README.md](frontend/README.md) | Frontend dashboard architecture |

---

## What This Project Is (and Isn't)

### ✅ It IS
- A **verification and arbitration layer** that sits upstream of your existing PIM/ERP
- The **arbitration engine** (`backend/app/arbitration.py`) — decides which disagreeing source to trust, by how much, and shows its work
- **Evidence-first**: every resolved value carries source, location, raw snippet, reasoning, and confidence
- **Human-in-the-loop by default**: low-confidence attributes route to review, never silently auto-published
- **Industrial-grade classification**: ETIM/ECLASS/UNSPSC mapping (demo scope: 2 categories)

### ❌ It is NOT
- A PIM replacement (Akeneo, Salsify, inRiver, Pimcore, Stibo own that)
- "An AI that reads PDFs" — extraction is commodity; arbitration is the moat
- A generic document processor — purpose-built for industrial product specs

---

## Repository Structure

```
veritas/
├── PROBLEM_STATEMENT.md          ← Read first (AI agents: start here)
├── STATUS_AND_ROADMAP.md         ← Honest status: done vs stubbed vs future
├── README.md                     ← This file
├── docs/
│   ├── API.md                    ← Complete REST API reference
│   ├── ARCHITECTURE.md           ← System design, module deep-dives
│   └── DEPLOYMENT.md             ← Docker, K8s, cloud quickstarts
├── backend/
│   ├── app/
│   │   ├── main.py               ← FastAPI app, all endpoints
│   │   ├── extraction.py         ← Pattern/LLM/Vision extraction
│   │   ├── arbitration.py        ← CORE: conflict resolution + confidence
│   │   ├── classification.py     ← ETIM/ECLASS/UNSPSC mapping
│   │   ├── graph.py              ← Product relationships
│   │   ├── export.py             ← JSON, Akeneo CSV export
│   │   ├── learning.py           ← Bayesian reliability learning
│   │   ├── database.py           ← SQLAlchemy + SQLite/Postgres
│   │   ├── models.py             ← ORM models
│   │   ├── auth.py               ← JWT auth, tenant isolation
│   │   ├── services/
│   │   │   ├── llm_extraction.py    ← LLM fallback for extraction
│   │   │   ├── vision_extraction.py ← VLM for nameplate images
│   │   │   └── discovery.py         ← Auto-datasheet discovery
│   │   └── sample_data/          ← 3 genuinely conflicting sources for 1 PLC SKU
│   ├── tests/
│   │   ├── test_arbitration.py
│   │   ├── test_arbitration_extended.py
│   │   └── test_extraction.py
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── styles.css
    └── app.js                    ← Vanilla JS dashboard (no build step)
```

---

## Running the Project

### Prerequisites
- Python 3.11+
- (Optional) Node.js for frontend tooling — **not required**

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Optional: configure environment
cp .env.example .env  # edit if needed

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
# Option 1: Open directly (may have CORS issues)
open index.html

# Option 2: Static server (recommended)
python -m http.server 5500
# Open http://localhost:5500
```

### Run Demo
1. Start backend (`uvicorn app.main:app --reload --port 8000`)
2. Open frontend
3. Click **"Run demo pipeline"** in top bar
4. Watch the Siemens PLC SKU with 3 conflicting sources resolve through the pipeline

---

## API Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Get JWT token |
| `POST` | `/api/auth/register` | Register new tenant |
| `POST` | `/api/ingest` | Ingest text/CSV sources, run full pipeline |
| `POST` | `/api/ingest/upload` | Upload files (PDF, CSV, images) |
| `POST` | `/api/ingest/discover` | Auto-discover datasheet + run pipeline |
| `GET` | `/api/demo/run` | Run bundled demo dataset |
| `GET` | `/api/products` | List all products (tenant-scoped) |
| `GET` | `/api/products/{id}` | Full product record with evidence |
| `POST` | `/api/products/{id}/review` | Approve/edit/reject attribute |
| `GET` | `/api/products/{id}/ask?q=` | Natural-language Q&A over evidence |
| `GET` | `/api/products/{id}/export?format=` | Export JSON or Akeneo CSV |
| `GET` | `/api/reliability` | View learned vs static reliability weights |
| `GET` | `/api/health` | Health check |

**Interactive docs:** `http://localhost:8000/docs` (Swagger) / `http://localhost:8000/redoc` (ReDoc)

---

## Core Concepts

### Source Reliability Weighting
| Source Type | Static Prior | Description |
|-------------|--------------|-------------|
| `datasheet` | 0.95 | Manufacturer datasheet |
| `image_label` | 0.90 | Photo of nameplate |
| `manufacturer_website` | 0.75 | Official product page |
| `catalog_pdf` | 0.70 | Catalog excerpt |
| `distributor_erp` | 0.55 | Distributor system export |
| `unknown` | 0.40 | Fallback |

**Phase 5:** These become **learned per-tenant** via Bayesian Beta-Binomial model updated on every human review action.

### Attribute Resolution Statuses
| Status | Meaning |
|--------|---------|
| `agreed` | All sources agree within tolerance |
| `resolved_conflict` | Conflict detected, resolved to highest-reliability source |
| `unresolved_conflict` | Conflict + low confidence → **routed to human review** |
| `single_source` | Only one source reports this attribute |
| `human_approved` | Reviewer approved automated resolution |
| `human_corrected` | Reviewer provided corrected value |
| `rejected` | Reviewer rejected the attribute |

### Quality Score
```
overall_score = 50% × completeness + 50% × avg_confidence
```
- `completeness`: % of expected attributes found
- `avg_confidence`: mean confidence across all resolved attributes
- `needs_review`: attributes with `unresolved_conflict` or confidence < 0.75

---

## Feeding Your Own Data

### Via API (JSON)
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Your Product",
    "product_id": "SKU-123",
    "sources": [
      {
        "source_id": "src_1",
        "source_type": "datasheet",
        "format": "text",
        "raw_content": "Supply voltage: 24 V DC\nWeight: 1.5 kg\n...",
        "location_hint": "Page 3"
      }
    ]
  }'
```

### Via File Upload
```bash
curl -X POST http://localhost:8000/api/ingest/upload \
  -H "Authorization: Bearer <token>" \
  -F "product_name=Your Product" \
  -F "product_id=SKU-123" \
  -F "source_ids=src_1" \
  -F "source_types=datasheet" \
  -F "files=@datasheet.pdf"
```

---

## Extending the Pipeline

### Add New Attributes
1. Add regex pattern to `backend/app/extraction.py` → `TEXT_PATTERNS`
2. Add attribute key to `backend/app/main.py` → `EXPECTED_ATTRIBUTES`
3. Test with conflicting sources

### Add New Source Types
1. Add entry to `SOURCE_RELIABILITY` in `arbitration.py`
2. Handle extraction format if needed
3. Learning adapts weights automatically per-tenant

### Add Export Connectors
```python
# backend/app/export.py
def export_to_salsify(record): ...

# Register in main.py
EXPORT_FORMATS["salsify"] = export_to_salsify
```

### Swap Extraction for LLM/VLM
Replace `extract_from_text()` in `extraction.py` — arbitration downstream unchanged.

---

## Testing

```bash
cd backend
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=html
```

---

## Configuration

Create `.env` in `backend/`:
```bash
# Database (SQLite default, Postgres for production)
DATABASE_URL=sqlite:///./veritas.db
# DATABASE_URL=postgresql://user:pass@host:5432/veritas

# Auth
JWT_SECRET=your-32-byte-base64-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS (lock down before production!)
CORS_ORIGINS=http://localhost:5500,https://yourdomain.com

# Optional: LLM extraction fallback
NVIDIA_API_KEY=...
OPENAI_API_KEY=...

# Optional: Discovery agent
SEARCH_API_KEY=...
```

---

## Production Checklist

- [ ] PostgreSQL (not SQLite) — set `DATABASE_URL`
- [ ] Strong `JWT_SECRET` (32+ random bytes)
- [ ] Restrict `CORS_ORIGINS` to your domains
- [ ] Rate limiting middleware
- [ ] Request size limits for uploads
- [ ] Structured JSON logging
- [ ] Health checks for orchestration
- [ ] Database migrations (Alembic)
- [ ] SSL/TLS termination
- [ ] Monitoring/alerting
- [ ] Backup strategy
- [ ] Load testing

---

## License

MIT License — see [LICENSE](LICENSE) if present.

---

## Contributing

1. Read [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) and [STATUS_AND_ROADMAP.md](STATUS_AND_ROADMAP.md)
2. Check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for extension points
3. Run tests: `cd backend && pytest tests/`
4. Open PR with clear description of what arbitration/trust capability it improves

---

## Acknowledgments

- **UniHack 2024** competition submission
- Industrial product data standards: ETIM, ECLASS, UNSPSC, Unilog
- Siemens sample data for demo (publicly available datasheets)