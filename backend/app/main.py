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
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
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
    "weight",
    "operating_temp_range",
    "protection_rating",
    "work_memory",
    "digital_inputs",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    init_db()
    yield
    # Future: close DB pools, cleanup resources

app = FastAPI(title="Veritas — Industrial Product Intelligence API", version="0.2.0", lifespan=lifespan)

cors_env = os.getenv("CORS_ORIGINS", "")
origins_list = [o.strip() for o in cors_env.split(",") if o.strip() and o.strip() != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list if origins_list else ["*"],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

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


def _save_product(record: Dict[str, Any], db: Session, expected_version: int | None = None) -> None:
    """Upsert a product record to the DB with optimistic locking."""
    existing = db.query(Product).filter_by(product_id=record["product_id"], tenant_id=record["tenant_id"]).first()
    if existing:
        if expected_version is not None and existing.version != expected_version:
            raise HTTPException(status_code=409, detail="Record modified by another user. Please refresh and retry.")
        existing.version = (existing.version or 1) + 1
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
    if row:
        d = row.to_dict()
        d["_version"] = row.version
        return d
    return None


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
        # Validate and ignore extra keys
        req.sources = [SourceInput.model_validate(discovered, strict=False)]
        
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


@app.get("/api/demo/files/{filename}")
def get_demo_file(filename: str):
    """Serve a sample data file for the upload demo."""
    allowed_files = {
        "source_a_datasheet.txt": "text/plain",
        "source_b_website.txt": "text/plain",
        "source_c_distributor_erp.csv": "text/csv",
    }
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="File not found")
    file_path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type=allowed_files[filename], filename=filename)


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


@app.delete("/api/products/clear")
def clear_products(db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    db.query(Product).filter(Product.tenant_id == tenant_id).delete()
    db.commit()
    return {"status": "ok", "message": "All products cleared"}


@app.post("/api/products/{product_id}/review")
def review_attribute(product_id: str, action: ReviewAction, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    record = _load_product(product_id, tenant_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found.")

    current_version = record.get("_version", 1)

    attr_record = record["attributes"].get(action.attribute)
    if not attr_record:
        raise HTTPException(status_code=404, detail="Attribute not found on this product.")

    if action.action == "approve":
        attr_record["status"] = "human_approved"
        attr_record["confidence"] = 1.0
        attr_record["reasoning"] = f"Verified and approved by {action.reviewer}."
    elif action.action == "edit":
        val = action.corrected_value
        unit = attr_record.get("unit")
        if unit and isinstance(val, str):
            if val.endswith(f" {unit}"):
                val = val[:-len(f" {unit}")].strip()
            elif val.endswith(unit):
                val = val[:-len(unit)].strip()
        
        if isinstance(val, str):
            val_clean = val.strip()
            try:
                if "." in val_clean:
                    val = float(val_clean)
                else:
                    val = int(val_clean)
            except ValueError:
                val = val_clean

        attr_record["resolved_value"] = val
        attr_record["status"] = "human_corrected"
        attr_record["confidence"] = 1.0
        attr_record["reasoning"] = f"Human-corrected by {action.reviewer}, overriding automated resolution."
    elif action.action == "reject":
        attr_record["status"] = "rejected"
        attr_record["confidence"] = 0.0
    else:
        raise HTTPException(status_code=400, detail="action must be approve | edit | reject")

    log_entry = action.model_dump()
    log_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    record["review_log"].append(log_entry)

    # Recompute quality score
    record["quality"] = arbitration.compute_quality_score(record["attributes"], EXPECTED_ATTRIBUTES)

    # Phase 5: update learned reliability weights from new review action
    learning.update_reliability_from_review(
        db,
        [action.model_dump()],  # only the new action
        record["attributes"],
        tenant_id=tenant_id
    )

    _save_product(record, db, expected_version=current_version)
    return record


# Synonyms/aliases so natural questions like "what's the voltage?" match "supply_voltage_rated"
_ASK_ALIASES = {
    "voltage": ["supply_voltage_rated", "supply_voltage"],
    "power": ["supply_voltage_rated", "supply_voltage"],
    "weight": ["weight"],
    "mass": ["weight"],
    "heavy": ["weight"],
    "temperature": ["operating_temp_range"],
    "temp": ["operating_temp_range"],
    "heat": ["operating_temp_range"],
    "ip": ["protection_rating"],
    "protection": ["protection_rating"],
    "ingress": ["protection_rating"],
    "memory": ["work_memory"],
    "ram": ["work_memory"],
    "storage": ["work_memory"],
    "input": ["digital_inputs"],
    "inputs": ["digital_inputs"],
    "di": ["digital_inputs"],
    "digital": ["digital_inputs"],
}


@app.get("/api/products/{product_id}/ask")
def ask(product_id: str, q: str, db: Session = Depends(get_db), tenant_id: str = Depends(get_current_tenant)):
    """
    Retrieval-lite Q&A over stored evidence snippets.
    Uses alias expansion + keyword overlap — stand-in for real RAG.
    """
    record = _load_product(product_id, tenant_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="Product not found.")

    q_terms = set(q.lower().split())
    best_attr, best_score, best_evidence = None, 0, None

    for attr, data in record["attributes"].items():
        score = 0
        # Direct token overlap with attribute name
        attr_terms = set(attr.replace("_", " ").split())
        score += len(q_terms & attr_terms)
        # Alias expansion: check if any query word is an alias for this attribute
        for qt in q_terms:
            if attr in _ASK_ALIASES.get(qt, []):
                score += 2  # aliases are strong signals
        if score > best_score:
            best_score = score
            best_attr = attr
            best_evidence = data

    if not best_attr or best_score == 0 or best_evidence is None:
        return {"answer": "No matching attribute found for that question.", "evidence": []}

    return {
        "answer": f"{best_attr.replace('_', ' ')}: {best_evidence.get('resolved_value')} {best_evidence.get('unit') or ''}".strip(),
        "confidence": best_evidence.get("confidence", 0.0),
        "reasoning": best_evidence.get("reasoning", ""),
        "evidence": best_evidence.get("evidence", []),
    }


@app.get("/api/products/{product_id}/export")
def export_product(
    product_id: str,
    fmt: str = Query("json", alias="format", description="Export format: json | akeneo_csv"),
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
        content_type, filename, content = exporter.export_product(record, fmt)
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
