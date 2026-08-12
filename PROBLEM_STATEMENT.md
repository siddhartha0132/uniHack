# Problem Statement — Veritas

*This document is written so that any AI agent (or human) with no prior context can
read it once and understand what this project is, why it exists, what's already
built, and how to extend it correctly. If you are an AI agent picking up this repo,
read this file and STATUS_AND_ROADMAP.md before writing any code.*

---

## 1. The problem, in one paragraph

Industrial manufacturers and distributors manage product information scattered
across websites, PDF datasheets, technical manuals, spreadsheets, and images. This
data is fragmented, inconsistent, and frequently contradictory between sources — one
document says a part weighs 1.2kg, another says 1.35kg, another says 1.4kg — and
today a human has to manually read everything, notice the conflict, decide which
source to trust, and re-key the correct value into a catalog or ERP system. This does
not scale past a few hundred SKUs, let alone the tens or hundreds of thousands a
mid-size industrial distributor carries.

## 2. What this project is NOT

- **It is not a PIM (Product Information Management) replacement.** Akeneo, Salsify,
  Syndigo, inRiver, Pimcore, and Stibo already own that category — they store,
  syndicate, and publish product content across channels, and as of 2026 several of
  them already ship AI-assisted attribute extraction and description generation.
  Competing with them head-on on cataloging/syndication features is not a winning
  strategy for a new entrant.
- **It is not "an AI that reads PDFs and extracts specs."** That capability is
  commodity now — any modern LLM does this reasonably well out of the box. If the
  whole product were extraction, it would have no moat.

## 3. What this project IS

**Veritas is a verification and arbitration layer that sits upstream of whatever
catalog/PIM/ERP a company already owns.** It ingests multiple, often-conflicting
sources for the same product and produces a single structured record where every
attribute carries:

- a resolved value
- a confidence score
- a status (agreed / single-source / resolved-conflict / unresolved-conflict /
  human-approved / human-corrected / rejected)
- a plain-language reasoning string explaining *why* that value was chosen
- a full evidence trail back to the exact source, location, and raw text snippet

The defensible part of this system is not extraction — it's the **arbitration
engine** (`backend/app/arbitration.py`), which decides which of several disagreeing
sources to trust, by how much, and shows its work. That decision logic, plus the
fact that it improves over time as humans correct it (a real per-customer switching
cost — see STATUS_AND_ROADMAP.md item 3), is the actual product.

A secondary differentiator is **industrial classification mapping**
(`backend/app/classification.py`) — mapping products to ETIM/ECLASS/UNSPSC codes,
which general-purpose consumer-goods-focused PIM tools handle poorly, and which
industrial distributors frequently need for marketplace and procurement integrations.

## 4. Who the customer is

Primary ICP: **industrial distributors** (electrical, automation, MRO, fasteners,
HVAC) carrying tens of thousands of SKUs sourced from hundreds of different
manufacturers, currently reconciling conflicting supplier data by hand or with
data-entry contractors. Secondary ICP: mid-market manufacturers without a dedicated
PIM team who can't justify a six-figure enterprise PIM deployment.

The business model is integration, not replacement: Veritas verifies and structures
data, then pushes it into the customer's *existing* PIM/ERP/marketplace via API —
it does not ask anyone to migrate off a system they already have.

## 5. Core architectural decisions (and why)

| Decision | Reasoning |
|---|---|
| Arbitration logic is deterministic Python, not an LLM call | Makes the core moat inspectable, testable, and cheap to run at scale. An LLM can assist extraction; it should not be a black box for the trust-critical arbitration decision. |
| Reliability weighting starts as a static prior table | Simple, transparent starting point. The real long-term moat is making this table *learned per customer* from review corrections — see roadmap. |
| Every resolved value keeps a full evidence trail, always | Non-negotiable. The entire value proposition is "provably correct, not just plausible." Never resolve a value without attaching its evidence. |
| Low-confidence/conflicting attributes are never silently auto-published | Defaults to human review below a confidence threshold. For industrial specs (voltage, load, safety ratings), false confidence has real liability consequences — this is both an ethical default and a marketing angle ("the AI that says 'I'm not sure'"). |
| Backend and frontend are decoupled via a plain REST API | Any client (web dashboard, PIM plugin, CLI, another AI agent) can drive the pipeline. Don't couple pipeline logic to the UI. |

## 6. Conventions for anyone (or any agent) extending this code

- **Attribute names are normalized snake_case keys** (e.g. `supply_voltage`,
  `operating_temp_range`) shared across extraction, arbitration, and the frontend.
  If you add a new attribute type, add its extraction pattern in `extraction.py`
  AND add it to `EXPECTED_ATTRIBUTES` in `main.py` so completeness scoring accounts
  for it.
- **Never resolve a value without an `evidence` list.** Every function that produces
  a resolved attribute must carry forward `source_id`, `source_type`, `location`,
  and `raw_snippet` for each contributing observation.
- **`SOURCE_RELIABILITY` in `arbitration.py` is a starting prior, not a finished
  model.** Do not hardcode business logic elsewhere that assumes it's static —
  the roadmap calls for this to become a per-customer learned value.
- **Confidence scores are 0–1 internally, displayed as 0–100% in the UI.** Keep this
  consistent; don't introduce a third scale.
- **Sample data lives in `backend/app/sample_data/`** and is deliberately
  contradictory (weight and temperature range disagree across the three sources) —
  this is intentional, it's what makes the demo show real arbitration instead of a
  trivial pass-through. If you add more sample products, make sure at least one
  attribute genuinely conflicts.

## 7. How to know if a change is "on strategy"

Before adding a feature, ask: does this strengthen the arbitration/trust story, or
does it just add generic AI extraction capability? Generic extraction (more file
formats, better OCR, a real VLM for images) is worth doing but is not the moat —
prioritize it below anything that improves conflict resolution quality, evidence
traceability, source-reliability learning, or industrial-classification depth.
