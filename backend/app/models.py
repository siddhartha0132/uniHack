"""
models.py
---------
Phase 3: SQLAlchemy ORM models.

Stores the full resolved product record as JSON columns for MVP simplicity.
This avoids over-normalization at this stage while making the persistence
layer a drop-in replacement for the in-memory PRODUCTS dict.

Phase 5 adds CustomerReliability for learned source weights.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON
from sqlalchemy.types import TypeDecorator

from .database import Base


class JSONColumn(TypeDecorator):
    """Stores Python dicts/lists as JSON text. Works with both SQLite and Postgres."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return json.loads(value) if value is not None else None


class Product(Base):
    """
    One row = one fully processed product record.
    Mirrors the in-memory dict shape from main.py exactly so existing code
    can be migrated with minimal changes.
    """
    __tablename__ = "products"

    product_id: Any   = Column(String, primary_key=True, index=True)
    tenant_id: Any    = Column(String, primary_key=True, index=True, default="tenant_demo")
    product_name: Any = Column(String, nullable=False)

    # Full resolved pipeline output stored as JSON blobs
    attributes_json: Any     = Column(JSONColumn, default=dict)
    quality_json: Any        = Column(JSONColumn, default=dict)
    classification_json: Any = Column(JSONColumn, nullable=True)
    related_json: Any        = Column(JSONColumn, default=dict)
    sources_json: Any        = Column(JSONColumn, default=list)
    review_log_json: Any     = Column(JSONColumn, default=list)

    created_at: Any  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Any  = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
    version: Any     = Column(Integer, default=1, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM row back to the same dict shape the API returns."""
        return {
            "product_id":     self.product_id,
            "product_name":   self.product_name,
            "attributes":     self.attributes_json or {},
            "quality":        self.quality_json or {},
            "classification": self.classification_json,
            "related":        self.related_json or {},
            "sources":        self.sources_json or [],
            "review_log":     self.review_log_json or [],
            "version":        self.version,
            "tenant_id":      self.tenant_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Product":
        """Build an ORM row from the pipeline output dict."""
        return cls(
            product_id          = d["product_id"],
            tenant_id           = d.get("tenant_id", "tenant_demo"),
            product_name        = d["product_name"],
            attributes_json     = d.get("attributes", {}),
            quality_json        = d.get("quality", {}),
            classification_json = d.get("classification"),
            related_json        = d.get("related", {}),
            sources_json        = d.get("sources", []),
            review_log_json     = d.get("review_log", []),
        )


class CustomerReliability(Base):
    """
    Phase 5: Per-source-type Bayesian reliability model.
    Uses Beta distribution parameters (alpha=successes, beta=failures).
    One row per source_type per customer (customer_id = 'global' for MVP).
    """
    __tablename__ = "customer_reliability"

    id: Any          = Column(String, primary_key=True)  # "{tenant_id}:{customer_id}:{source_type}"
    tenant_id: Any   = Column(String, nullable=False, default="tenant_demo")
    customer_id: Any = Column(String, nullable=False, default="global")
    source_type: Any = Column(String, nullable=False)
    alpha: Any       = Column(Float, default=1.0)   # number of correct resolutions + 1
    beta: Any        = Column(Float, default=1.0)   # number of corrections + 1
    updated_at: Any  = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    @property
    def mean_reliability(self) -> float:
        """Beta distribution mean: alpha / (alpha + beta)."""
        a = float(getattr(self, "alpha", 1.0) or 1.0)
        b = float(getattr(self, "beta", 1.0) or 1.0)
        return a / (a + b)
