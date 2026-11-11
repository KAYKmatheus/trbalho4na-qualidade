"""Pure business rules for reservation integrity.

These rules are intentionally free of persistence concerns and map directly to the
PRD requirements: FR-06, FR-07, RN02, RN03, RN04 and the material availability
corner cases in CT-15, CT-18 and CT-20.
"""

from __future__ import annotations

from datetime import datetime


def is_overlapping_interval(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    """Return True when two intervals overlap using the documented open-ended rule."""
    if start_a >= end_a or start_b >= end_b:
        return False
    return max(start_a, start_b) < min(end_a, end_b)


def material_stock_available(*, available: int, reserved: int, requested: int) -> bool:
    """Check whether a material request can still be accommodated.

    The function is intentionally pure: it returns True only when the requested
    units can be respected with the current committed reserve. The service layer
    converts False to a domain ConflictError for the API and transaction boundary.
    """
    net_available = max(0, available - reserved)
    return requested <= net_available
