"""Action and field classification helpers for deterministic test generation."""

from __future__ import annotations


IMPORTANT_FIELD_ORDER = ("email", "password", "coupon", "search", "generic")


def classify_action(step: dict) -> str:
    action_type = str(step.get("action") or step.get("type") or "").lower()
    if action_type == "type":
        return "input"
    if action_type in {"click", "submit", "keypress"}:
        return "interaction"
    if action_type in {"navigate", "switch_context"}:
        return "navigation"
    if action_type == "refresh":
        return "state"
    return "other"


def detect_field_type(field_name: str) -> str:
    name = (field_name or "").strip().lower()
    if "email" in name:
        return "email"
    if "password" in name or "passcode" in name:
        return "password"
    if "search" in name or "query" in name:
        return "search"
    if "coupon" in name or "promo" in name or "discount" in name:
        return "coupon"
    return "generic"


def infer_field_name(step: dict) -> str:
    """Return the most semantically useful name for the field targeted by *step*.

    Priority:
    1. ``id`` / ``name`` HTML attributes (inside element_snapshot.attributes or
       the top-level target.attributes dict) — these are developer-assigned and
       most reliably reflect the field's purpose.
    2. ``placeholder`` / ``aria-label`` attributes.
    3. ``friendly_name`` — often the placeholder value or user-typed text, so
       it is consulted last as a fallback.
    """
    target = step.get("target") if isinstance(step.get("target"), dict) else {}
    if not target:
        return ""

    # Collect attributes from both locations (element_snapshot takes precedence
    # for the snapshot-specific keys; top-level attrs for legacy recordings).
    snapshot = target.get("element_snapshot") if isinstance(target.get("element_snapshot"), dict) else {}
    snap_attrs = snapshot.get("attributes") if isinstance(snapshot.get("attributes"), dict) else {}
    top_attrs = target.get("attributes") if isinstance(target.get("attributes"), dict) else {}

    # 1. id / name — most reliable semantic signals
    for key in ("id", "name"):
        value = snap_attrs.get(key) or top_attrs.get(key)
        if value:
            return str(value)

    # 2. placeholder / aria-label
    for key in ("placeholder", "aria-label"):
        value = snap_attrs.get(key) or top_attrs.get(key)
        if value:
            return str(value)

    # 3. friendly_name fallback
    if target.get("friendly_name"):
        return str(target["friendly_name"])

    # 4. snapshot aria_label / text
    for key in ("aria_label", "text"):
        value = snapshot.get(key)
        if value:
            return str(value)

    return ""
