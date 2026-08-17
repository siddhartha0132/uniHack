# API Reference — Veritas Industrial Product Intelligence

Base URL: `http://localhost:8000` (development)

All endpoints require authentication via JWT Bearer token (except `/api/health`). See [Authentication](#authentication).

---

## Authentication

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "company_name": "Acme Industrial"
}
```

### Usage
Include the token in subsequent requests:
```
Authorization: Bearer <access_token>
```

---

## Health Check

### GET /api/health
Returns service status and version.

**Response:**
```json
{
  "status": "ok",
  "version": "0.2.0"
}
```

---

## Product Ingestion

### POST /api/ingest
Run the full pipeline on provided sources (text/CSV).

**Request:**
```json
{
  "product_name": "SIMATIC S7-1200 CPU 1214C",
  "product_id": "6ES7214-1AG40-0XB0",
  "sources": [
    {
      "source_id": "source_a",
      "source_type": "datasheet",
      "format": "text",
      "raw_content": "Supply voltage: 24 V DC\nWeight: 1.35 kg\n...",
      "location_hint": "Page 12"
    }
  ]
}
```

**Source Types & Reliability Weights:**
| source_type | static_prior | description |
|-------------|--------------|-------------|
| datasheet | 0.95 | Manufacturer datasheet (highest trust) |
| image_label | 0.90 | Photo of nameplate/label |
| manufacturer_website | 0.75 | Official product page |
| catalog_pdf | 0.70 | Catalog excerpt |
| distributor_erp | 0.55 | Distributor system export |
| unknown | 0.40 | Fallback |

**Response:** Full product record with resolved attributes, quality score, classification, and related products.

---

### POST /api/ingest/upload
Upload files directly (PDF, CSV, images, text). Multipart/form-data.

**Form Fields:**
| field | type | description |
|-------|------|-------------|
| product_name | string | Product name |
| product_id | string | SKU/part number |
| source_ids[] | string[] | Parallel array: source_id per file |
| source_types[] | string[] | Parallel array: source_type per file |
| files[] | file[] | Files to upload |

**Supported formats:** `.pdf`, `.csv`, `.txt`, `.jpg`, `.jpeg`, `.png`

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/ingest/upload" \
  -H "Authorization: Bearer <token>" \
  -F "product_name=Test Product" \
  -F "product_id=SKU-001" \
  -F "source_ids=src1" \
  -F "source_types=datasheet" \
  -F "files=@datasheet.pdf"
```

---

### POST /api/ingest/discover
Auto-discover a datasheet for a product SKU if no sources provided.

**Request:** Same as `/api/ingest` but `sources` can be empty.

**Response:** Full product record (uses discovery agent to find datasheet).

---

### GET /api/demo/run
Run the bundled demo dataset (Siemens PLC with 3 conflicting sources).

**Response:** Full product record for `6ES7214-1AG40-0XB0`.

---

## Product Retrieval

### GET /api/products
List all products for current tenant.

**Response:**
```json
[
  {
    "product_id": "6ES7214-1AG40-0XB0",
    "product_name": "SIMATIC S7-1200 CPU 1214C",
    "overall_score": 87.5,
    "needs_review": 2
  }
]
```

---

### GET /api/products/{product_id}
Get full product record with all attributes, evidence, and review log.

**Response:**
```json
{
  "product_id": "6ES7214-1AG40-0XB0",
  "product_name": "SIMATIC S7-1200 CPU 1214C",
  "attributes": {
    "weight": {
      "resolved_value": 1.35,
      "unit": "kg",
      "status": "resolved_conflict",
      "confidence": 0.78,
      "reasoning": "Conflict detected. Resolved to datasheet (Page 12) as highest-reliability source...",
      "evidence": [
        {
          "source_id": "source_a",
          "source_type": "datasheet",
          "location": "Page 12",
          "raw_snippet": "Weight: 1.35 kg",
          "value": 1.35,
          "unit": "kg",
          "agrees_with_resolution": true
        },
        {
          "source_id": "source_b",
          "source_type": "manufacturer_website",
          "location": "Product page",
          "raw_snippet": "Weight: 1.2 kg",
          "value": 1.2,
          "unit": "kg",
          "agrees_with_resolution": false
        }
      ]
    }
  },
  "quality": {
    "overall_score": 87.5,
    "completeness": 100.0,
    "avg_confidence": 75.0,
    "conflicts_detected": 2,
    "needs_review": ["weight", "operating_temp_range"],
    "missing_attributes": [],
    "explanation": "6/6 expected attributes found. 4/6 attributes agreed across sources without conflict..."
  },
  "classification": {
    "etim_class": "EC000234",
    "eclass_class": "27-01-01-01",
    "unspsc_class": "43-21-15-01",
    "confidence": 0.92
  },
  "related": {
    "family": ["6ES7214-1AG40-0XB0"],
    "compatible": ["6ES7214-1BG40-0XB0"],
    "replacements": []
  },
  "review_log": [],
  "sources": [...],
  "tenant_id": "tenant_abc123",
  "_version": 1
}
```

---

## Human Review

### POST /api/products/{product_id}/review
Approve, edit, or reject an attribute. Updates confidence, quality score, and learned reliability.

**Request:**
```json
{
  "attribute": "weight",
  "action": "edit",
  "corrected_value": 1.38,
  "reviewer": "jane.doe@company.com"
}
```

**Actions:**
| action | effect |
|--------|--------|
| approve | status → `human_approved`, confidence → max(current, 0.95) |
| edit | resolved_value → corrected_value, status → `human_corrected`, confidence → 0.98 |
| reject | status → `rejected`, confidence → 0.0 |

**Response:** Updated product record with recomputed quality score.

---

## Q&A (Retrieval-lite)

### GET /api/products/{product_id}/ask?q={question}
Natural-language question over stored evidence. Uses alias expansion + keyword matching (stand-in for RAG).

**Example queries:**
- `GET /api/products/6ES7214-1AG40-0XB0/ask?q=what is the weight`
- `GET /api/products/6ES7214-1AG40-0XB0/ask?q=voltage`
- `GET /api/products/6ES7214-1AG40-0XB0/ask?q=operating temperature range`

**Response:**
```json
{
  "answer": "weight: 1.35 kg",
  "confidence": 0.78,
  "reasoning": "Conflict detected. Resolved to datasheet (Page 12) as highest-reliability source...",
  "evidence": [...]
}
```

---

## Export

### GET /api/products/{product_id}/export?format={json|akeneo_csv}
Export processed product record.

**Formats:**
| format | description |
|--------|-------------|
| json | Full record as JSON |
| akeneo_csv | Akeneo-compatible CSV for PIM import |

**Response:** File download with appropriate Content-Type and Content-Disposition headers.

---

## Reliability Weights (Phase 5)

### GET /api/reliability
View current learned reliability weights vs static priors.

**Response:**
```json
{
  "learned_weights": {
    "datasheet": 0.96,
    "manufacturer_website": 0.72,
    "distributor_erp": 0.58
  },
  "static_priors": {
    "datasheet": 0.95,
    "image_label": 0.90,
    "manufacturer_website": 0.75,
    "catalog_pdf": 0.70,
    "distributor_erp": 0.55,
    "unknown": 0.40
  },
  "note": "learned_weights override static_priors during arbitration when present"
}
```

**Mechanism:** Bayesian Beta-Binomial model updated on every review action. See `backend/app/learning.py`.

---

## Error Responses

All endpoints return standard HTTP status codes:
- `200` — Success
- `400` — Bad request (validation error)
- `401` — Unauthorized (invalid/missing token)
- `404` — Not found
- `409` — Conflict (optimistic locking version mismatch)
- `500` — Internal server error

**Error format:**
```json
{
  "detail": "Human-readable error message"
}
```

---

## Data Models

### SourceInput
| field | type | required | description |
|-------|------|----------|-------------|
| source_id | string | yes | Unique identifier for this source |
| source_type | string | yes | One of: datasheet, manufacturer_website, distributor_erp, image_label, catalog_pdf, unknown |
| format | string | yes | "text" or "csv" |
| raw_content | string | yes | Raw text or CSV content |
| location_hint | string | no | Page, section, or row hint |

### Attribute Observation (internal)
| field | type | description |
|-------|------|-------------|
| attribute | string | Normalized key (snake_case) |
| value | number/string/null | Normalized value (or null for ranges) |
| value_range | [number, number] | Min/max for range attributes |
| unit | string | Unit of measure |
| raw_snippet | string | Exact text snippet for evidence |
| location | string | Page, row, or section |
| extracted_by | string | "regex", "llm", or "vision" |

### Resolved Attribute
| field | type | description |
|-------|------|-------------|
| resolved_value | any | Final chosen value |
| unit | string | Unit of measure |
| status | string | agreed, resolved_conflict, unresolved_conflict, single_source, human_approved, human_corrected, rejected |
| confidence | float | 0.0–1.0 |
| reasoning | string | Human-readable explanation |
| evidence | array | Full evidence trail (see above) |

### Quality Score
| field | type | description |
|-------|------|-------------|
| overall_score | float | 0–100 (50% completeness + 50% avg confidence) |
| completeness | float | % of expected attributes found |
| avg_confidence | float | Average confidence across all attributes |
| conflicts_detected | int | Number of attributes with conflicts |
| needs_review | string[] | Attributes below confidence threshold or unresolved |
| missing_attributes | string[] | Expected but not found |
| explanation | string | Plain-language summary |

---

## Rate Limits & Quotas

Currently no rate limiting (demo). Before production:
- Add rate limiting middleware
- Configure per-tenant quotas
- Add request size limits for file uploads

---

## Versioning

Current API version: `0.2.0` (pre-1.0, breaking changes possible).
Version returned in `/api/health` and FastAPI OpenAPI spec at `/docs`.

---

## OpenAPI / Swagger UI

Interactive docs available at:
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/redoc` — ReDoc