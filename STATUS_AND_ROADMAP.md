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
- Backend tested and confirmed working end to end via curl (ingest → arbitrate →
  quality score → review → ask), not just written and assumed correct.

## 🟡 Deliberately stubbed for demo scope (working, but simplified — not fake)

These are real, functioning implementations chosen to be fast to build and run
with zero external dependencies/API keys, not placeholders that fake output. Each
has a clear, scoped upgrade path:

1. **Extraction is regex/pattern-based, not LLM- or VLM-powered.**
   *Upgrade path:* replace/augment `extraction.py`'s pattern matching with an LLM
   call (structured-output prompt) for text, and a vision-language model call for
   images/nameplates. The arbitration engine downstream doesn't need to change —
   it just consumes `{attribute, value, unit, raw_snippet, location, source}`
   observations regardless of how they were produced. This is the single highest
   -value near-term upgrade since it removes the current dependency on documents
   using recognizable phrasing.

2. **Storage is in-memory (`PRODUCTS` dict in `main.py`), not persisted.**
   *Upgrade path:* Postgres for transactional product records + review audit log;
   a vector DB (Qdrant/Weaviate) with real embeddings for the `/ask` endpoint
   instead of keyword overlap; Neo4j for the relationship graph once it needs to
   scale past a hand-written dict. All three are additive — the API contract
   (`main.py` route shapes) doesn't need to change, only what's behind it.

3. **Source reliability weights are a static table, not learned.**
   This is the single most important upgrade for the actual business moat (see
   PROBLEM_STATEMENT.md, section 5). *Upgrade path:* every `approve`/`edit`/`reject`
   action in the review workflow is already logged (`review_log`) — the next step
   is a small model (even a simple Bayesian update per `source_type` per customer)
   that adjusts `SOURCE_RELIABILITY` weights over time based on how often each
   source type turns out to be right vs. corrected. This is what makes the product
   get cheaper/more accurate to run the longer a customer uses it — a real
   switching cost, not just a nice-to-have.

4. **Relationship graph is a hardcoded dict for one SKU.**
   *Upgrade path:* Neo4j-backed, populated from manufacturer family/compatibility
   data as it's ingested, enabling real graph queries ("what replaces this
   discontinued part across the whole catalog").

5. **Classification table covers 2 categories only** (PLC controllers, temperature
   sensors), with a handful of hand-picked codes.
   *Upgrade path:* the full ETIM and ECLASS dictionaries are licensed data sets —
   integrating them (and UNSPSC, which is free) properly is real, scoped work, not
   a shortcut. Budget for a data-licensing conversation, not just engineering time.

## 🔴 Real future work — not yet started at all

- **Authentication / multi-tenancy.** Right now there's no user model, no
  per-customer data isolation, no auth on any endpoint. Required before any real
  pilot touches real customer data.
- **File upload handling** for actual PDF/image files (currently the API accepts
  pre-extracted raw text/CSV — there's no PDF-to-text or image-OCR step in this
  repo yet). Needs PyMuPDF or similar for PDFs, and a VLM call for images.
- **PIM/ERP export connectors.** The pitch depends on "integrate into the customer's
  existing system," but there's currently no export/push implementation for any
  specific target (Akeneo import format, generic CSV/XML feed, etc.) — pick one
  real target for the first pilot and build that connector end to end.
- **Web crawler / discovery agent** to automatically find a manufacturer's
  datasheet/product page given just a product name or SKU (referenced conceptually
  in PROBLEM_STATEMENT.md as the "Discovery" role, not implemented).
- **Production infra:** containerization/deployment config, environment-based
  config instead of hardcoded CORS `allow_origins=["*"]`, logging/monitoring,
  rate limiting.
- **Automated tests.** Everything above was verified manually via curl during
  development; there is no test suite yet. Before extending the arbitration logic
  further, add unit tests for `arbitrate()` and `compute_quality_score()` first —
  that logic is the product and regressions there are the most expensive kind.
- **Pilot data validation.** Everything has only been run against the hand-written
  sample dataset. Running a real, messy pilot dataset from a design-partner
  distributor through the pipeline will surface extraction pattern gaps and
  arbitration edge cases that synthetic data won't.

## Suggested build order for whoever picks this up next

1. Real PDF/CSV file upload (not just raw text in the request body) — quick, unblocks real testing.
2. LLM-based extraction as an alternative/fallback to regex patterns — highest leverage upgrade.
3. Persistence (Postgres) — needed before anything resembling a real pilot.
4. One real PIM export connector — needed to make the "integrate, don't replace" pitch real, not just a slide.
5. Learned source-reliability weighting — the actual long-term moat; do this once there's enough real review-log data to make it meaningful (i.e., after step 4, once a pilot is running).
