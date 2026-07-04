"""Mutation target scoring and meaningfulness checks."""

from __future__ import annotations


def detect_mutation_targets(base_flow: dict, mutated_flow: dict) -> list[dict]:
    base_steps = base_flow.get("steps") if isinstance(base_flow.get("steps"), list) else []
    mutated_steps = mutated_flow.get("steps") if isinstance(mutated_flow.get("steps"), list) else []

    targets: list[dict] = []
    length = min(len(base_steps), len(mutated_steps))
    for idx in range(length):
        before = base_steps[idx] if isinstance(base_steps[idx], dict) else {}
        after = mutated_steps[idx] if isinstance(mutated_steps[idx], dict) else {}

        if before.get("input_value") != after.get("input_value"):
            targets.append({"index": idx, "kind": "input_value", "before": before.get("input_value"), "after": after.get("input_value")})
            continue

        if before.get("action") != after.get("action"):
            targets.append({"index": idx, "kind": "action", "before": before.get("action"), "after": after.get("action")})

    if len(mutated_steps) > len(base_steps):
        for idx in range(len(base_steps), len(mutated_steps)):
            step = mutated_steps[idx] if isinstance(mutated_steps[idx], dict) else {}
            targets.append({"index": idx, "kind": "inserted_step", "after": step.get("action")})

    return targets


def score_mutation_relevance(
    *,
    variation_type: str,
    semantic_model: dict,
    mutation_targets: list[dict],
) -> dict:
    reasons: list[str] = []
    score = 0.1

    if not mutation_targets:
        return {
            "score": 0.0,
            "confidence": "low",
            "meaningful": False,
            "reasons": ["no_mutation_targets_detected"],
        }

    submit_path = set(semantic_model.get("submit_path_indices") or [])
    auth_inputs = set(semantic_model.get("auth_input_indices") or [])

    touched_submit_path = any(target.get("index") in submit_path for target in mutation_targets)
    touched_auth_inputs = any(target.get("index") in auth_inputs for target in mutation_targets)

    if touched_submit_path:
        score += 0.45
        reasons.append("touches_submit_path")
    if touched_auth_inputs:
        score += 0.35
        reasons.append("touches_auth_inputs")

    if variation_type == "double_submit":
        has_inserted_step = any(target.get("kind") == "inserted_step" for target in mutation_targets)
        if has_inserted_step:
            score += 0.45
            reasons.append("injects_submit_like_step")

    if variation_type in {"xss_probe", "sql_injection", "boundary_length", "type_mismatch", "empty_required_fields", "input_validation"}:
        has_input_mutation = any(target.get("kind") == "input_value" for target in mutation_targets)
        if has_input_mutation:
            score += 0.25
            reasons.append("mutates_input_payload")

    score = max(0.0, min(1.0, score))
    confidence = "high" if score >= 0.75 else "medium" if score >= 0.45 else "low"
    meaningful = score >= 0.45

    return {
        "score": score,
        "confidence": confidence,
        "meaningful": meaningful,
        "reasons": reasons or ["low_semantic_relevance"],
    }
