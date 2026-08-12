# Veritas — Industrial Product Intelligence, Verified

A working end-to-end MVP: ingest conflicting product data from multiple sources
(datasheet, manufacturer website, distributor ERP), automatically detect and resolve
conflicts with full evidence trails, score data quality, and route low-confidence
attributes to a human review queue.

Read **PROBLEM_STATEMENT.md** first if you (human or AI) are new to this project — it
explains what this is, who it's for, and why it's built the way it is.

Read **STATUS_AND_ROADMAP.md** to see exactly what's implemented vs. what's stubbed
for demo purposes vs. what's genuinely future work.

---

## What's in this project

```
veritas/
├── PROBLEM_STATEMENT.md      ← read this first (any AI agent picking up this repo should start here)
├── STATUS_AND_ROADMAP.md     ← what's done, what's stubbed, what to build next
├── backend/
│   ├── app/
│   │   ├── main.py           ← FastAPI app, all endpoints
│   │   ├── extraction.py     ← pulls attributes out of raw text/CSV sources
│   │   ├── arbitration.py    ← THE CORE LOGIC: conflict detection + resolution + confidence scoring
│   │   ├── classification.py ← ETIM/ECLASS/UNSPSC mapping (demo scope: 2 categories)
│   │   ├── graph.py          ← product relationships (family/compatible/replacement)
│   │   └── sample_data/      ← 3 genuinely conflicting sources for one real PLC SKU
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── styles.css
    └── app.js                ← vanilla JS, no build step, talks to the API
```

## Running it

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:** just open `frontend/index.html` directly in a browser (it calls
`http://127.0.0.1:8000` by default — see the `VERITAS_API_BASE` variable at the top
of `app.js` if you need to point it elsewhere), or serve it with any static server:
```bash
cd frontend
python3 -m http.server 5500
```

Then click **"Run demo pipeline"** in the top bar. This runs the bundled sample
dataset — a Siemens PLC SKU with three sources that genuinely disagree on weight and
temperature range — through the full pipeline and shows you the resolved product
record with confidence scores and an evidence ledger you can expand per attribute.

## Feeding it your own data

`POST /api/ingest` with:
```json
{
  "product_name": "Your Product",
  "product_id": "SKU-123",
  "sources": [
    {
      "source_id": "source_1",
      "source_type": "datasheet",
      "format": "text",
      "raw_content": "... raw extracted text ..."
    }
  ]
}
```
`source_type` drives the reliability weighting in the arbitration engine — see
`arbitration.py` → `SOURCE_RELIABILITY`.

## Why this is built the way it is

See PROBLEM_STATEMENT.md for the full reasoning, but in short: extraction (pulling
values out of a PDF) is commodity — every LLM can do it. This project's actual value
is the **arbitration engine** — the part that decides which of several disagreeing
sources to trust, how confident to be, and shows its work. That's `arbitration.py`,
and it's the file to read first if you want to understand what makes this different
from "an AI that reads PDFs."
