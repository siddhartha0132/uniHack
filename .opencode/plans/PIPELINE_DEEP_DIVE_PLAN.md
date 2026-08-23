# Plan: Expand VERITAS PIPELINE Section with Deep Technical Details

## Objective
Replace the current simple ASCII diagram (lines 32-46 in DEMO_SCRIPT.md) with a comprehensive, in-depth technical breakdown of the Veritas pipeline that demonstrates the full depth of the system for the demo video and technical audience.

---

## Current State (What Exists)
- Lines 34-46: Simple 4-stage ASCII diagram + tech stack bullet list
- No details on data structures, algorithms, or internal flow

---

## Target State (What to Add)

### 1. Pipeline Stage Deep-Dive (6 Stages)
For each stage: **Input → Process → Output → Key Code Module → Data Structure**

| Stage | Input | Core Logic | Output | Module |
|-------|-------|------------|--------|--------|
| **1. Ingestion** | Raw files (PDF, TXT, CSV, IMG) + metadata | Multi-format parsing, text extraction, page/row location tracking | `SourceInput` objects with `raw_content`, `location_hint` | `main.py:_run_pipeline()`, `extraction.py:extract_from_pdf_bytes/text/csv` |
| **2. Extraction** | Clean text per source | Regex patterns (7 attrs) + LLM fallback (NVIDIA NIM) + VLM for images | `Observation[]`: `{attribute, value, unit, raw_snippet, location, extracted_by}` | `extraction.py:extract_from_text()`, `services/llm_extraction.py`, `services/vision_extraction.py` |
| **3. Arbitration** | `Observation[]` grouped by source | Reliability-weighted conflict resolution with 8% numeric tolerance | `ResolvedAttribute[]`: `{resolved_value, confidence, status, reasoning, evidence[]}` | `arbitration.py:arbitrate()`, `arbitration.py:_values_agree()`, `learning.py:get_learned_weights()` |
| **4. Classification** | Product name + description | Keyword matching against ETIM/ECLASS/UNSPSC lookup table | `{etim_class, eclass_code, unspsc, category}` | `classification.py:classify()`, `CLASSIFICATION_TABLE` |
| **5. Quality Scoring** | Resolved attributes + expected list | Completeness (50%) + Avg Confidence (50%) + conflict/review flags | `{overall_score, completeness, avg_confidence, conflicts, needs_review[]}` | `arbitration.py:compute_quality_score()` |
| **6. Export** | Full product record | JSON (clean) + Akeneo CSV (PIM-ready) | File download | `export.py:to_generic_json()`, `export.py:to_akeneo_csv()` |

---

### 2. Data Flow with Concrete Types

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VERITAS PIPELINE DATA FLOW                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SOURCES                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │
│  │  PDF/Doc    │  │  Web/HTML   │  │  CSV/ERP    │   →  extract_from_*()  │
│  │  (PyMuPDF)  │  │  (requests) │  │  (csv)      │                        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                        │
│         │                │                │                                │
│         ▼                ▼                ▼                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OBSERVATIONS (per source)                                          │   │
│  │  [{attribute: "weight", value: 1.35, unit: "kg",                   │   │
│  │    raw_snippet: "Weight: 1.35 kg", location: "Page 24",            │   │
│  │    extracted_by: "regex", source_id: "source_a",                   │   │
│  │    source_type: "datasheet", reliability: 0.95} ...]               │   │
│  └────────────────────────┬────────────────────────────────────────────┘   │
│                           │                                                │
│                           ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ARBITRATION ENGINE (core moat)                                    │   │
│  │                                                                      │   │
│  │  1. GROUP by attribute across sources                              │   │
│  │     weight: [obs_a(1.35), obs_b(1.2), obs_c(1.4)]                 │   │
│  │                                                                      │   │
│  │  2. SORT by source reliability (datasheet=0.95 > website=0.75)    │   │
│  │                                                                      │   │
│  │  3. PARTITION: agreeing vs disagreeing (8% tolerance)             │   │
│  │     1.35 vs 1.4 = 3.6% ✓ agrees  |  1.35 vs 1.2 = 12.5% ✗        │   │
│  │                                                                      │   │
│  │  4. RESOLVE: highest-reliability wins conflicts                   │   │
│  │     weight → 1.35 (datasheet)                                     │   │
│  │                                                                      │   │
│  │  5. SCORE CONFIDENCE:                                              │   │
│  │     - agreed: avg_reliability + corroboration_bonus               │   │
│  │     - resolved_conflict: top_reliability - 0.20 + reliability_gap │   │
│  │     - single_source: reliability * 0.85                           │   │
│  │                                                                      │   │
│  │  6. LEARNED WEIGHTS OVERRIDE: Beta(alpha, beta) per source_type   │   │
│  │     learned = alpha/(alpha+beta) from human reviews               │   │
│  └────────────────────────┬────────────────────────────────────────────┘   │
│                           │                                                │
│                           ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RESOLVED ATTRIBUTES                                                 │   │
│  │  {                                                                   │   │
│  │    "weight": {                                                       │   │
│  │      "resolved_value": 1.35, "unit": "kg",                          │   │
│  │      "confidence": 0.79, "status": "resolved_conflict",             │   │
│  │      "reasoning": "Conflict detected. Resolved to datasheet...",    │   │
│  │      "evidence": [                                                   │   │
│  │        {"source_id": "source_a", "source_type": "datasheet",        │   │
│  │         "location": "Page 24", "value": 1.35, "agrees": true},     │   │
│  │        {"source_id": "source_b", "source_type": "manufacturer_",    │   │
│  │         "location": "Product page", "value": 1.2, "agrees": false} │   │
│  │      ]                                                               │   │
│  │    },                                                                │   │
│  │    ... (5 more attributes)                                           │   │
│  │  }                                                                   │   │
│  └────────────────────────┬────────────────────────────────────────────┘   │
│                           │                                                │
│           ┌──────────────┼──────────────┐                                 │
│           ▼              ▼              ▼                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                      │
│  │ CLASSIFY     │ │ QUALITY      │ │ GRAPH        │                      │
│  │ (ETIM/       │ │ SCORE        │ │ (related)    │                      │
│  │  ECLASS/     │ │ (50% comp +  │ │              │                      │
│  │  UNSPSC)     │ │  50% conf)   │ │              │                      │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘                      │
│         │                │                │                                │
│         └────────────────┼────────────────┘                                │
│                          ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FULL PRODUCT RECORD (persisted to SQLite/Postgres)                │   │
│  │  { product_id, product_name, attributes, quality, classification, │   │
│  │    related, sources, review_log, tenant_id, version }             │   │
│  └────────────────────────┬────────────────────────────────────────────┘   │
│                           │                                                │
│              ┌────────────┼────────────┐                                  │
│              ▼            ▼            ▼                                  │
│       ┌───────────┐ ┌───────────┐ ┌───────────┐                          │
│       │ EXPORT    │ │ HUMAN     │ │ Q&A       │                          │
│       │ JSON/CSV  │ │ REVIEW    │ │ (ask)     │                          │
│       └───────────┘ └───────────┘ └───────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Arbitration Algorithm Detail (The Moat)

**Conflict Detection:**
```python
NUMERIC_TOLERANCE = 0.08  # 8% relative difference

def _values_agree(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == 0 and b == 0: return True
        denom = max(abs(a), abs(b), 1e-9)
        return abs(a - b) / denom <= 0.08
    return str(a).strip().lower() == str(b).strip().lower()
```

**Resolution Priority:**
1. Group observations by attribute
2. Sort by source reliability (learned > static prior)
3. Partition: agreeing vs disagreeing with top source
4. If all agree → `agreed` (confidence = avg_reliability + bonus)
5. If conflict → `resolved_conflict` (top reliability - 0.20 + gap)
6. If confidence < 0.60 → `unresolved_conflict` (human review)
7. If single source → `single_source` (reliability * 0.85)

**Learned Weights (Bayesian):**
- Prior: `SOURCE_RELIABILITY` converted to Beta(alpha, beta) with strength=10
- Review `approve` → alpha += 1
- Review `edit`/`reject` → beta += 1
- Learned reliability = alpha / (alpha + beta)
- Used as `reliability_overrides` in arbitration

---

### 4. Key Code Modules & Functions

| File | Key Functions | Purpose |
|------|---------------|---------|
| `extraction.py` | `extract_from_text()`, `extract_from_pdf_bytes()`, `extract_from_csv()` | Multi-format extraction → Observations |
| `services/llm_extraction.py` | `extract_with_llm()` | NVIDIA NIM fallback when regex finds nothing |
| `services/vision_extraction.py` | `extract_with_vision()` | VLM for nameplate images |
| `arbitration.py` | `arbitrate()`, `compute_quality_score()`, `_values_agree()` | Core conflict resolution + scoring |
| `classification.py` | `classify()` | ETIM/ECLASS/UNSPSC keyword mapping |
| `learning.py` | `update_reliability_from_review()`, `get_learned_weights()` | Beta-Binomial learning from reviews |
| `export.py` | `to_generic_json()`, `to_akeneo_csv()` | PIM-ready exports |
| `main.py` | `_run_pipeline()`, `ingest()`, `ingest_upload()` | Orchestration + API endpoints |
| `models.py` | `Product`, `CustomerReliability` | SQLAlchemy ORM |
| `database.py` | `get_db()`, `init_db()` | DB session management |

---

### 5. Human Review → Learning Loop

```
Human Action          →  Learning Update                    →  Next Arbitration
────────────────────────────────────────────────────────────────────────────
Approve attribute     →  alpha += 1 for winning source_type  →  Higher learned
                                                                    reliability
Edit/Reject attr      →  beta += 1 for winning source_type   →  Lower learned
                                                                    reliability
                                                                   
Effect: After ~10 reviews, learned weights dominate static priors
```

---

### 6. Source Reliability Hierarchy

| Source Type | Static Prior | Learned Range | Description |
|-------------|--------------|---------------|-------------|
| `datasheet` | 0.95 | ~0.85-0.99 | Manufacturer technical datasheet |
| `image_label` | 0.90 | ~0.80-0.99 | Photo of physical nameplate |
| `manufacturer_website` | 0.75 | ~0.60-0.90 | Official product page |
| `catalog_pdf` | 0.70 | ~0.55-0.85 | Catalog excerpt |
| `distributor_erp` | 0.55 | ~0.40-0.80 | Distributor system export |
| `unknown` | 0.40 | ~0.30-0.70 | Fallback |

---

### 7. Quality Score Formula

```
overall_score = 0.5 × completeness + 0.5 × avg_confidence

completeness = 100 × (found_attributes / expected_attributes)

avg_confidence = 100 × mean(resolved_attribute.confidence)

needs_review = attributes where:
  - status == "unresolved_conflict" OR
  - confidence < 0.75
```

---

## Implementation Plan for DEMO_SCRIPT.md

### Section to Replace: Lines 32-55 (Architecture Overview)

**New Structure:**

```markdown
## 🏗️ Architecture Overview — Deep Dive

### Pipeline Data Flow (6 Stages)

[Visual diagram with data types at each stage]

### Stage 1: Ingestion (`main.py`, `extraction.py`)
- Accepts: PDF (PyMuPDF), TXT, CSV, Images (JPG/PNG)
- Multi-part upload with `source_ids[]`, `source_types[]` parallel arrays
- Auto-detects format by extension/MIME type
- Extracts text per page (PDF) / row (CSV) with location hints

### Stage 2: Extraction (`extraction.py`, `services/llm_extraction.py`, `services/vision_extraction.py`)
- **Regex-first**: 7 patterns for industrial attrs (voltage, weight, temp, IP, memory, DI)
- **LLM Fallback**: NVIDIA NIM (Llama-4-Scout) when regex finds 0 observations
- **VLM**: Llama-3.2-90b-vision for nameplate images
- Output: `Observation[]` with `{attribute, value, unit, raw_snippet, location, extracted_by}`

### Stage 3: Arbitration — The Core Moat (`arbitration.py`, `learning.py`)
[Detailed algorithm with code snippets]
- Groups observations by attribute across sources
- Sorts by learned reliability (Beta-Binomial per source_type)
- 8% numeric tolerance for conflict detection
- Resolution: highest-reliability wins, confidence penalized for conflicts
- Statuses: `agreed`, `resolved_conflict`, `unresolved_conflict`, `single_source`, `human_approved`, `human_corrected`, `rejected`

### Stage 4: Classification (`classification.py`)
- Keyword-based mapping to ETIM/ECLASS/UNSPSC
- 2 demo categories: PLC controllers, temperature sensors
- Full dictionaries require licensing (ETIM/ECLASS)

### Stage 5: Quality Scoring (`arbitration.py:compute_quality_score`)
- `overall = 50% completeness + 50% avg_confidence`
- Flags `needs_review`: unresolved_conflict OR confidence < 0.75

### Stage 6: Export (`export.py`)
- **Generic JSON**: Clean, flat structure for API consumption
- **Akeneo CSV**: PIM-ready with unit-embedded column headers

### Human Review → Learning Loop (`learning.py`, `main.py:/review`)
- Beta(alpha, beta) per source_type per tenant
- Prior: static table converted to Beta with strength=10
- Approve → alpha+1 | Edit/Reject → beta+1
- Learned weights override static priors in next arbitration run

### Source Reliability Hierarchy
[Table with static priors, learned ranges, descriptions]
```

---

## Questions for Clarification

1. **Depth level**: How much code detail? (Full function signatures vs conceptual)
2. **Audience**: Demo video viewers (mixed technical) vs technical deep-dive readers?
3. **Visuals**: Mermaid diagrams OK? ASCII art preferred?
4. **Emphasis**: Which stages matter most for your demo narrative?
5. **Length target**: Current section ~15 lines → aim for ~80-120 lines?

---

## Files to Modify
- `.opencode/plans/DEMO_SCRIPT.md` — Lines 32-55 (Architecture Overview section)

---

## Dependencies
- No code changes needed — purely documentation expansion
- References existing codebase: `arbitration.py`, `extraction.py`, `learning.py`, `classification.py`, `export.py`, `main.py`