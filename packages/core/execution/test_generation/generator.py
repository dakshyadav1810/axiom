"""Deterministic orchestration for v1 test-case generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .environments import ENV_3G, ENV_MOBILE, ENV_NORMAL
from .intents import intent_for_variation, planned_assertions
from .mutations import (
    baseline_flow,
    inject_back_navigation,
    inject_double_submit,
    inject_refresh,
    mutate_boundary_length,
    mutate_empty_required_fields,
    mutate_input_validation,
    mutate_sql_injection,
    mutate_type_mismatch,
    mutate_xss_probe,
)
from .opportunity import has_stable_anchor_for_first_interaction
from .semantic_model import build_semantic_model
from .target_scoring import detect_mutation_targets, score_mutation_relevance

DEFAULT_MUTATION_RELEVANCE_THRESHOLD = 0.45


@dataclass(frozen=True)
class VariationSpec:
    name: str
    variation_type: str
    environment_profile: str
    expected_failure_class: str
    expected_outcome: str = "pass"  # "pass" | "fail"


VARIATION_ORDER: list[VariationSpec] = [
    VariationSpec("baseline", "baseline", ENV_NORMAL, "unknown", expected_outcome="pass"),
    # Negative-test variants: expected_outcome="fail" means the app SHOULD reject
    # the mutated input, so a test run that "fails" is actually a PASS.
    VariationSpec("input_validation", "input_validation", ENV_NORMAL, "validation_failed", expected_outcome="fail"),
    VariationSpec("empty_required_fields", "empty_required_fields", ENV_NORMAL, "validation_failed", expected_outcome="fail"),
    VariationSpec("type_mismatch", "type_mismatch", ENV_NORMAL, "validation_failed", expected_outcome="fail"),
    # Boundary-length: the app must reject (or truncate) the oversized input — a validation
    # failure IS the expected outcome, so expected_outcome="fail" triggers inversion.
    VariationSpec("boundary_length", "boundary_length", ENV_NORMAL, "validation_failed", expected_outcome="fail"),
    VariationSpec("xss_probe", "xss_probe", ENV_NORMAL, "security_failure", expected_outcome="fail"),
    VariationSpec("sql_injection", "sql_injection", ENV_NORMAL, "security_failure", expected_outcome="fail"),
    # Environment variants
    VariationSpec("mobile_viewport", "mobile_viewport", ENV_MOBILE, "resolver_failure", expected_outcome="pass"),
    VariationSpec("slow_network_3g", "slow_network_3g", ENV_3G, "network_error", expected_outcome="pass"),
    # double_submit: a correctly-behaving app disables the button after the first
    # click, so the executor's second attempt will fail.  That failure IS the pass
    # condition — if the flow somehow succeeds, the app accepted a duplicate
    # submission (real bug).
    VariationSpec("double_submit", "double_submit", ENV_NORMAL, "race_condition", expected_outcome="fail"),
    # back_navigation and refresh_mid_flow disabled — these are state-destructive
    # mutations that depend on app-specific business logic (whether state is
    # preserved across back/refresh).  Re-enable when per-flow opt-in is built.
    # VariationSpec("back_navigation", "back_navigation", ENV_NORMAL, "state_corruption"),
    # VariationSpec("refresh_mid_flow", "refresh_mid_flow", ENV_NORMAL, "state_corruption"),
]


def _build_case(
    *,
    flow_id: str,
    spec: VariationSpec,
    flow_json: dict,
    active: bool,
    applicability_reason: Optional[str],
    applicability_meta: Optional[dict] = None,
) -> dict:
    return {
        "flow_id": flow_id,
        "name": spec.name,
        "variation_type": spec.variation_type,
        "environment_profile": spec.environment_profile,
        "is_baseline": spec.variation_type == "baseline",
        "active": active,
        "applicability_reason": applicability_reason,
        "applicability_meta_json": applicability_meta or {},
        "expected_failure_class": spec.expected_failure_class,
        "expected_outcome": spec.expected_outcome,
        "definition_json": flow_json,
    }


def _compose_applicability_meta(
    *,
    base_flow: dict,
    mutated_flow: dict,
    variation_type: str,
    semantic_model: dict,
    extra: Optional[dict] = None,
) -> dict:
    intent = intent_for_variation(variation_type)
    mutation_targets = detect_mutation_targets(base_flow, mutated_flow)
    relevance = score_mutation_relevance(
        variation_type=variation_type,
        semantic_model=semantic_model,
        mutation_targets=mutation_targets,
    )

    meta = dict(extra or {})
    meta.update(
        {
            "semantic_intent_id": intent.intent_id,
            "intent_expected_mode": intent.expected_mode,
            "semantic_prerequisites": {
                "requires_submit_path": intent.requires_submit_path,
                "requires_typed_input": intent.requires_typed_input,
                "requires_auth_path": intent.requires_auth_path,
            },
            "planned_assertions": planned_assertions(intent.intent_id),
            "mutation_targets": mutation_targets,
            "target_relevance_score": relevance["score"],
            "target_relevance_confidence": relevance["confidence"],
            "target_relevance_reasons": relevance["reasons"],
            "target_relevance_meaningful": relevance["meaningful"],
            "semantic_model_snapshot": {
                "has_submit_path": semantic_model.get("has_submit_path", False),
                "has_auth_path": semantic_model.get("has_auth_path", False),
                "submit_idx": semantic_model.get("submit_idx"),
            },
        }
    )
    return meta


def _apply_semantic_activation_gates(cases: list[dict], threshold: float) -> list[dict]:
    threshold = max(0.0, min(1.0, float(threshold)))
    gated_cases: list[dict] = []

    for case in cases:
        meta = case.get("applicability_meta_json") if isinstance(case.get("applicability_meta_json"), dict) else {}
        expected_outcome = str(case.get("expected_outcome") or "pass").strip().lower()
        score_raw = meta.get("target_relevance_score")
        score = float(score_raw) if isinstance(score_raw, (int, float)) else 0.0
        meaningful_raw = meta.get("target_relevance_meaningful")
        meaningful = bool(meaningful_raw) and score >= threshold

        meta["mutation_relevance_threshold"] = threshold
        meta["target_relevance_meaningful"] = meaningful
        meta["target_relevance_gate_reason"] = "below_threshold" if score < threshold else "meets_threshold"

        if expected_outcome == "fail" and bool(case.get("active", True)) and not meaningful:
            case = dict(case)
            case["active"] = False
            case["applicability_reason"] = case.get("applicability_reason") or "low_semantic_relevance"
            meta["gated_by_semantic_relevance"] = True
        else:
            meta["gated_by_semantic_relevance"] = False

        case["applicability_meta_json"] = meta
        gated_cases.append(case)

    return gated_cases


def generate_test_cases(
    flow_id: str,
    flow_json: dict,
    *,
    input_mutation_rules: Optional[dict] = None,
    do_not_mutate_fields: Optional[set[str]] = None,
    baseline_timeout_ms: Optional[int] = None,
    mutation_relevance_threshold: float = DEFAULT_MUTATION_RELEVANCE_THRESHOLD,
) -> list[dict]:
    base = baseline_flow(flow_json)
    general_settings = base.get("general_settings") if isinstance(base.get("general_settings"), dict) else {}
    flow_is_mobile = bool(general_settings.get("is_mobile", False))
    semantic_model = build_semantic_model(base)
    steps = base.get("steps") if isinstance(base.get("steps"), list) else []
    cases: list[dict] = []

    for spec in VARIATION_ORDER:
        if flow_is_mobile and spec.variation_type in {"mobile_viewport", "slow_network_3g"}:
            continue

        if spec.variation_type == "baseline":
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=baseline_flow(base),
                    active=True,
                    applicability_reason=None,
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=baseline_flow(base),
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={"reason": "always_on"},
                    ),
                )
            )
            continue

        if spec.variation_type == "input_validation":
            mutated, ok, reason = mutate_input_validation(
                base,
                mutation_rules=input_mutation_rules,
                do_not_mutate_fields=do_not_mutate_fields,
            )
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_input_field_type": ["email", "password", "coupon", "search"],
                            "do_not_mutate_fields": sorted(do_not_mutate_fields or set()),
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "empty_required_fields":
            mutated, ok, reason = mutate_empty_required_fields(
                base,
                do_not_mutate_fields=do_not_mutate_fields,
            )
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_type_action": True,
                            "do_not_mutate_fields": sorted(do_not_mutate_fields or set()),
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "type_mismatch":
            mutated, ok, reason = mutate_type_mismatch(
                base,
                do_not_mutate_fields=do_not_mutate_fields,
            )
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_numeric_or_email_field": True,
                            "do_not_mutate_fields": sorted(do_not_mutate_fields or set()),
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "boundary_length":
            mutated, ok, reason = mutate_boundary_length(
                base,
                do_not_mutate_fields=do_not_mutate_fields,
            )
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_type_action": True,
                            "do_not_mutate_fields": sorted(do_not_mutate_fields or set()),
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "xss_probe":
            mutated, ok, reason = mutate_xss_probe(
                base,
                do_not_mutate_fields=do_not_mutate_fields,
            )
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_type_action": True,
                            "do_not_mutate_fields": sorted(do_not_mutate_fields or set()),
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "sql_injection":
            mutated, ok, reason = mutate_sql_injection(
                base,
                do_not_mutate_fields=do_not_mutate_fields,
            )
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_type_action": True,
                            "do_not_mutate_fields": sorted(do_not_mutate_fields or set()),
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "mobile_viewport":
            mobile_ok = has_stable_anchor_for_first_interaction(steps)
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=baseline_flow(base),
                    active=mobile_ok,
                    applicability_reason=None if mobile_ok else "mobile_selector_risk",
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=baseline_flow(base),
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_first_interaction_stable_anchor": True,
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "slow_network_3g":
            has_steps = bool(steps)
            timeout_budget_available = baseline_timeout_ms is None or baseline_timeout_ms > 0
            active = has_steps and timeout_budget_available
            reason = None
            if not has_steps:
                reason = "empty_flow"
            elif not timeout_budget_available:
                reason = "no_timeout_budget"
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=baseline_flow(base),
                    active=active,
                    applicability_reason=reason,
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=baseline_flow(base),
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_non_empty_flow": True,
                            "baseline_timeout_ms": baseline_timeout_ms,
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "double_submit":
            mutated, ok, reason = inject_double_submit(base)
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_submit_intent": True,
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "back_navigation":
            mutated, ok, reason = inject_back_navigation(base)
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_state_change": True,
                        },
                    ),
                )
            )
            continue

        if spec.variation_type == "refresh_mid_flow":
            mutated, ok, reason = inject_refresh(base)
            cases.append(
                _build_case(
                    flow_id=flow_id,
                    spec=spec,
                    flow_json=mutated,
                    active=ok,
                    applicability_reason=reason if ok else (reason or "not_applicable"),
                    applicability_meta=_compose_applicability_meta(
                        base_flow=base,
                        mutated_flow=mutated,
                        variation_type=spec.variation_type,
                        semantic_model=semantic_model,
                        extra={
                            "requires_state_change": True,
                        },
                    ),
                )
            )

    if flow_is_mobile:
        adjusted_cases: list[dict] = []
        for case in cases:
            normalized = dict(case)
            normalized["environment_profile"] = ENV_MOBILE
            adjusted_cases.append(normalized)
        cases = adjusted_cases

    return _apply_semantic_activation_gates(cases, mutation_relevance_threshold)
