"""Intent contracts for semantic variant generation and assertion planning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentSpec:
    intent_id: str
    variation_types: tuple[str, ...]
    expected_mode: str  # pass | fail
    requires_submit_path: bool = False
    requires_typed_input: bool = False
    requires_auth_path: bool = False


INTENT_SPECS: tuple[IntentSpec, ...] = (
    IntentSpec("baseline_stability", ("baseline",), "pass"),
    IntentSpec("reject_invalid_auth", ("input_validation",), "fail", requires_submit_path=True, requires_auth_path=True),
    IntentSpec("reject_invalid_required_field", ("empty_required_fields", "type_mismatch"), "fail", requires_submit_path=True, requires_typed_input=True),
    IntentSpec("enforce_boundary_length", ("boundary_length",), "fail", requires_submit_path=True, requires_typed_input=True),
    IntentSpec("sanitize_xss", ("xss_probe",), "fail", requires_submit_path=True, requires_typed_input=True),
    IntentSpec("sanitize_sql_injection", ("sql_injection",), "fail", requires_submit_path=True, requires_typed_input=True),
    IntentSpec("viewport_resilience", ("mobile_viewport",), "pass"),
    IntentSpec("network_resilience", ("slow_network_3g",), "pass"),
    IntentSpec("prevent_duplicate_submit", ("double_submit",), "fail", requires_submit_path=True),
)


_VARIATION_TO_INTENT: dict[str, IntentSpec] = {
    variation_type: spec
    for spec in INTENT_SPECS
    for variation_type in spec.variation_types
}


def intent_for_variation(variation_type: str) -> IntentSpec:
    return _VARIATION_TO_INTENT.get(variation_type, IntentSpec("generic_resilience", (variation_type,), "pass"))


def planned_assertions(intent_id: str) -> list[dict]:
    if intent_id == "reject_invalid_auth":
        return [
            {"id": "run_not_passed", "description": "Mutated flow should not complete successfully"},
            {"id": "has_failure_signal", "description": "At least one step-level failure signal is present"},
            {"id": "has_first_party_rejection_signal", "description": "First-party network or step-level rejection signal is present"},
        ]

    if intent_id in {"reject_invalid_required_field", "enforce_boundary_length"}:
        return [
            {"id": "run_not_passed", "description": "Mutated flow should not complete successfully"},
            {"id": "has_first_party_rejection_signal", "description": "Validation/rejection evidence observed in first-party signals"},
        ]

    if intent_id in {"sanitize_xss", "sanitize_sql_injection"}:
        return [
            {"id": "run_not_passed", "description": "Injected payload should not produce a successful run"},
            {"id": "has_first_party_rejection_signal", "description": "Payload rejection/sanitization evidence observed"},
            {"id": "no_first_party_server_crash", "description": "No first-party 5xx server crash should be observed"},
        ]

    if intent_id == "prevent_duplicate_submit":
        return [
            {"id": "no_multiple_first_party_successes", "description": "Duplicate submit must not create multiple distinct successful side effects"},
        ]

    if intent_id in {"viewport_resilience", "network_resilience", "baseline_stability"}:
        return [
            {"id": "run_passed", "description": "Flow should complete successfully"},
        ]

    return [{"id": "run_completed", "description": "Run completed with deterministic verdict"}]
