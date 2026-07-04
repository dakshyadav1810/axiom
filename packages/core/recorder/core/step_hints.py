"""
Auto-inference engine for step hints.

Analyses each recorded step's element data, action type, and page context
to compute:
  - is_critical:  Should the UI auto-expand assertions for this step?
  - suggested_outcome:  Pre-filled expected outcome (url_change, element_appears, text_contains)
  - suggested_preconditions:  Pre-filled preconditions (url_contains, element_enabled)
  - reason:  Human-readable explanation for the suggestion

The function is called in state_aware_recorder._process_interaction() and the
result is attached as `step_hints` on the Step/ExtendedStep model that gets
broadcast over WebSocket.
"""

from __future__ import annotations

import re
from typing import Any, Optional

# ── Submit / CTA keyword pattern ──────────────────────────────────────
_SUBMIT_RE = re.compile(
    r"submit|confirm|checkout|pay|sign.?in|log.?in|register|sign.?up"
    r"|delete|remove|save|create|send|place.?order|add.?to.?cart|buy",
    re.IGNORECASE,
)

# ── Navigation / page-change indicators ───────────────────────────────
_NAV_RE = re.compile(r"href|navigate|redirect|route|next|continue|proceed", re.IGNORECASE)


def compute_step_hints(
    step_data: dict[str, Any],
    step_index: int,
    total_steps: int,
    prev_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    Compute auto-inferred hints for a single step.

    Parameters
    ----------
    step_data : dict
        The full step dict (Step/ExtendedStep serialised).
    step_index : int
        0-based index of this step in the recording so far.
    total_steps : int
        Current count of steps in the flow (after this step is added).
    prev_url : str | None
        The page URL *before* this interaction, used for url_change detection.

    Returns
    -------
    dict  with keys:
        is_critical, suggested_outcome, suggested_preconditions, reason
    """
    action = step_data.get("action", "")
    target = step_data.get("target") or {}
    element = target.get("element_data") or {}
    context = step_data.get("recorded_context") or {}
    markers = step_data.get("state_markers") or {}

    friendly = target.get("friendly_name", "")
    tag = element.get("tag", "").lower()
    el_type = (element.get("extra_attributes") or {}).get("type", "").lower()
    text = element.get("text", "")
    role = element.get("role", "")
    aria = element.get("aria_label", "")
    combined_text = f"{friendly} {text} {aria}".strip()

    # ── 1. Determine criticality ──────────────────────────────────────
    is_critical = _is_critical(action, combined_text, tag, el_type, role, step_index, total_steps)

    # ── 2. Suggest expected outcome ───────────────────────────────────
    suggested_outcome = _suggest_outcome(action, markers, prev_url, context, combined_text, tag, el_type)

    # ── 3. Suggest preconditions ──────────────────────────────────────
    suggested_preconditions = _suggest_preconditions(action, context, element, markers)

    # ── 4. Build human-readable reason ────────────────────────────────
    reason = _build_reason(is_critical, suggested_outcome, action, combined_text)

    # ── 5. Detect repeating group ─────────────────────────────────────
    repeating_group = element.get("repeating_group") or {}
    group_detected = repeating_group.get("detected", False)

    hints: dict[str, Any] = {
        "is_critical": is_critical,
        "suggested_outcome": suggested_outcome,
        "suggested_preconditions": suggested_preconditions,
        "reason": reason,
    }

    if group_detected:
        hints["repeating_group"] = {
            "detected": True,
            "group_selector": repeating_group.get("group_selector"),
            "sibling_count": repeating_group.get("sibling_count", 0),
            "sibling_index": repeating_group.get("sibling_index", 0),
        }

    # ── 6. Test data type suggestion for type actions ─────────────────
    if action == "type":
        input_value = step_data.get("input_value", "")
        data_type = _suggest_data_type(input_value, el_type, element)
        if data_type:
            hints["suggested_data_type"] = data_type

    return hints


# ── Private helpers ───────────────────────────────────────────────────


def _is_critical(
    action: str,
    combined_text: str,
    tag: str,
    el_type: str,
    role: str,
    index: int,
    total: int,
) -> bool:
    """Determine whether this step is \"critical\" (assertions auto-shown).

    NOTE: 'last step' detection is intentionally NOT done here because at
    recording time every step is momentarily the last step.  The frontend
    `isCriticalStep` handles that check dynamically.
    """
    if action in {"navigate", "switch_context"}:
        return True
    # Submit-like buttons / links
    if _SUBMIT_RE.search(combined_text):
        return True
    # <input type="submit"> or <button type="submit">
    if el_type == "submit":
        return True
    # ARIA roles that imply CTA
    if role in ("button",) and _SUBMIT_RE.search(combined_text):
        return True
    # Form submission => likely critical
    if tag in ("form",):
        return True
    return False


def _suggest_outcome(
    action: str,
    markers: dict,
    prev_url: Optional[str],
    context: dict,
    combined_text: str,
    tag: str,
    el_type: str,
) -> Optional[dict]:
    """Return a suggested ExpectedOutcome dict or None."""

    # Navigate actions always suggest url_change
    if action == "navigate":
        return {"outcome_type": "url_change", "value": None}
    if action == "switch_context":
        return None

    # If state_markers recorded a URL change, use that
    pre_url = markers.get("pre_url")
    post_url = markers.get("post_url")
    transition = markers.get("transition_hint", "")

    if pre_url and post_url and pre_url != post_url:
        return {"outcome_type": "url_change", "value": None}

    if transition == "url_changed":
        return {"outcome_type": "url_change", "value": None}

    # Fall back to comparing prev_url (the URL tracked by the recorder between steps)
    # against the current context URL — this is the primary path since state_markers
    # may not always be populated.
    current_url = context.get("url", "")
    if prev_url and current_url and prev_url != current_url:
        return {"outcome_type": "url_change", "value": None}

    # Submit-like buttons likely cause a page or element change
    if _SUBMIT_RE.search(combined_text):
        return {"outcome_type": "element_appears", "value": None}

    # Links with href often navigate
    if tag == "a":
        return {"outcome_type": "url_change", "value": None}

    return None


def _suggest_preconditions(
    action: str,
    context: dict,
    element: dict,
    markers: dict,
) -> Optional[dict]:
    """Return a suggested preconditions dict keyed by UI field names."""
    suggestions: dict[str, Any] = {}

    # For non-navigate actions, suggest URL contains the current path
    if action not in {"navigate", "switch_context"}:
        url = context.get("url", "")
        if url:
            # Extract pathname for a compact suggestion
            from urllib.parse import urlparse
            path = urlparse(url).path
            if path and path != "/":
                suggestions["urlContains"] = path

    return suggestions if suggestions else None


def _build_reason(
    is_critical: bool,
    suggested_outcome: Optional[dict],
    action: str,
    combined_text: str,
) -> Optional[str]:
    """Build a short human-readable explanation string."""
    parts: list[str] = []

    if is_critical:
        if action == "navigate":
            parts.append("Page navigation — assertion recommended")
        elif action == "switch_context":
            parts.append("Context switched to a different tab/popup")
        elif _SUBMIT_RE.search(combined_text):
            parts.append("Submit-intent action detected")
        else:
            parts.append("Critical step")

    if suggested_outcome:
        otype = suggested_outcome.get("outcome_type", "")
        if otype == "url_change":
            parts.append("URL likely changes after this step")
        elif otype == "element_appears":
            parts.append("A confirmation element may appear")
        elif otype == "text_contains":
            parts.append("Page text may update")

    return " · ".join(parts) if parts else None


def _suggest_data_type(
    input_value: str,
    el_type: str,
    element: dict,
) -> Optional[str]:
    """Infer a test-data type label from input attributes and recorded value."""
    extras = element.get("extra_attributes") or {}
    name = (extras.get("name") or "").lower()
    placeholder = (extras.get("placeholder") or "").lower()

    # Input type hints
    if el_type in ("email",) or "email" in name or "email" in placeholder:
        return "email"
    if el_type in ("password",):
        return "password"
    if el_type in ("tel",) or "phone" in name or "phone" in placeholder:
        return "phone"
    if el_type in ("number",) or "zip" in name or "postal" in name:
        return "number"
    if el_type in ("url",):
        return "url"
    if el_type in ("date", "datetime-local"):
        return "date"
    # Heuristic from name/placeholder
    if any(kw in name or kw in placeholder for kw in ("name", "first", "last", "user")):
        return "name"
    if any(kw in name or kw in placeholder for kw in ("address", "street", "city")):
        return "address"
    if any(kw in name or kw in placeholder for kw in ("search", "query", "q")):
        return "search_query"
    return None
