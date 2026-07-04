"""Assertion-driven verdict evaluation for semantic mutation intents."""

from __future__ import annotations


def _network_summary(run: dict) -> dict:
    diagnostics = run.get("diagnostics_json") if isinstance(run, dict) else {}
    if not isinstance(diagnostics, dict):
        return {}
    summary = diagnostics.get("summary")
    if not isinstance(summary, dict):
        return {}
    network = summary.get("network_summary")
    return network if isinstance(network, dict) else {}


def _double_submit_summary(run: dict) -> dict:
    diagnostics = run.get("diagnostics_json") if isinstance(run, dict) else {}
    if not isinstance(diagnostics, dict):
        return {}
    summary = diagnostics.get("summary")
    if not isinstance(summary, dict):
        return {}
    duplicate_submit = summary.get("double_submit_summary")
    return duplicate_submit if isinstance(duplicate_submit, dict) else {}


def _assert_run_not_passed(run: dict) -> dict:
    passed = (run.get("status") == "passed")
    return {
        "id": "run_not_passed",
        "status": "passed" if not passed else "failed",
        "reason": "run_status_not_passed" if not passed else "run_completed_successfully",
        "evidence": {"run_status": run.get("status")},
    }


def _assert_has_failure_signal(steps: list[dict]) -> dict:
    failed_steps = [step for step in steps if step.get("status") == "failed"]
    return {
        "id": "has_failure_signal",
        "status": "passed" if failed_steps else "failed",
        "reason": "step_failure_present" if failed_steps else "no_step_failures_detected",
        "evidence": {"failed_step_count": len(failed_steps)},
    }


def _assert_run_passed(run: dict) -> dict:
    passed = run.get("status") == "passed"
    return {
        "id": "run_passed",
        "status": "passed" if passed else "failed",
        "reason": "run_completed_successfully" if passed else "run_status_not_passed",
        "evidence": {"run_status": run.get("status")},
    }


def _assert_has_first_party_rejection_signal(run: dict, steps: list[dict]) -> dict:
    failed_steps = [step for step in steps if step.get("status") == "failed"]
    network = _network_summary(run)
    first_party_4xx = int(network.get("first_party_status_4xx_count") or 0)
    first_party_request_failed = int(network.get("first_party_request_failed_count") or 0)
    first_party_5xx = int(network.get("first_party_status_5xx_count") or 0)

    has_rejection = bool(failed_steps) or first_party_4xx > 0 or first_party_request_failed > 0 or first_party_5xx > 0
    return {
        "id": "has_first_party_rejection_signal",
        "status": "passed" if has_rejection else "failed",
        "reason": "rejection_signal_present" if has_rejection else "no_rejection_signal_detected",
        "evidence": {
            "failed_step_count": len(failed_steps),
            "first_party_status_4xx_count": first_party_4xx,
            "first_party_request_failed_count": first_party_request_failed,
            "first_party_status_5xx_count": first_party_5xx,
        },
    }


def _assert_no_first_party_server_crash(run: dict) -> dict:
    network = _network_summary(run)
    first_party_5xx = int(network.get("first_party_status_5xx_count") or 0)
    passed = first_party_5xx == 0
    return {
        "id": "no_first_party_server_crash",
        "status": "passed" if passed else "failed",
        "reason": "no_first_party_5xx_detected" if passed else "first_party_5xx_detected",
        "evidence": {
            "first_party_status_5xx_count": first_party_5xx,
        },
    }


def _assert_no_multiple_first_party_successes(run: dict) -> dict:
    duplicate_submit = _double_submit_summary(run)
    verdict = str(duplicate_submit.get("verdict") or "").lower()
    if verdict in {"pass", "fail", "inconclusive"}:
        status = "passed" if verdict == "pass" else ("failed" if verdict == "fail" else "skipped")
        return {
            "id": "no_multiple_first_party_successes",
            "status": status,
            "reason": str(duplicate_submit.get("reason") or "double_submit_summary"),
            "evidence": {
                "duplicate_submit_summary": {
                    "duplicate_success_operations": duplicate_submit.get("duplicate_success_operations", 0),
                    "distinct_effect_duplications": duplicate_submit.get("distinct_effect_duplications", 0),
                    "idempotent_replays": duplicate_submit.get("idempotent_replays", 0),
                    "inconclusive_operations": duplicate_submit.get("inconclusive_operations", 0),
                }
            },
        }

    network = _network_summary(run)
    first_party_2xx = int(network.get("first_party_status_2xx_count") or 0)
    passed = first_party_2xx <= 1
    return {
        "id": "no_multiple_first_party_successes",
        "status": "passed" if passed else "failed",
        "reason": "legacy_single_or_no_first_party_success" if passed else "legacy_multiple_first_party_success_responses_detected",
        "evidence": {
            "first_party_status_2xx_count": first_party_2xx,
        },
    }


def evaluate_assertion_set(assertions: list[dict], run: dict, steps: list[dict]) -> list[dict]:
    results: list[dict] = []
    for assertion in assertions:
        assertion_id = assertion.get("id")
        if assertion_id == "run_not_passed":
            results.append(_assert_run_not_passed(run))
        elif assertion_id == "has_failure_signal":
            results.append(_assert_has_failure_signal(steps))
        elif assertion_id == "run_passed":
            results.append(_assert_run_passed(run))
        elif assertion_id == "has_first_party_rejection_signal":
            results.append(_assert_has_first_party_rejection_signal(run, steps))
        elif assertion_id == "no_first_party_server_crash":
            results.append(_assert_no_first_party_server_crash(run))
        elif assertion_id == "no_multiple_first_party_successes":
            results.append(_assert_no_multiple_first_party_successes(run))
        else:
            results.append(
                {
                    "id": assertion_id or "unknown",
                    "status": "skipped",
                    "reason": "unsupported_assertion",
                    "evidence": {},
                }
            )
    return results


def decide_semantic_verdict(
    *,
    expected_outcome: str,
    mutation_meaningful: bool,
    assertion_results: list[dict],
    fallback_status: str,
) -> dict:
    if expected_outcome == "fail" and not mutation_meaningful:
        return {
            "verdict": "inconclusive",
            "reason": "mutation_not_semantically_meaningful",
        }

    passed = [item for item in assertion_results if item.get("status") == "passed"]
    failed = [item for item in assertion_results if item.get("status") == "failed"]

    if failed:
        return {
            "verdict": "fail",
            "reason": "assertions_failed",
        }

    if passed:
        return {
            "verdict": "pass",
            "reason": "assertions_satisfied",
        }

    return {
        "verdict": "inconclusive",
        "reason": "insufficient_assertion_signal",
    }
