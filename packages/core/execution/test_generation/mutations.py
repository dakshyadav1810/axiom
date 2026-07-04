"""Deterministic flow mutation primitives."""

from __future__ import annotations

from copy import deepcopy

from .opportunity import (
    find_all_type_candidates,
    find_input_candidate,
    find_state_change_injection_index,
    find_submit_intent_index,
)


DEFAULT_INVALID_VALUES = {
    "email": "invalid-email",
    "password": "x",               # single char — reliably fails min-length validation
    "coupon": "INVALID_COUPON_###",
    "search": "!invalid?search#",   # special chars avoid silent stripping
    "generic": "__INVALID__",
}


def baseline_flow(flow_json: dict) -> dict:
    return deepcopy(flow_json)


def mutate_input_validation(
    flow_json: dict,
    *,
    mutation_rules: dict | None = None,
    do_not_mutate_fields: set[str] | None = None,
) -> tuple[dict, bool, str | None]:
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    candidate = find_input_candidate(steps, do_not_mutate_fields=do_not_mutate_fields)
    if not candidate:
        return modified, False, "no_eligible_type_action"

    rules = dict(DEFAULT_INVALID_VALUES)
    if mutation_rules:
        for key, value in mutation_rules.items():
            if isinstance(value, str) and value:
                rules[str(key)] = value

    idx = candidate["index"]
    field_type = candidate["field_type"]
    steps[idx]["input_value"] = rules.get(field_type, rules["generic"])
    return modified, True, None


def mutate_empty_required_fields(
    flow_json: dict,
    *,
    do_not_mutate_fields: set[str] | None = None,
) -> tuple[dict, bool, str | None]:
    """Clear ALL type-action input values to empty string.

    A well-behaved form must reject submissions when required fields are blank —
    so this is a negative-test variant (expected_outcome='fail').
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    candidates = find_all_type_candidates(steps, do_not_mutate_fields=do_not_mutate_fields)
    if not candidates:
        return modified, False, "no_type_action"
    for c in candidates:
        steps[c["index"]]["input_value"] = ""
    return modified, True, None


def mutate_boundary_length(
    flow_json: dict,
    *,
    do_not_mutate_fields: set[str] | None = None,
    length: int = 10_000,
) -> tuple[dict, bool, str | None]:
    """Fill every type-action field with an extremely long string.

    A well-behaved app must reject or truncate the oversized input — the flow
    failing to complete IS the expected outcome (expected_outcome='fail').
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    candidates = find_all_type_candidates(steps, do_not_mutate_fields=do_not_mutate_fields)
    if not candidates:
        return modified, False, "no_type_action"
    long_value = "A" * length
    for c in candidates:
        steps[c["index"]]["input_value"] = long_value
    return modified, True, None


def mutate_xss_probe(
    flow_json: dict,
    *,
    do_not_mutate_fields: set[str] | None = None,
) -> tuple[dict, bool, str | None]:
    """Inject a reflected-XSS payload into every type-action field.

    A secure app must reject or sanitize the payload — the flow should fail
    (e.g. validation error, form rejected).  That failure is the expected
    outcome (expected_outcome='fail').  If the flow somehow *succeeds* the
    malicious input was accepted, which is a real vulnerability.
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    candidates = find_all_type_candidates(steps, do_not_mutate_fields=do_not_mutate_fields)
    if not candidates:
        return modified, False, "no_type_action"
    xss_payload = "<script>alert('xss')</script>"
    for c in candidates:
        steps[c["index"]]["input_value"] = xss_payload
    return modified, True, None


def mutate_sql_injection(
    flow_json: dict,
    *,
    do_not_mutate_fields: set[str] | None = None,
) -> tuple[dict, bool, str | None]:
    """Inject a classic SQL injection payload into every type-action field.

    A secure app must reject or sanitize the payload — the flow should fail
    (e.g. validation error, query rejected).  That failure is the expected
    outcome (expected_outcome='fail').  If the flow somehow *succeeds* the
    injection payload was processed, which is a real vulnerability.
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    candidates = find_all_type_candidates(steps, do_not_mutate_fields=do_not_mutate_fields)
    if not candidates:
        return modified, False, "no_type_action"
    sql_payload = "' OR '1'='1' --"
    for c in candidates:
        steps[c["index"]]["input_value"] = sql_payload
    return modified, True, None


def mutate_type_mismatch(
    flow_json: dict,
    *,
    do_not_mutate_fields: set[str] | None = None,
) -> tuple[dict, bool, str | None]:
    """Put the wrong data type into typed fields (e.g. letters in an email field,
    numbers-only string where free text is expected).

    A well-behaved form must reject this — negative-test (expected_outcome='fail').
    Targets fields with known types (email, password, search, coupon); skips generic.
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    candidates = find_all_type_candidates(
        steps, do_not_mutate_fields=do_not_mutate_fields, include_generic=False
    )
    if not candidates:
        return modified, False, "no_typed_field"

    TYPE_MISMATCH_VALUES = {
        "email": "notanemail",              # missing @ and domain
        "password": "x",                   # single char — below any min-length
        "search": "!search?invalid#",       # special chars that break strict query parsers
        "coupon": "!@#$%^&*()",             # special chars only
    }
    for c in candidates:
        mismatched = TYPE_MISMATCH_VALUES.get(c["field_type"], "__MISMATCH__")
        steps[c["index"]]["input_value"] = mismatched
    return modified, True, None


def inject_double_submit(flow_json: dict) -> tuple[dict, bool, str | None]:
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    submit_idx = find_submit_intent_index(steps, last=True)
    if submit_idx is None:
        return modified, False, "no_submit_intent_action"

    # Duplicate the submit step without marking it optional.
    # If the app correctly disables the button or ignores the second click,
    # the executor will still attempt it — a real duplicate-submission bug
    # (e.g. double-charge) will show up as a 2xx response count discrepancy
    # or a UI-level assertion failure in subsequent steps.
    second_submit = deepcopy(steps[submit_idx])
    second_submit.pop("failure_behavior", None)  # must not be optional
    second_submit["step_id"] = f"generated_double_submit_{submit_idx}"
    steps.insert(submit_idx + 1, second_submit)
    return modified, True, None


def inject_back_navigation(flow_json: dict) -> tuple[dict, bool, str | None]:
    """Insert go_back after the state-changing step, then replay that step.

    Resulting flow:
      steps[0..S]  →  go_back  →  replay_of_step_S  →  steps[S+1..]

    This tests: "If the user goes back after a state change, can they redo
    the action and continue the flow?"  The previous implementation only
    inserted go_back with no replay, leaving the browser on the wrong page
    so every subsequent step would timeout.
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    insert_at = find_state_change_injection_index(steps)
    if insert_at is None:
        return modified, False, "no_state_change_opportunity"

    # The state-changing step is at insert_at - 1 (find_state_change_injection_index
    # returns idx + 1, i.e. the position *after* the step that caused the change).
    state_change_idx = insert_at - 1
    state_change_step = deepcopy(steps[state_change_idx])
    state_change_step["step_id"] = f"generated_redo_{state_change_idx}"

    # Insert go_back first, then the replayed step right after
    steps.insert(
        insert_at,
        {
            "step_id": f"generated_go_back_{insert_at}",
            "order": insert_at + 1,
            "action": "go_back",
            "target": None,
            "input_value": None,
        },
    )
    # insert_at + 1 because go_back was inserted at insert_at
    steps.insert(insert_at + 1, state_change_step)
    return modified, True, None


def inject_refresh(flow_json: dict) -> tuple[dict, bool, str | None]:
    """Insert a page refresh after the state-changing step.

    Unlike back_navigation, refresh stays on the same URL — the browser
    reloads the current page.  A wait_for_stable sentinel step is added
    after the refresh so the executor gives the page time to re-render
    before attempting to locate elements.
    """
    modified = deepcopy(flow_json)
    steps = modified.get("steps") if isinstance(modified.get("steps"), list) else []
    insert_at = find_state_change_injection_index(steps)
    if insert_at is None:
        return modified, False, "no_state_change_opportunity"

    steps.insert(
        insert_at,
        {
            "step_id": f"generated_refresh_{insert_at}",
            "order": insert_at + 1,
            "action": "refresh",
            "target": None,
            "input_value": None,
        },
    )
    # Add a stability wait after the refresh so the page finishes rendering
    steps.insert(
        insert_at + 1,
        {
            "step_id": f"generated_wait_stable_{insert_at}",
            "order": insert_at + 2,
            "action": "wait_for_stable",
            "target": None,
            "input_value": None,
        },
    )
    return modified, True, None
