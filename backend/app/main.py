"""
main.py
-------
FastAPI application. Exposes the end-to-end pipeline:

  ingest sources → extract → arbitrate → classify → attach graph relations
  → quality score → (human review loop) → structured product record

Phase 3: Products now persisted via SQLAlchemy (SQLite default, Postgres-ready).
Phase 4: Export endpoint added (JSON + Akeneo CSV).
Phase 5: Learned reliability weights applied on each pipeline run.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

import os
import uuid
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Load .env if present (Phase 2 — NVIDIA_API_KEY etc.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from . import extraction, arbitration, classification, graph
from .database import get_db, init_db
from .models import Product
from . import export as exporter
from . import learning
from .auth import auth_router, get_current_tenant

APP_DIR = os.path.dirname(__file__)
SAMPLE_DIR = os.path.join(APP_DIR, "sample_data")

EXPECTED_ATTRIBUTES = [
    "supply_voltage_rated",
    "supply_voltage",
    "weight",
    "operating_temp_range",
    "protection_rating",
    "work_memory",
    "digital_inputs",
]

app = FastAPI(title="Veritas — Industrial Product Intelligence API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only — lock this down before any real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


@app.on_event("startup")
def on_startup():
    """Create DB tables on first startup."""
    init_db()


# ─── Pydantic schemas ────────────────────────────────────────────────────────

class SourceInput(BaseModel):
    source_id: str
    source_type: str  # datasheet | manufacturer_website | distributor_erp | image_label | catalog_pdf
    format: str       # "text" | "csv"
    raw_content: str
    location_hint: Optional[str] = None


class IngestRequest(BaseModel):
    product_name: str
    product_id: str
    sources: List[SourceInput]


class ReviewAction(BaseModel):
    attribute: str
    action: str  # "approve" | "edit" | "reject"
    corrected_value: Optional[Any] = None
    reviewer: Optional[str] = "demo-reviewer"


# ─── Pipeline helper ─────────────────────────────────────────────────────────

def _run_pipeline(
    product_name: str,
    product_id: str,
    sources: List[SourceInput],
    db: Session,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    Core pipeline: extract → arbitrate (with learned weights) → classify → graph → quality score.
    """
    observations_by_source = {}
    for src in sources:
        if src.format == "csv":
            obs = extraction.extract_from_csv(src.raw_content, src.source_id)
        else:
            obs = extraction.extract_from_text(
                src.raw_content, src.source_id, src.location_hint or src.source_id
            )
        observations_by_source[src.source_id] = {
            "source_type": src.source_type,
            "observations": obs,
        }

    # Phase 5: fetch learned reliability weights for this run
    reliability_overrides = learning.get_learned_weights(db, tenant_id=tenant_id)

    resolved = arbitration.arbitrate(observations_by_source, reliability_overrides)
    quality = arbitration.compute_quality_score(resolved, EXPECTED_ATTRIBUTES)
    classification_result = classification.classify(product_name)
    related = graph.get_related(product_id)

    return {
        "product_id":    product_id,
        "product_name":  product_name,
        "attributes":    resolved,
        "quality":       quality,
        "classification": classification_result,
        "related":       related,
        "review_log":    [],
        "sources":       [{"source_id": s.source_id, "source_type": s.source_type} for s in sources],
        "tenant_id":     tenant_id,
    }


def _save_product(record: Dict[str, Any], db: Session) -> None:
    """Upsert a product record to the DB."""
    existing = db.query(Product).filter_by(product_id=record["product_id"], tenant_id=record["tenant_id"]).first()
    if existing:
        existing.product_name       = record["product_name"]
        existing.attributes_json    = record["attributes"]
        existing.quality_json       = record["quality"]
        existing.classification_json = record.get("classification")
        existing.related_json       = record.get("related", {})
        existing.sources_json       = record.get("sources", [])
        existing.review_log_json    = record.get("review_log", [])
    else:
        db.add(Product.from_dict(record))
    db.commit()


def _load_product(product_id: str, tenant_id: str, db: Session) -> Optional[Dict[str, Any]]:
    row = db.query(Product).filter_by(product_id=product_id, tenant_id=tenant_id).first()
    return row.to_dict() if row else None


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/api/ingest")
def ingest(req: IngestRequest, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    record = _run_pipeline(req.product_name, req.product_id, req.sources, db, tenant_id)
    _save_product(record, db)
    return record


@app.post("/api/ingest/upload")
async def ingest_upload(
    product_name: str = Form(...),
    product_id: str = Form(...),
    source_ids: List[str] = Form(...),
    source_types: List[str] = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant),
):
    """
    Phase 1: Accept actual file uploads (PDF, TXT, CSV) via multipart/form-data.
    source_ids and source_types must be parallel arrays matching files order.
    """
    if len(files) != len(source_ids) or len(files) != len(source_types):
        raise HTTPException(status_code=400, detail="files, source_ids, and source_types must have the same length.")

    sources = []
    for file, sid, stype in zip(files, source_ids, source_types):
        content_type = file.content_type or ""
        filename = (file.filename or "").lower()
        raw_bytes = await file.read()

        if filename.endswith(".pdf") or "pdf" in content_type:
            # PDF: extract text page-by-page
            obs = extraction.extract_from_pdf_bytes(raw_bytes, sid)
            # For pipeline, we need a SourceInput-like object; use empty raw_content
            # and inject pre-extracted observations differently.
            # Workaround: re-wrap as a text source with joined text
            # (clean solution: refactor pipeline to accept pre-extracted obs — Phase 3+)
            text = "\n".join(o.get("raw_snippet", "") for o in obs)
            fmt = "text"
            raw_content = text if text.strip() else raw_bytes.decode("utf-8", errors="replace")
        elif filename.endswith(".csv") or "csv" in content_type:
            fmt = "csv"
            raw_content = raw_bytes.decode("utf-8", errors="replace")
        elif filename.endswith((".jpg", ".jpeg", ".png")) or "image" in content_type:
            from .services.vision_extraction import extract_with_vision
            obs = extract_with_vision(raw_bytes, sid, "Uploaded Image")
            # Wrap as text so pipeline accepts it
            text = "\n".join(o.get("raw_snippet", "") for o in obs)
            fmt = "text"
            raw_content = text if text.strip() else "[IMAGE DATA]"
        else:
            fmt = "text"
            raw_content = raw_bytes.decode("utf-8", errors="replace")

        sources.append(SourceInput(
            source_id=sid,
            source_type=stype,
            format=fmt,
            raw_content=raw_content,
        ))

    record = _run_pipeline(product_name, product_id, sources, db, tenant_id)
    _save_product(record, db)
    return record


@app.post("/api/ingest/discover")
def ingest_discover(req: IngestRequest, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    """
    Phase 7: Auto-discovery. If sources are empty, try to find a datasheet via the discovery agent.
    """
    from .services.discovery import discover_datasheet_for_sku
    
    if not req.sources:
        discovered = discover_datasheet_for_sku(req.product_id)
        # Convert dictionary to SourceInput
        req.sources = [SourceInput(**discovered)]
        
    record = _run_pipeline(req.product_name, req.product_id, req.sources, db, tenant_id)
    _save_product(record, db)
    return record


@app.get("/api/demo/run")
def run_demo(db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    """Convenience endpoint: runs the pipeline on the bundled sample dataset."""
    def read(fname):
        with open(os.path.join(SAMPLE_DIR, fname), "r") as f:
            return f.read()

    sources = [
        SourceInput(
            source_id="source_a",
            source_type="datasheet",
            format="text",
            raw_content=read("source_a_datasheet.txt"),
        ),
        SourceInput(
            source_id="source_b",
            source_type="manufacturer_website",
            format="text",
            raw_content=read("source_b_website.txt"),
            location_hint="Product page",
        ),
        SourceInput(
            source_id="source_c",
            source_type="distributor_erp",
            format="csv",
            raw_content=read("source_c_distributor_erp.csv"),
        ),
    ]
    record = _run_pipeline("SIMATIC S7-1200 CPU 1214C", "6ES7214-1AG40-0XB0", sources, db, tenant_id)
    _save_product(record, db)
    return record


@app.get("/api/products")
def list_products(db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    products = db.query(Product).filter(Product.tenant_id == tenant_id).all()
    return [
        {
            "product_id":    p.product_id,
            "product_name":  p.product_name,
            "overall_score": (p.quality_json or {}).get("overall_score", 0),
            "needs_review":  len((p.quality_json or {}).get("needs_review", [])),
        }
        for p in products
    ]


@app.get("/api/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    record = _load_product(product_id, tenant_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found. Run /api/demo/run first, or POST /api/ingest.")
    return record


@app.post("/api/products/{product_id}/review")
def review_attribute(product_id: str, action: ReviewAction, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    record = _load_product(product_id, tenant_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found.")

    attr_record = record["attributes"].get(action.attribute)
    if not attr_record:
        raise HTTPException(status_code=404, detail="Attribute not found on this product.")

    if action.action == "approve":
        attr_record["status"] = "human_approved"
        attr_record["confidence"] = max(attr_record["confidence"], 0.95)
    elif action.action == "edit":
        attr_record["resolved_value"] = action.corrected_value
        attr_record["status"] = "human_corrected"
        attr_record["confidence"] = 0.98
        attr_record["reasoning"] = f"Human-corrected by {action.reviewer}, overriding automated resolution."
    elif action.action == "reject":
        attr_record["status"] = "rejected"
        attr_record["confidence"] = 0.0
    else:
        raise HTTPException(status_code=400, detail="action must be approve | edit | reject")

    record["review_log"].append(action.model_dump())

    # Recompute quality score
    record["quality"] = arbitration.compute_quality_score(record["attributes"], EXPECTED_ATTRIBUTES)

    # Phase 5: update learned reliability weights from new review action
    learning.update_reliability_from_review(
        db,
        [action.model_dump()],  # only the new action
        record["attributes"],
        tenant_id=tenant_id
    )

    _save_product(record, db)
    return record


@app.get("/api/products/{product_id}/ask")
def ask(product_id: str, q: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    """
    Retrieval-lite Q&A over stored evidence snippets.
    Keyword overlap ranking — stand-in for real RAG (STATUS_AND_ROADMAP.md item 1).
    """
    record = _load_product(product_id, tenant_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found.")

    q_terms = set(q.lower().split())
    best_attr, best_score, best_evidence = None, 0, None

    for attr, data in record["attributes"].items():
        attr_terms = set(attr.replace("_", " ").split())
        overlap = len(q_terms & attr_terms)
        if overlap > best_score:
            best_score = overlap
            best_attr = attr
            best_evidence = data

    if not best_attr:
        return {"answer": "No matching attribute found for that question.", "evidence": []}

    return {
        "answer": f"{best_attr.replace('_', ' ')}: {best_evidence['resolved_value']} {best_evidence.get('unit') or ''}".strip(),
        "confidence": best_evidence["confidence"],
        "reasoning": best_evidence["reasoning"],
        "evidence": best_evidence["evidence"],
    }


@app.get("/api/products/{product_id}/export")
def export_product(
    product_id: str,
    format: str = Query("json", description="Export format: json | akeneo_csv"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant)
):
    """
    Phase 4: Export a processed product record as a structured file.
    GET /api/products/{id}/export?format=json
    GET /api/products/{id}/export?format=akeneo_csv
    """
    record = _load_product(product_id, tenant_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found.")

    try:
        content_type, filename, content = exporter.export_product(record, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/reliability")
def get_reliability(db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    """Phase 5: Return current learned reliability weights (for dashboard transparency)."""
    weights = learning.get_learned_weights(db, tenant_id=tenant_id)
    from .arbitration import SOURCE_RELIABILITY
    return {
        "learned_weights": weights,
        "static_priors": SOURCE_RELIABILITY,
        "note": "learned_weights override static_priors during arbitration when present",
    }
