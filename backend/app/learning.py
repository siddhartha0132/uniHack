"""
learning.py
-----------
Phase 5: Learned source-reliability weights.

This is the actual long-term moat described in PROBLEM_STATEMENT.md section 5
and STATUS_AND_ROADMAP.md item 3.

The model:
- Each source_type gets a Beta distribution: Beta(alpha, beta)
- alpha = prior + number of times this source type was right (approved)
- beta  = prior + number of times this source type was wrong (corrected/rejected)
- The mean of Beta(alpha, beta) = alpha / (alpha + beta) is used as the reliability weight

Starting prior: alpha=1, beta=1 (uniform, no data) → mean = 0.5
As review data accumulates, the weights drift toward actual observed accuracy.

The static SOURCE_RELIABILITY table in arbitration.py is used as the initial
prior (converted to equivalent Beta parameters), so the learned model starts
with the same intuitions as the hand-crafted weights rather than from scratch.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import CustomerReliability
from .arbitration import SOURCE_RELIABILITY


# Convert the static prior table to equivalent Beta parameters.
# p = alpha/(alpha+beta) → alpha = p*k, beta = (1-p)*k, k=strength of prior
# We use k=10 so the static priors take ~10 reviews to move significantly.
PRIOR_STRENGTH = 10


def _prior_alpha_beta(source_type: str):
    p = SOURCE_RELIABILITY.get(source_type, SOURCE_RELIABILITY["unknown"])
    alpha = p * PRIOR_STRENGTH
    beta = (1 - p) * PRIOR_STRENGTH
    return max(alpha, 0.1), max(beta, 0.1)


def get_reliability_row(
    db: Session,
    source_type: str,
    tenant_id: str,
    customer_id: str = "global",
) -> CustomerReliability:
    """Fetch or create a reliability row for a given source_type."""
    row_id = f"{tenant_id}:{customer_id}:{source_type}"
    row = db.get(CustomerReliability, row_id)
    if row is None:
        alpha, beta = _prior_alpha_beta(source_type)
        row = CustomerReliability(
            id=row_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            source_type=source_type,
            alpha=alpha,
            beta=beta,
        )
        db.add(row)
        db.flush()
    return row


def update_reliability_from_review(
    db: Session,
    review_log: List[Dict[str, Any]],
    attributes: Dict[str, Any],
    tenant_id: str,
    customer_id: str = "global",
) -> None:
    """
    Apply Bayesian updates to reliability weights based on review actions.
    Called after every approve/edit/reject on a product.

    Logic:
    - approve:          source that provided the resolved value was correct → alpha +1
    - edit / reject:    source that provided the resolved value was wrong → beta +1
    """
    for action_record in review_log:
        attr_name = action_record.get("attribute")
        action    = action_record.get("action")
        if not attr_name or not action:
            continue

        attr_data = attributes.get(attr_name, {})
        evidence  = attr_data.get("evidence", [])

        # Find the source_type that contributed the resolved value (first agreeing source)
        source_type = None
        for ev in evidence:
            if ev.get("agrees_with_resolution"):
                source_type = ev.get("source_type")
                break

        if not source_type:
            continue

        row = get_reliability_row(db, source_type, tenant_id, customer_id)

        if action == "approve":
            row.alpha += 1.0
        elif action in ("edit", "reject"):
            row.beta += 1.0

        row.updated_at = datetime.now(timezone.utc)

    db.commit()


def get_learned_weights(
    db: Session,
    tenant_id: str,
    customer_id: str = "global",
) -> Dict[str, float]:
    """
    Returns a dict of {source_type: learned_reliability} for all source types
    that have been observed. Falls back to static prior for unseen types.
    This dict is passed to arbitration.arbitrate() as reliability_overrides.
    """
    rows = db.query(CustomerReliability).filter(
        CustomerReliability.tenant_id == tenant_id,
        CustomerReliability.customer_id == customer_id
    ).all()

    weights = {}
    for row in rows:
        weights[row.source_type] = round(row.mean_reliability, 4)

    return weights
