# Veritas — Industrial Product Intelligence
## Demo Script & Project Overview

---

## 🎯 What This Project Is (The Elevator Pitch)

> **"Veritas is a verification and arbitration layer that sits upstream of your PIM/ERP. It ingests multiple conflicting product data sources (datasheets, manufacturer websites, distributor ERPs), automatically detects and resolves conflicts with full evidence trails, scores data quality, and routes low-confidence attributes to human review."**

### The Core Problem
Industrial manufacturers/distributors manage product data scattered across:
- PDF datasheets (manufacturer)
- Product web pages (manufacturer website)
- Legacy ERP exports (distributors)
- Spreadsheets, images, catalogs

**These sources frequently contradict each other** — one says weight = 1.35kg, another 1.2kg, another 1.4kg. Today a human manually reads everything, spots conflicts, decides which source to trust, and re-keys the correct value. This doesn't scale past a few hundred SKUs.

### The Solution (Veritas)
An **arbitration engine** that:
1. **Extracts** structured attributes from each source (regex + LLM fallback)
2. **Detects conflicts** across sources per attribute (with numeric tolerance)
3. **Resolves** by source-reliability weighting (datasheet > website > ERP)
4. **Scores** quality (completeness + confidence)
5. **Routes** low-confidence/conflicted attributes to human review
6. **Exports** clean, structured records to any PIM/ERP (Akeneo, Salsify, etc.)

**Key Differentiator**: It's not "AI that reads PDFs" — that's commodity. The moat is the **deterministic arbitration logic** that shows its work (evidence, reasoning, confidence) and **learns per-customer** from human corrections.

---

## 🏗️ Architecture Overview — The Veritas Pipeline

### The 6-Stage Pipeline (What Happens Under the Hood)

When you hit "Run demo pipeline" or upload files, here's what runs automatically:

| Stage | What Happens | Key Point |
|-------|--------------|-----------|
| **1. Ingest** | Accepts PDFs (PyMuPDF), text, CSVs, images. Extracts text per page/row with location tracking. | Handles real-world formats — no manual copy-paste needed. |
| **2. Extract** | Regex patterns pull 7 industrial attributes (voltage, weight, temp, IP rating, memory, digital I/O). If regex finds nothing → LLM fallback (NVIDIA NIM Llama-4-Scout). For images → VLM (Llama-3.2-90b-vision). | Regex-first for speed/transparency; LLM only when needed. |
| **3. Arbitrate** *(the core moat)* | Groups every attribute across all sources. Sorts by source reliability (datasheet=0.95 > website=0.75 > ERP=0.55). Uses 8% numeric tolerance — 1.35 vs 1.4 = agrees, 1.35 vs 1.2 = conflict. Highest-reliability source wins conflicts. Confidence penalized for disagreements. | Deterministic, explainable, no black box. |
| **4. Classify** | Maps product name/description to ETIM, ECLASS, UNSPSC codes via keyword matching. 2 demo categories (PLC controllers, temperature sensors). | Industrial codes that consumer PIMs miss. |
| **5. Quality Score** | `Overall = 50% completeness + 50% avg confidence`. Flags anything unresolved or below 75% confidence for human review. | One headline number + exact list of what needs attention. |
| **6. Export** | Clean JSON for APIs + Akeneo-ready CSV (unit-embedded headers) for PIM import. | Drops straight into your existing catalog. |

---

### Source Reliability Hierarchy (Why Datasheet Wins)

| Source Type | Static Prior | What It Means |
|-------------|--------------|---------------|
| **Datasheet** | 0.95 | Manufacturer's own technical spec — highest trust |
| **Image/Nameplate** | 0.90 | Physical label photo — very reliable |
| **Manufacturer Website** | 0.75 | Official product page — marketing may simplify |
| **Catalog PDF** | 0.70 | Catalog excerpt — may be outdated |
| **Distributor ERP** | 0.55 | Legacy system export — often stale/translated |
| **Unknown** | 0.40 | Fallback |

**The learning twist**: Every human review updates a Bayesian Beta model per source type. Approve → that source gets more trust. Edit/Reject → less trust. After ~10 reviews, learned weights override static priors for *your* data.

---

### Pipeline Flow (What to Show & Say)

```
SOURCES  →  EXTRACT  →  ARBITRATE  →  CLASSIFY  →  SCORE  →  EXPORT
  │          │          │           │           │         │
  ▼          ▼          ▼           ▼           ▼         ▼
PDF/Web   Regex+LLM  Group by    ETIM/      50%comp   JSON/
CSV/Image fallback   attribute  ECLASS/    +50%conf  Akeneo
           (fallback) Sort by    UNSPSC     =Overall  CSV
           per-page   reliability
           +location  8% tol.
                    Resolve
                    Conflicts
```

**Narration Cues:**
- "Sources go in" → "Regex extracts, LLM only if needed"
- "Arbitration groups by attribute, sorts by reliability"
- "8% tolerance decides agree vs conflict"
- "Highest reliability wins conflicts"
- "Classification adds industrial codes"
- "Quality score = completeness + confidence"
- "Export drops into your PIM"

---

### Human Review → Learning Loop

```
You click "Approve" on protection_rating (all 3 agreed)
    → System: "Datasheet was right" → alpha += 1 for datasheet
    → Next run: datasheet reliability drifts toward 0.97

You click "Edit" on weight (datasheet said 1.35, you correct to 1.38)
    → System: "Datasheet was wrong" → beta += 1 for datasheet
    → Next run: datasheet reliability drops slightly
```

The system **learns your suppliers' actual accuracy** over time — a real switching cost.

---

### Statuses You'll See in the Evidence Ledger

| Status | Meaning | Confidence Range |
|--------|---------|------------------|
| **Agreed** | All sources within 8% tolerance | 80-99% |
| **Resolved Conflict** | Disagreement, highest-reliability won | 60-85% |
| **Unresolved Conflict** | Conflict + low confidence → **human review required** | <60% |
| **Single Source** | Only one source reported it | ~65% (capped) |
| **Human Approved** | Reviewer clicked Approve | 95%+ |
| **Human Corrected** | Reviewer provided corrected value | 98% |
| **Rejected** | Reviewer rejected the attribute | 0% |

---

### Tech Stack (For Reference)

- **Backend**: FastAPI (Python 3.11), SQLAlchemy + SQLite/PostgreSQL
- **Frontend**: Vanilla JS (no build step), served via static server
- **Auth**: JWT with tenant isolation
- **Extraction**: Regex + NVIDIA NIM LLM fallback + VLM for images
- **Classification**: Keyword-based ETIM/ECLASS/UNSPSC (2 categories demoed)
- **Learning**: Bayesian Beta-Binomial updated on every review

---

## 🎬 Demo Video Script (3-4 Minutes)

### 0:00-0:30 — The Problem (Show, Don't Tell)
> "Industrial distributors carry tens of thousands of SKUs from hundreds of manufacturers. Product data comes from datasheets, websites, and distributor ERPs — and they often disagree."

**Action**: Open the 3 sample files side-by-side
- `backend/app/sample_data/source_a_datasheet.txt` (datasheet: 1.35kg, -20 to +60°C)
- `backend/app/sample_data/source_b_website.txt` (website: 1.2kg, -20 to 60°C)
- `backend/app/sample_data/source_c_distributor_erp.csv` (ERP: 1.4kg, -20 to 55°C)

> "Same Siemens PLC. Three sources. Three different weights. Three different temperature ranges. Today this requires manual reconciliation."

### 0:30-1:00 — Run the Demo Pipeline
**Action**: Open http://127.0.0.1:5500 → Sign in (demo/demo) → Click **"Run demo pipeline"**

> "One click runs the full pipeline: extraction → arbitration → classification → quality scoring."

**Show the result**:
- Product: SIMATIC S7-1200 CPU 1214C
- Quality Score: **89.2/100** (100% complete, 78.5% avg confidence)
- 6 attributes extracted
- 3 conflicts detected & resolved
- 1 flagged for human review

### 1:00-2:00 — The Evidence Ledger (Core Moat)
> "This is the heart of Veritas — every attribute shows exactly WHY that value was chosen."

**Action**: Click each attribute row to expand evidence

**Talk through each**:

| Attribute | Status | Key Point |
|-----------|--------|-----------|
| **weight** | Resolved Conflict (79%) | Datasheet (1.35kg) won over website (1.2kg) & ERP (1.4kg) — datasheet has 0.95 reliability |
| **supply_voltage_rated** | Resolved Conflict (75%) | All 3 agree on 24V DC, but datasheet also had range 20.4-28.8V |
| **operating_temp_range** | Resolved Conflict (83%) | Datasheet (-20 to +60°C) won over ERP (-20 to 55°C) |
| **protection_rating** | Agreed (85%) | All 3 sources say IP20 |
| **work_memory** | Agreed (85%) | All 3 say 100 KB |
| **digital_inputs** | Single Source (64%) | Only website reports 14 — flagged for review |

> "Notice: the reasoning text explains the conflict, which source won, and why. No black box."

### 2:00-2:30 — Classification & Relationships
> "Industrial buyers need standard codes — ETIM, ECLASS, UNSPSC. Most PIMs handle these poorly."

**Show**:
- ETIM: EC002542 — Modular PLC – CPU
- ECLASS: 27-37-16-01 — Programmable logic controller
- UNSPSC: 43211900

**Related Products Graph** (hardcoded for demo):
- Family members: CPU 1212C, CPU 1215C
- Compatible accessories: Signal board, Analog input module

### 2:30-3:00 — Human-in-the-Loop Review
> "Low-confidence attributes route to human review — never silently auto-published."

**Action**: Click **"Approve"** on `protection_rating` → confidence jumps to 95%
**Action**: Click **"Edit"** on `digital_inputs` → enter "16" → status becomes `human_corrected`, confidence 98%
**Action**: Show quality score recalculates in real-time

> "Every review action also trains the reliability model — the system learns this customer's source accuracy over time."

### 3:00-3:20 — Natural Language Q&A
> "Grounded Q&A over the evidence — not hallucination."

**Action**: Ask: *"What is the operating temperature range?"*
**Show**: Answer cites datasheet snippet, confidence 83%

**Action**: Ask: *"What's the weight?"*
**Show**: Answer cites 1.35kg from datasheet, explains conflict resolved

### 3:20-3:40 — Export & Upload Proof
> "Clean export to any PIM. And it works on YOUR data, not just the demo."

**Action**: Click **Export → JSON** → show clean structure
**Action**: Click **Export → Akeneo CSV** → show PIM-ready format

**Action**: Click **"Upload Files"** → **"Use Demo Data"** → **"Process"**
> "Same pipeline, same result — proves it's not hardcoded."

### 3:40-4:00 — Closing
> "Veritas doesn't replace your PIM — it verifies data BEFORE it enters your PIM. The arbitration engine is the moat: deterministic, explainable, and learns from your team's corrections."

---

## 🔑 Key Talking Points (Memorize These)

| Topic | Soundbite |
|-------|-----------|
| **Why not a PIM?** | "We sit UPSTREAM of PIMs. Akeneo, Salsify, inRiver store and syndicate — we verify and structure." |
| **Why not just LLM extraction?** | "Extraction is commodity. Arbitration — deciding which disagreeing source to trust — is the moat." |
| **How does conflict resolution work?** | "Source reliability weights (datasheet 0.95, website 0.75, ERP 0.55) + numeric tolerance (8%) + Bayesian learning from human reviews." |
| **What about hallucination?** | "Every value has evidence: source, location, raw snippet. Low confidence = human review. No silent auto-publish." |
| **How does it learn?** | "Beta-Binomial model per source type. Approve = alpha+1, Edit/Reject = beta+1. Weights drift toward observed accuracy." |
| **Industrial classification?** | "ETIM/ECLASS/UNSPSC mapping built-in. Consumer PIMs don't do this well." |
| **Production ready?** | "Core engine is. Need: LLM extraction upgrade, full ETIM/ECLASS license, Neo4j graph, Docker/K8s config, pilot data validation." |

---

## 📁 Project Structure (For Reference)

```
veritas/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, all endpoints
│   │   ├── arbitration.py       # CORE: conflict resolution + confidence
│   │   ├── extraction.py        # Regex + LLM + VLM extraction
│   │   ├── classification.py    # ETIM/ECLASS/UNSPSC mapping
│   │   ├── learning.py          # Bayesian reliability learning
│   │   ├── export.py            # JSON + Akeneo CSV export
│   │   ├── database.py          # SQLAlchemy + SQLite/Postgres
│   │   ├── models.py            # Product + CustomerReliability ORM
│   │   ├── auth.py              # JWT auth, tenant isolation
│   │   └── services/            # LLM, VLM, Discovery agents
│   ├── tests/                   # Arbitration + extraction tests
│   └── sample_data/             # 3 conflicting sources for demo
├── frontend/
│   └── _legacy/                 # Vanilla JS dashboard (served at :5500)
├── src/                         # UniHack enrichment pipeline (separate)
└── docs/                        # API, Architecture, Deployment guides
```

---

## 🚀 Running the Demo

```bash
# Backend (port 8000)
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (port 5500)
cd frontend/_legacy
python -m http.server 5500

# Open http://127.0.0.1:5500
# Sign in: demo / demo
```

---

## ⚠️ Known Limitations (Be Honest If Asked)

| Limitation | Status | Mitigation |
|------------|--------|------------|
| Extraction is regex-based | 🟡 Stubbed | LLM fallback exists (NVIDIA NIM); swap-in point documented |
| Classification covers 2 categories | 🟡 Stubbed | Full ETIM/ECLASS requires licensing |
| Relationship graph is hardcoded | 🟡 Stubbed | Neo4j integration planned |
| Discovery agent is mocked | 🟡 Stubbed | Search API + crawler needed |
| Only tested on synthetic demo data | 🔴 Not done | Pilot with real distributor data required |
| No production infra | 🔴 Not done | Docker, K8s, monitoring, rate limiting needed |

---

## 🎓 If They Ask Technical Follow-ups

### "How does the arbitration math work?"
> "Each source type has a prior reliability (datasheet=0.95, ERP=0.55). Observations grouped by attribute. Highest-reliability source wins conflicts. Confidence = reliability ± corroboration bonus/conflict penalty. Bayesian Beta model learns from reviews."

### "What's the tolerance for numeric conflicts?"
> "8% relative difference. 1.35 vs 1.4 kg = 3.7% → agrees. 1.2 vs 1.35 = 12.5% → conflict."

### "How does multi-tenancy work?"
> "JWT token contains tenant_id. All DB queries filtered by tenant_id. Reliability weights learned per-tenant."

### "Can I add new attributes?"
> "Yes: 1) Add regex pattern to extraction.py TEXT_PATTERNS, 2) Add to EXPECTED_ATTRIBUTES in main.py, 3) Test with conflicting sources."

### "What about images/nameplates?"
> "VLM endpoint exists (services/vision_extraction.py) using NVIDIA NIM Llama-3.2-90b-vision. Requires NVIDIA_API_KEY."

---

## 📝 Quick Reference: API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Get JWT token |
| POST | `/api/ingest` | Ingest text/CSV sources |
| POST | `/api/ingest/upload` | Upload PDF/CSV/Image files |
| POST | `/api/ingest/discover` | Auto-discover datasheet |
| GET | `/api/demo/run` | Run bundled demo |
| GET | `/api/products` | List all products |
| GET | `/api/products/{id}` | Full product with evidence |
| POST | `/api/products/{id}/review` | Approve/Edit/Reject attribute |
| GET | `/api/products/{id}/ask?q=` | Natural language Q&A |
| GET | `/api/products/{id}/export` | Export JSON/Akeneo CSV |
| GET | `/api/reliability` | View learned vs static weights |

---

## 🎤 Final Tips for Your Demo

1. **Narrate what you're clicking** — "I'm expanding the weight attribute to show the evidence ledger..."
2. **Pause on the evidence** — Let them read the raw snippets
3. **Emphasize "shows its work"** — This is the differentiator
4. **Be honest about stubs** — "The discovery agent is mocked; production needs a real crawler"
5. **End with the upload** — Proves it's not a canned demo

---

*Generated for Veritas Demo Video — UniHack 2024*