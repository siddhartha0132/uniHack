# Status & Roadmap

Read PROBLEM_STATEMENT.md first for context. This document is the honest,
concrete answer to: *what actually works right now, what's a scoped stand-in for
demo purposes, and what's the real work still ahead.*

---

## ✅ What's done and working (verified end to end, not just written)

- **Ingestion API** (`POST /api/ingest`) accepting multiple sources per product,
  each tagged with a source type and format (text/CSV).
- **Pattern-based extraction** (`extraction.py`) pulling structured attribute
  candidates out of raw text and CSV — voltage, weight, temperature range,
  protection rating, memory, digital I/O count — each with a raw text snippet and
  location (page number / CSV row) preserved for evidence.
- **Arbitration engine** (`arbitration.py`) — the core of the product:
  - Detects agreement vs. conflict across sources per attribute, with a tolerance
    band for numeric noise vs. genuine disagreement.
  - Resolves conflicts by source-reliability weighting, not arbitrarily.
  - Produces a confidence score (0–1) per attribute, discounted appropriately for
    single-source claims vs. corroborated claims vs. resolved conflicts.
  - Produces a human-readable `reasoning` string for every resolution.
  - Flags attributes below a confidence threshold as `unresolved_conflict`,
    intended for mandatory human review rather than silent auto-publish.
- **Quality scoring** (`compute_quality_score`) — rolls up completeness + average
  confidence into one headline score with a plain-language explanation, and lists
  exactly which attributes need review.
- **Classification mapping** (`classification.py`) — maps product name/description
  to ETIM/ECLASS/UNSPSC codes for two demo categories (PLC controllers, temperature
  sensors).
- **Relationship graph (in-memory)** (`graph.py`) — compatible accessories,
  replacement products, and family members for the demo SKU.
- **Human review workflow** (`POST /api/products/{id}/review`) — approve / edit /
  reject any attribute; approving or editing immediately updates confidence and
  triggers a quality-score recompute; every action is logged in `review_log`.
- **Retrieval-style Q&A** (`GET /api/products/{id}/ask`) — grounded, cited answers
  to natural-language questions about a processed product.
- **Working frontend dashboard** — product list, expandable evidence ledger per
  attribute (sorted lowest-confidence-first so reviewers see what needs attention),
  approve/reject actions, classification and related-product panels, ask box.
- **Sample dataset** — one real PLC SKU (Siemens S7-1200 CPU 1214C) with three
  sources that genuinely disagree on weight (1.35 / 1.2 / 1.4 kg) and temperature
  range, so the demo shows real conflict resolution, not a trivial pass-through.
- **Backend tested and confirmed working end to end via curl** (ingest → arbitrate →
  quality score → review → ask), not just written and assumed correct.

### ✅ Implemented (Previously Stubbed)

- **Authentication / multi-tenancy** — JWT auth with tenant isolation implemented
  in `auth.py` and `main.py` (tenant isolation via `get_current_tenant` dependency).
- **File upload handling** — PDF (PyMuPDF), CSV, and image upload implemented in
  `POST /api/ingest/upload` with PyMuPDF for PDFs and VLM stub for images.
- **Persistence** — SQLAlchemy + SQLite (Postgres-ready) with `Product` and
  `CustomerReliability` models in `models.py`, `database.py`.
- **Learned source-reliability weighting** — Full Bayesian Beta model in `learning.py`
  with `CustomerReliability` table, updated on every review action.
- **PIM/ERP export connectors** — JSON and Akeneo CSV export implemented in
  `export.py` and `GET /api/products/{id}/export`.

---

## 🟡 Partially Implemented / Stubbed

1. **Extraction is regex/pattern-based, not LLM- or VLM-powered.**
   *Upgrade path:* replace/augment `extraction.py`'s pattern matching with an LLM
   call (structured-output prompt) for text, and a vision-language model call for
   images/nameplates. The arbitration engine downstream doesn't need to change —
   it just consumes `{attribute, value, unit, raw_snippet, location, source}`
   observations regardless of how they were produced. This is the single highest
   -value near-term upgrade since it removes the current dependency on documents
   using recognizable phrasing.

2. **Relationship graph is a hardcoded dict for one SKU.**
   *Upgrade path:* Neo4j-backed, populated from manufacturer family/compatibility
   data as it's ingested, enabling real graph queries ("what replaces this
   discontinued part across the whole catalog").

3. **Classification table covers 2 categories only** (PLC controllers, temperature
   sensors), with a handful of hand-picked codes.
   *Upgrade path:* the full ETIM and ECLASS dictionaries are licensed data sets —
   integrating them (and UNSPSC, which is free) properly is real, scoped work, not
   a shortcut. Budget for a data-licensing conversation, not just engineering time.

4. **Discovery agent** — Mock implementation in `discovery.py`; needs real web
   crawler / search API integration for production.

5. **Automated tests** — 3 arbitration + 2 extraction tests exist; need
   comprehensive coverage for `arbitrate()`, `compute_quality_score()`,
   `extract_from_text()`, and `normalize_value()`.

---

## 🔴 Real future work — not yet started at all

- **Production infra:** containerization/deployment config, environment-based
  config instead of hardcoded CORS `allow_origins=["*"]`, logging/monitoring,
  rate limiting.
- **Pilot data validation.** Everything has only been run against the hand-written
  sample dataset. Running a real, messy pilot dataset from a design-partner
  distributor through the pipeline will surface extraction pattern gaps and
  arbitration edge cases that synthetic data won't.

---

## Suggested build order for whoever picks this up next

1. LLM-based extraction as an alternative/fallback to regex patterns — highest leverage upgrade.
2. Real web crawler / discovery agent for manufacturer datasheets.
3. Expand classification coverage with licensed ETIM/ECLASS/UNSPSC data.
4. Relationship graph backed by Neo4j for multi-SKU compatibility queries.
5. Production infrastructure: containerization, logging, monitoring, rate limiting.
6. Comprehensive test suite covering all core modules.
7. Pilot data validation with real distributor datasets.
