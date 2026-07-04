"""Deterministic variation opportunity extraction."""

from __future__ import annotations

from urllib.parse import urlparse

from .classification import detect_field_type, infer_field_name, IMPORTANT_FIELD_ORDER


def _step_action(step: dict) -> str:
    return str(step.get("action") or step.get("type") or "").lower()


def _target_dict(step: dict) -> dict:
    target = step.get("target")
    return target if isinstance(target, dict) else {}


def _target_attrs(step: dict) -> dict:
    target = _target_dict(step)
    attrs = target.get("attributes")
    if isinstance(attrs, dict):
        return attrs
    snapshot = target.get("element_snapshot")
    if isinstance(snapshot, dict):
        snap_attrs = snapshot.get("attributes")
        if isinstance(snap_attrs, dict):
            return snap_attrs
    return {}


def _get_html_input_type(step: dict) -> str:
    """Return the lowercased HTML ``type`` attribute of the target element, or ''."""
    target = _target_dict(step)
    # element_snapshot.attributes is most reliable
    snapshot = target.get("element_snapshot")
    if isinstance(snapshot, dict):
        snap_attrs = snapshot.get("attributes")
        if isinstance(snap_attrs, dict):
            val = snap_attrs.get("type")
            if val:
                return str(val).lower()
    # top-level attributes fallback
    top_attrs = target.get("attributes")
    if isinstance(top_attrs, dict):
        val = top_attrs.get("type")
        if val:
            return str(val).lower()
    return ""


def _normalize_url(url: str | None) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if not parsed.scheme:
        return raw
    # Normalize to detect real transitions while ignoring fragments.
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme}://{parsed.netloc}{path}{query}"


def find_input_candidate(steps: list[dict], do_not_mutate_fields: set[str] | None = None) -> dict | None:
    do_not_mutate_fields = {f.strip().lower() for f in (do_not_mutate_fields or set())}
    candidates: list[dict] = []

    for idx, step in enumerate(steps):
        if _step_action(step) != "type":
            continue
        field_name = infer_field_name(step)
        normalized_name = field_name.strip().lower()
        if normalized_name and normalized_name in do_not_mutate_fields:
            continue

        field_type = detect_field_type(field_name)

        # HTML input type="email"/"password"/"search" is an authoritative signal
        # that overrides name-only heuristics (e.g. friendly_name = placeholder text).
        if field_type == "generic":
            html_input_type = _get_html_input_type(step)
            if html_input_type in {"email", "password", "search"}:
                field_type = html_input_type

        if field_type not in {"email", "password", "coupon", "search"}:
            continue
        candidates.append({
            "index": idx,
            "field_name": field_name,
            "field_type": field_type,
        })

    if not candidates:
        return None

    rank = {name: idx for idx, name in enumerate(IMPORTANT_FIELD_ORDER)}
    candidates.sort(key=lambda item: (rank.get(item["field_type"], 999), item["index"]))
    return candidates[0]


def find_all_type_candidates(
    steps: list[dict],
    do_not_mutate_fields: set[str] | None = None,
    *,
    include_generic: bool = True,
) -> list[dict]:
    """Return ALL type-action steps, optionally filtered by do_not_mutate_fields.

    Unlike ``find_input_candidate`` this returns every ``type`` step so that
    mutations that need to touch multiple fields (e.g. empty_required_fields)
    can do so in a single pass.

    Each entry has keys: index, field_name, field_type, html_input_type.
    """
    do_not_mutate_fields = {f.strip().lower() for f in (do_not_mutate_fields or set())}
    results: list[dict] = []
    for idx, step in enumerate(steps):
        if _step_action(step) != "type":
            continue
        field_name = infer_field_name(step)
        normalized_name = field_name.strip().lower()
        if normalized_name and normalized_name in do_not_mutate_fields:
            continue
        field_type = detect_field_type(field_name)
        html_input_type = _get_html_input_type(step)
        if field_type == "generic" and html_input_type in {"email", "password", "search"}:
            field_type = html_input_type
        if not include_generic and field_type == "generic":
            continue
        results.append({
            "index": idx,
            "field_name": field_name,
            "field_type": field_type,
            "html_input_type": html_input_type,
        })
    return results


def find_first_click_index(steps: list[dict]) -> int | None:
    for idx, step in enumerate(steps):
        action = _step_action(step)
        if action in {"click", "submit"}:
            return idx
    return None


def find_submit_intent_index(steps: list[dict], *, last: bool = False) -> int | None:
    """Return the index of the first (or last, when ``last=True``) submit-intent step.

    ``last=True`` is used by ``inject_double_submit`` so that multi-step flows
    (e.g. add-to-cart → continue → pay) duplicate the *most consequential*
    submit (the payment/final step) rather than the first one encountered.
    """
    submit_intents = {"submit", "checkout", "create", "login", "pay"}
    submit_like_tokens = (
        "submit",
        "checkout",
        "continue",
        "place order",
        "place-order",
        "log in",
        "sign in",
        "pay",
    )

    result: int | None = None
    for idx, step in enumerate(steps):
        action = _step_action(step)
        matched = False
        if action == "submit":
            matched = True
        elif action in {"click", "keypress"}:
            target = _target_dict(step)
            intent = str(target.get("action_intent") or "").strip().lower()
            if intent in submit_intents:
                matched = True
            else:
                friendly = str(target.get("friendly_name") or "").strip().lower()
                if any(token in friendly for token in submit_like_tokens):
                    matched = True
                else:
                    attrs = _target_attrs(step)
                    attr_values = " ".join(str(v).strip().lower() for v in attrs.values() if v is not None)
                    if any(token in attr_values for token in submit_like_tokens):
                        matched = True

        if matched:
            if not last:
                return idx
            result = idx

    return result


def has_stable_anchor_for_first_interaction(steps: list[dict]) -> bool:
    interaction_actions = {"click", "type", "select", "submit", "keypress"}
    first_interaction: dict | None = None
    for step in steps:
        if _step_action(step) in interaction_actions:
            first_interaction = step
            break
    if not first_interaction:
        return False

    target = _target_dict(first_interaction)
    selectors = target.get("selectors") if isinstance(target.get("selectors"), dict) else {}

    # Strong anchors: test IDs, stable HTML attributes
    if selectors.get("test_id"):
        return True
    attrs = _target_attrs(first_interaction)
    for key in ("id", "name", "data-testid", "data-test", "data-qa"):
        if attrs.get(key):
            return True

    # Medium anchors: text, accessibility, or CSS selectors survive viewport
    # changes in the deterministic-first + resolver pipeline.
    if selectors.get("text") or selectors.get("accessibility"):
        return True

    # Element snapshot with meaningful role/aria_label is enough
    snapshot = target.get("element_snapshot") if isinstance(target.get("element_snapshot"), dict) else {}
    if snapshot.get("role") and (snapshot.get("aria_label") or snapshot.get("text")):
        return True

    # A CSS selector is the weakest but still usually works
    if selectors.get("css"):
        return True

    return False


def find_state_change_injection_index(steps: list[dict]) -> int | None:
    if not steps:
        return None

    for idx, step in enumerate(steps):
        action = _step_action(step)
        markers = step.get("state_markers") if isinstance(step.get("state_markers"), dict) else {}
        hint = str(markers.get("transition_hint") or "").strip().lower()
        if hint and hint != "stable":
            return idx + 1

        pre_url = _normalize_url(markers.get("pre_url"))
        post_url = _normalize_url(markers.get("post_url"))
        if pre_url and post_url and pre_url != post_url:
            return idx + 1

        if action in {"navigate", "switch_context", "go_back", "refresh"}:
            return idx + 1

        # Fallback: submit-intent actions are usually state changing.
        submit_idx = find_submit_intent_index([step])
        if submit_idx == 0:
            return idx + 1

    return None


def find_injection_midpoint(steps: list[dict]) -> int | None:
    if not steps:
        return None
    return max(1, len(steps) // 2)
