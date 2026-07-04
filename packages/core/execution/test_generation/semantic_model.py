"""Semantic flow analysis primitives for intent-aware variant generation."""

from __future__ import annotations

from .classification import detect_field_type, infer_field_name
from .opportunity import find_submit_intent_index


def _step_action(step: dict) -> str:
    return str(step.get("action") or step.get("type") or "").strip().lower()


def _looks_auth_related(step: dict) -> bool:
    target = step.get("target") if isinstance(step.get("target"), dict) else {}
    friendly = str(target.get("friendly_name") or "").strip().lower()
    attrs = target.get("attributes") if isinstance(target.get("attributes"), dict) else {}
    attr_blob = " ".join(str(v).strip().lower() for v in attrs.values() if v is not None)
    step_text = f"{friendly} {attr_blob}"
    return any(token in step_text for token in ("login", "log in", "sign in", "password", "email", "otp", "auth"))


def build_semantic_model(flow_json: dict) -> dict:
    steps = flow_json.get("steps") if isinstance(flow_json.get("steps"), list) else []
    submit_idx = find_submit_intent_index(steps, last=True)

    type_input_indices: list[int] = []
    typed_field_indices: list[int] = []
    auth_input_indices: list[int] = []

    for idx, step in enumerate(steps):
        if _step_action(step) != "type":
            continue
        type_input_indices.append(idx)
        field_name = infer_field_name(step)
        field_type = detect_field_type(field_name)
        if field_type != "generic":
            typed_field_indices.append(idx)
        if field_type in {"email", "password"} or _looks_auth_related(step):
            auth_input_indices.append(idx)

    submit_path_indices = list(range(0, submit_idx + 1)) if isinstance(submit_idx, int) and submit_idx >= 0 else []

    return {
        "step_count": len(steps),
        "has_submit_path": bool(submit_path_indices),
        "submit_idx": submit_idx,
        "submit_path_indices": submit_path_indices,
        "type_input_indices": type_input_indices,
        "typed_field_indices": typed_field_indices,
        "auth_input_indices": auth_input_indices,
        "has_auth_path": bool(auth_input_indices),
    }
