# Architecture & Developer Guide — Veritas

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VERITAS PIPELINE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌─────────────┐    ┌────────────┐    ┌────────────────┐  │
│  │  SOURCES │───▶│ EXTRACTION  │───▶│ ARBITRATION │───▶│  CLASSIFICATION │  │
│  │  (files, │    │ (regex/LLM/ │    │ (conflict  │    │  (ETIM/ECLASS/ │  │
│  │   text)  │    │  vision)    │    │  resolution│    │   UNSPSC)      │  │
│  └──────────┘    └─────────────┘    └────────────┘    └────────────────┘  │
│       │                │                 │                   │             │
│       │                │                 ▼                   │             │
│       │                │         ┌─────────────┐             │             │
│       │                │         │  QUALITY    │             │             │
│       │                │         │  SCORE      │             │             │
│       │                │         └─────────────┘             │             │
│       │                │                 │                   │             │
│       ▼                ▼                 ▼                   ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    PERSISTENCE (SQLAlchemy + SQLite/Postgres)       │  │
│  │  Product, CustomerReliability, ReviewLog                            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                      HUMAN REVIEW LOOP                              │  │
│  │  approve / edit / reject  ──▶  update confidence  ──▶  learn weights│  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                            │
│                              ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                        EXPORT CONNECTORS                            │  │
│  │  JSON, Akeneo CSV, (future: Salsify, inRiver, Pimcore, custom)    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Modules

### 1. Extraction (`backend/app/extraction.py`)

**Purpose:** Convert raw documents → candidate attribute observations.

**Input formats:**
- Plain text (from PDF, web scraping, manual paste)
- CSV (structured rows)
- PDF bytes (via PyMuPDF)
- Images (via vision-language model stub)

**Output:** List of observations:
```python
{
    "attribute": "supply_voltage_rated",
    "value": 24.0,
    "value_range": None,
    "unit": "V DC",
    "raw_snippet": "Supply voltage: 24 V DC",
    "location": "Page 12",
    "extracted_by": "regex"  # or "llm", "vision"
}
```

**Extension points:**
- Add patterns to `TEXT_PATTERNS` list
- Implement `extract_with_llm()` in `services/llm_extraction.py`
- Implement `extract_with_vision()` in `services/vision_extraction.py`

**Key design decision:** Pattern-based (regex) for zero-API demo. Production swaps in LLM/VLM. Arbitration downstream doesn't care how observations were produced.

---

### 2. Arbitration (`backend/app/arbitration.py`) — **THE CORE**

**Purpose:** Decide which conflicting source to trust, with evidence and reasoning.

**Algorithm:**
1. Group observations by attribute across all sources
2. Sort candidates by source reliability (learned or static prior)
3. Partition into "agreeing" vs "disagreeing" with top candidate (using numeric tolerance)
4. Assign status and confidence:
   - `single_source`: only one source → confidence = reliability × 0.85
   - `agreed`: all agree → confidence = avg reliability + corroboration bonus
   - `resolved_conflict`: conflict exists → confidence = top reliability - penalty + reliability_gap bonus
   - `unresolved_conflict`: confidence < 0.60 → flagged for human review

**Key parameters:**
- `SOURCE_RELIABILITY`: static prior table (source_type → 0–1)
- `NUMERIC_TOLERANCE`: 8% relative difference = noise, not conflict
- `reliability_overrides`: learned weights from Phase 5 (per-tenant)

**Output per attribute:**
```python
{
    "resolved_value": 1.35,
    "unit": "kg",
    "status": "resolved_conflict",
    "confidence": 0.78,
    "reasoning": "Conflict detected. Resolved to datasheet (Page 12)...",
    "evidence": [...]
}
```

---

### 3. Classification (`backend/app/classification.py`)

**Purpose:** Map product name/description → ETIM, ECLASS, UNSPSC codes.

**Current state:** Demo scope — 2 categories (PLC controllers, temperature sensors) with hand-picked codes.

**Extension:** Licensed ETIM/ECLASS data required for production coverage.

---

### 4. Graph (`backend/app/graph.py`)

**Purpose:** Product relationships (family, compatible, replacements).

**Current state:** Hardcoded dict for one SKU.

**Extension:** Neo4j-backed, populated from manufacturer data during ingestion.

---

### 5. Learning (`backend/app/learning.py`)

**Purpose:** Bayesian Beta-Binomial model for per-tenant source reliability learning.

**Mechanism:**
- Each source_type has a Beta(α, β) distribution
- On review: if human approves top source → α += 1; if human corrects to disagreeing source → β += 1 for top, α += 1 for chosen
- Posterior mean = α / (α + β) used as learned weight
- Minimum 5 observations before learned weight overrides static prior

**Tables:** `CustomerReliability` (tenant_id, source_type, alpha, beta, updated_at)

---

### 6. Export (`backend/app/export.py`)

**Formats:**
- **JSON:** Full product record
- **Akeneo CSV:** Mapped to Akeneo PIM attribute structure

**Extension:** Add new exporters in `export.py`, register in `main.py`.

---

### 7. Discovery (`backend/app/services/discovery.py`)

**Purpose:** Auto-find manufacturer datasheets for a SKU.

**Current state:** Mock implementation returning sample data.

**Extension:** Integrate with search APIs (Google, Bing) or manufacturer site crawlers.

---

### 8. Auth (`backend/app/auth.py`)

**Purpose:** JWT authentication with tenant isolation.

**Features:**
- Register/login endpoints
- Password hashing (bcrypt)
- JWT tokens (HS256, 1hr expiry)
- `get_current_tenant` dependency for multi-tenant isolation

---

## Database Schema

### Product
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR NOT NULL,
    product_id VARCHAR NOT NULL,
    product_name VARCHAR,
    version INTEGER DEFAULT 1,  -- optimistic locking
    attributes_json JSON NOT NULL,
    quality_json JSON,
    classification_json JSON,
    related_json JSON,
    sources_json JSON,
    review_log_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, product_id)
);
```

### CustomerReliability
```sql
CREATE TABLE customer_reliability (
    id INTEGER PRIMARY KEY,
    tenant_id VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    alpha REAL DEFAULT 1.0,  -- Beta distribution parameter
    beta REAL DEFAULT 1.0,   -- Beta distribution parameter
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, source_type)
);
```

---

## Data Flow: Ingestion Pipeline

```
POST /api/ingest
       │
       ▼
┌──────────────────┐
│ _run_pipeline()  │  (main.py:99)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────────────┐
│ For each source: │     │ observations_by_source  │
│  text → extract  │────▶│ {                       │
│  csv → extract   │     │   "source_a": {         │
│  pdf → extract   │     │     "source_type": "...",│
│                  │     │     "observations": [...]│
└──────────────────┘     │   }, ...               │
         │               └─────────────────────────┘
         ▼
┌──────────────────┐
│ learning.get_    │
│ learned_weights()│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────────────┐
│ arbitration.ar-  │────▶│ resolved {attr: record} │
│ bitrate()        │     └─────────────────────────┘
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ compute_quality_ │
│ score()          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ classification.  │
│ classify()       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ graph.get_       │
│ related()        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ _save_product()  │  (upsert with optimistic locking)
└──────────────────┘
```

---

## Adding New Attributes

1. **Add extraction pattern** in `extraction.py` → `TEXT_PATTERNS`
2. **Add to expected list** in `main.py` → `EXPECTED_ATTRIBUTES`
3. **Add normalization** if needed (unit conversion, range parsing)
4. **Test arbitration** with conflicting sources

**Example — adding `operating_current`:**
```python
# extraction.py
TEXT_PATTERNS.append((
    "operating_current",
    re.compile(r"Operating current[:\s]*(\d+(?:\.\d+)?)\s*A", re.I),
    "A"
))

# main.py
EXPECTED_ATTRIBUTES.append("operating_current")
```

---

## Adding New Source Types

1. **Add to `SOURCE_RELIABILITY`** in `arbitration.py` with initial prior
2. **Handle in extraction** if format differs (e.g., new file type)
3. **Learning will adapt** weights per-tenant automatically

---

## Extending Classification

1. Obtain licensed ETIM/ECLASS/UNSPSC data
2. Load into lookup tables (SQLite or Postgres)
3. Replace `classification.py` keyword matching with proper lookup
4. Add confidence scoring based on match quality

---

## Extending Export Connectors

```python
# export.py
def export_to_salsify(record: Dict) -> tuple[str, str, bytes]:
    # Transform to Salsify format
    return "application/json", "salsify_export.json", json.dumps(...).encode()

# Register in main.py
EXPORT_FORMATS = {
    "json": exporter.export_json,
    "akeneo_csv": exporter.export_akeneo_csv,
    "salsify": export_to_salsify,
}
```

---

## Testing

```bash
# Run all tests
cd backend
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_arbitration.py -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**Test files:**
- `tests/test_arbitration.py` — Core arbitration logic
- `tests/test_arbitration_extended.py` — Edge cases, learning integration
- `tests/test_extraction.py` — Pattern extraction

---

## Configuration

Environment variables (`.env`):
```bash
# Database
DATABASE_URL=sqlite:///./veritas.db  # or postgresql://user:pass@host/db

# Auth
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# LLM (Phase 2+)
NVIDIA_API_KEY=...
OPENAI_API_KEY=...

# Discovery (Phase 7+)
SEARCH_API_KEY=...
```

---

## Production Checklist

- [ ] Lock down CORS: `allow_origins=["https://your-domain.com"]`
- [ ] Use Postgres (not SQLite) — set `DATABASE_URL`
- [ ] Strong `JWT_SECRET` (32+ random bytes)
- [ ] Rate limiting middleware
- [ ] Request size limits for file uploads
- [ ] Structured logging (JSON) + log aggregation
- [ ] Health checks for orchestration (k8s, ECS, etc.)
- [ ] Database migrations (Alembic)
- [ ] SSL/TLS termination
- [ ] Monitoring/alerting (Prometheus, Datadog, etc.)
- [ ] Backup strategy for database
- [ ] Load testing

---

## Directory Structure

```
veritas/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, all endpoints
│   │   ├── extraction.py        # Pattern/LLM/vision extraction
│   │   ├── arbitration.py       # CORE: conflict resolution
│   │   ├── classification.py    # ETIM/ECLASS/UNSPSC mapping
│   │   ├── graph.py             # Product relationships
│   │   ├── export.py            # JSON, Akeneo CSV export
│   │   ├── learning.py          # Bayesian reliability learning
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # ORM models
│   │   ├── auth.py              # JWT auth, tenant isolation
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm_extraction.py    # LLM fallback
│   │   │   ├── vision_extraction.py # VLM for images
│   │   │   └── discovery.py         # Datasheet discovery
│   │   └── sample_data/         # Demo sources (intentionally conflicting)
│   ├── tests/
│   │   ├── test_arbitration.py
│   │   ├── test_arbitration_extended.py
│   │   └── test_extraction.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js                   # Vanilla JS dashboard
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── PROBLEM_STATEMENT.md
├── STATUS_AND_ROADMAP.md
└── README.md
```