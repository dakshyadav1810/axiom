"""
Test execution engine — bridges repositories, test-case generation, and resolver executor.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional
from urllib.parse import urlparse

from ..models.resolver_models import FailureReason, FlowDefinition as ResolverFlowDef, ActionResult, OnFailure
from .executor import Executor, ExecutorConfig

from .db.repo_factory import (
    get_backend,
    FlowRepo,
    ProjectRepo,
    RunGroupRepo,
    TestCaseRepo,
    TestResultRepo,
    TestRunRepo,
)
from .test_generation import generate_test_cases, VARIATION_ORDER, planned_assertions, intent_for_variation
from .semantic_assertions import evaluate_assertion_set, decide_semantic_verdict

# Authoritative expected_outcome per variation_type — derived from VARIATION_ORDER so the
# inversion logic works even when the Supabase column is null or missing (e.g. migration
# not yet applied).  DB value takes precedence if explicitly set to a non-null string.
_EXPECTED_OUTCOME_BY_TYPE: dict[str, str] = {
    spec.variation_type: spec.expected_outcome for spec in VARIATION_ORDER
}

StepCallback = Callable[[dict], Coroutine[Any, Any, None]]
DEFAULT_TIMEOUT_MULTIPLIERS = {"normal": 1.0, "mobile": 1.5, "3g": 3.0}
DEFAULT_DIAGNOSTICS_POLICY = "signal_gated"
DEFAULT_TIMEOUT_POLICY = "profile_aware"
DEFAULT_VARIATION_MODE = "compat_only"
DEFAULT_REPLAY_MODE = "deterministic_first"
DEFAULT_RESOLVER_FALLBACK_POLICY = "balanced"
DEFAULT_NETWORK_NOISE_PATTERNS = [
    "net::err_aborted",
    "err_aborted",
    "/cdn-cgi/rum",
    "analytics",
    "telemetry",
]

# URL query/path fragments that indicate framework-internal prefetch requests
# which are routinely aborted on navigation and are never real bugs.
_PREFETCH_URL_PATTERNS = [
    "_rsc=",       # Next.js React Server Component prefetches
    "__nextjs",    # Other Next.js internals
    "?_data=",     # Remix loader prefetches
    "?index",      # Remix index route prefetches
]

# Domains/URL fragments to exclude from silent error detection — these are
# third-party tracking / analytics services whose 4xx/5xx responses are not
# indicative of real application bugs.
SILENT_ERROR_NOISE_DOMAINS = [
    "segment.io", "segment.com",
    "mixpanel.com",
    "sentry.io", "sentry-cdn.com",
    "google-analytics.com", "googletagmanager.com",
    "googleapis.com/analytics",
    "hotjar.com",
    "intercom.io", "intercomcdn.com",
    "facebook.com/tr", "facebook.net",
    "doubleclick.net",
    "fullstory.com",
    "heap.io", "heapanalytics.com",
    "amplitude.com",
    "clarity.ms",
    "newrelic.com",
    "datadoghq.com",
    "bugsnag.com",
    "launchdarkly.com",
    "cdn-cgi/",
    "chrome-extension://",
    "favicon.ico",
    "pendo.io",
    "hubspot.com",
    "optimizely.com",
    "bat.bing.com",
    "plausible.io",
    "posthog.com",
]
RESOLVER_FAILURE_TOKENS = {
    "low_confidence",
    "selector_no_match",
    "semantic_ambiguity",
    "semantic_no_match",
    "context_conflict",
}

# Variation types considered safe for compat_only mode.
# Destructive mutations (double_submit, back_navigation, refresh_mid_flow)
# are excluded — they can create duplicate orders or corrupt in-flight state.
# All input-mutation variants are non-destructive (they only change field values,
# not application state) so they belong here.
COMPAT_SAFE_VARIATION_TYPES = {
    "baseline",
    "input_validation",
    "empty_required_fields",
    "type_mismatch",
    "boundary_length",
    "xss_probe",
    "sql_injection",
    "mobile_viewport",
    "slow_network_3g",
}

MAX_TEST_WORKERS = max(1, int(os.getenv("AXIOM_MAX_TEST_WORKERS", "4")))
_TEST_WORKER_SEMAPHORE = asyncio.Semaphore(MAX_TEST_WORKERS)


async def _run_with_worker_slot(coro):
    async with _TEST_WORKER_SEMAPHORE:
        return await coro


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_failure(error: str | None) -> str | None:
    text = (error or "").lower().strip()
    if not text:
        return None
    if "timeout" in text:
        return "timeout"
    if text in {"low_confidence", "selector_no_match", "semantic_ambiguity", "semantic_no_match"}:
        return "resolver_failure"
    if "element" in text and "not found" in text:
        return "resolver_failure"
    if "network" in text:
        return "network_error"
    if "contract_violation" in text:
        return "contract_violation"
    if "action_failure" in text:
        return "action_failure"
    return "action_failure"


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)


def _extract_project_config(project: dict | None) -> dict:
    cfg = (project or {}).get("test_config_json", {}) if isinstance(project, dict) else {}
    if not isinstance(cfg, dict):
        cfg = {}

    input_rules = cfg.get("input_mutation_rules", {})
    if not isinstance(input_rules, dict):
        input_rules = {}

    block = cfg.get("do_not_mutate_fields", []) if isinstance(cfg.get("do_not_mutate_fields", []), list) else []
    blocked_fields = {
        str(item).strip().lower()
        for item in block
        if isinstance(item, str) and item.strip()
    }

    contract_allowlist_raw = cfg.get("contract_allowlist", [])
    contract_allowlist = [
        str(item).strip()
        for item in contract_allowlist_raw
        if isinstance(item, str) and item.strip()
    ] if isinstance(contract_allowlist_raw, list) else []

    console_ignore_raw = cfg.get("console_ignore_patterns", [])
    console_ignore_patterns = [
        str(item).strip().lower()
        for item in console_ignore_raw
        if isinstance(item, str) and item.strip()
    ] if isinstance(console_ignore_raw, list) else []
    network_noise_raw = cfg.get("network_noise_patterns", [])
    network_noise_patterns = list(DEFAULT_NETWORK_NOISE_PATTERNS)
    if isinstance(network_noise_raw, list):
        for item in network_noise_raw:
            if isinstance(item, str) and item.strip():
                network_noise_patterns.append(item.strip().lower())
    # Keep deterministic order with dedup.
    network_noise_patterns = list(dict.fromkeys(network_noise_patterns))

    raw_multipliers = cfg.get("timeout_multipliers", {})
    multipliers = dict(DEFAULT_TIMEOUT_MULTIPLIERS)
    if isinstance(raw_multipliers, dict):
        for key in ("normal", "mobile", "3g"):
            value = raw_multipliers.get(key)
            if isinstance(value, (int, float)) and value > 0:
                multipliers[key] = float(value)

    diagnostics_policy = str(cfg.get("diagnostics_policy") or DEFAULT_DIAGNOSTICS_POLICY).strip().lower()
    timeout_policy = str(cfg.get("timeout_policy") or DEFAULT_TIMEOUT_POLICY).strip().lower()
    variation_mode = str(cfg.get("variation_mode") or DEFAULT_VARIATION_MODE).strip().lower()
    replay_mode = str(cfg.get("replay_mode") or DEFAULT_REPLAY_MODE).strip().lower()
    resolver_fallback_policy = str(
        cfg.get("resolver_fallback_policy") or DEFAULT_RESOLVER_FALLBACK_POLICY
    ).strip().lower()

    relevance_threshold_raw = cfg.get("mutation_relevance_threshold", 0.45)
    if isinstance(relevance_threshold_raw, (int, float)):
        mutation_relevance_threshold = max(0.0, min(1.0, float(relevance_threshold_raw)))
    else:
        mutation_relevance_threshold = 0.45

    return {
        "input_mutation_rules": input_rules,
        "do_not_mutate_fields": blocked_fields,
        "contract_allowlist": contract_allowlist,
        "console_ignore_patterns": console_ignore_patterns,
        "network_noise_patterns": network_noise_patterns,
        "diagnostics_policy": diagnostics_policy or DEFAULT_DIAGNOSTICS_POLICY,
        "timeout_policy": timeout_policy or DEFAULT_TIMEOUT_POLICY,
        "timeout_multipliers": multipliers,
        "variation_mode": variation_mode or DEFAULT_VARIATION_MODE,
        "replay_mode": replay_mode or DEFAULT_REPLAY_MODE,
        "resolver_fallback_policy": resolver_fallback_policy or DEFAULT_RESOLVER_FALLBACK_POLICY,
        "mutation_relevance_threshold": mutation_relevance_threshold,
    }


def _compute_mutation_efficacy(
    *,
    applicability_meta: dict,
    step_rows: list[dict],
    run_status: str,
) -> dict:
    mutation_targets = applicability_meta.get("mutation_targets")
    if not isinstance(mutation_targets, list):
        mutation_targets = []

    target_indices: list[int] = []
    for target in mutation_targets:
        if not isinstance(target, dict):
            continue
        index = target.get("index")
        if isinstance(index, int):
            target_indices.append(index)

    executed_indices = [
        int(step.get("step_order"))
        for step in step_rows
        if isinstance(step, dict) and isinstance(step.get("step_order"), int)
    ]
    max_executed = max(executed_indices) if executed_indices else -1

    semantic_snapshot = applicability_meta.get("semantic_model_snapshot")
    submit_idx = semantic_snapshot.get("submit_idx") if isinstance(semantic_snapshot, dict) else None
    submit_attempted = bool(executed_indices) and (not isinstance(submit_idx, int) or max_executed >= submit_idx)

    target_touched = any(index <= max_executed for index in target_indices)
    failure_signal = any(
        isinstance(step, dict) and step.get("status") == "failed"
        for step in step_rows
    )

    score_raw = applicability_meta.get("target_relevance_score")
    score = float(score_raw) if isinstance(score_raw, (int, float)) else 0.0
    threshold_raw = applicability_meta.get("mutation_relevance_threshold", 0.45)
    threshold = float(threshold_raw) if isinstance(threshold_raw, (int, float)) else 0.45
    threshold = max(0.0, min(1.0, threshold))

    relevance_meaningful = bool(applicability_meta.get("target_relevance_meaningful")) and score >= threshold
    observed_effect = failure_signal or run_status != "passed"

    meaningful = bool(target_indices) and relevance_meaningful and submit_attempted and (target_touched or observed_effect)

    reasons: list[str] = []
    if not target_indices:
        reasons.append("no_mutation_targets")
    if not relevance_meaningful:
        reasons.append("low_relevance")
    if not submit_attempted:
        reasons.append("submit_not_attempted")
    if not (target_touched or observed_effect):
        reasons.append("no_observable_effect")

    return {
        "applied": bool(target_indices),
        "meaningful": meaningful,
        "submit_attempted": submit_attempted,
        "target_touched": target_touched,
        "observed_effect": observed_effect,
        "target_count": len(target_indices),
        "relevance_score": score,
        "relevance_threshold": threshold,
        "reasons": reasons,
    }


def _normalize_host(url: str | None) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    return (parsed.hostname or "").lower()


def _base_domain(host: str) -> str:
    parts = [p for p in host.split(".") if p]
    if len(parts) <= 2:
        return ".".join(parts)
    return ".".join(parts[-2:])


def _is_first_party_url(url: str | None, base_url: str | None) -> bool:
    host = _normalize_host(url)
    base_host = _normalize_host(base_url)
    if not host or not base_host:
        return False
    if host == base_host or host.endswith(f".{base_host}"):
        return True
    return _base_domain(host) == _base_domain(base_host)


def _url_matches_allowlist(url: str | None, allowlist: list[str]) -> bool:
    if not allowlist:
        return False
    raw_url = str(url or "")
    parsed = urlparse(raw_url)
    normalized = f"{parsed.netloc}{parsed.path}".lower() if parsed.netloc else raw_url.lower()
    return any(pattern.lower() in normalized for pattern in allowlist)


def _compute_effective_timeout(
    timeout_ms: int,
    environment_profile: str,
    timeout_policy: str,
    timeout_multipliers: Optional[dict],
) -> int:
    profile = (environment_profile or "normal").lower()
    multipliers = dict(DEFAULT_TIMEOUT_MULTIPLIERS)
    if isinstance(timeout_multipliers, dict):
        for key in ("normal", "mobile", "3g"):
            value = timeout_multipliers.get(key)
            if isinstance(value, (int, float)) and value > 0:
                multipliers[key] = float(value)
    if timeout_policy != "profile_aware":
        return timeout_ms
    factor = multipliers.get(profile, multipliers["normal"])
    return max(1, int(timeout_ms * factor))


def _run_level_timeout_seconds(step_count: int, effective_timeout_ms: int) -> int:
    # Keep a generous floor while scaling with profile-adjusted step timeout.
    per_step = max(3.0, (effective_timeout_ms / 1000.0) * 1.5)
    return int(max(180.0, per_step * max(step_count + 2, 6)))


def _flow_is_mobile(flow: dict) -> bool:
    if bool(flow.get("is_mobile", False)):
        return True
    flow_json = flow.get("flow_json") if isinstance(flow.get("flow_json"), dict) else {}
    general_settings = flow_json.get("general_settings") if isinstance(flow_json.get("general_settings"), dict) else {}
    return bool(general_settings.get("is_mobile", False))


def _top_counter(counter: Counter[str], limit: int = 5) -> list[dict]:
    return [{"value": key, "count": count} for key, count in counter.most_common(limit)]


def _normalize_operation_url(url: str) -> str:
    parsed = urlparse(str(url or ""))
    path = parsed.path or "/"
    return f"{(parsed.netloc or '').lower()}{path}"


def _redact_volatile_payload_fields(value: Any) -> Any:
    volatile_key_pattern = re.compile(
        r"(^|_)(timestamp|ts|nonce|token|signature|sig|traceid|trace_id|requestid|request_id|correlationid|correlation_id)$",
        re.IGNORECASE,
    )
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_str = str(key)
            if volatile_key_pattern.search(key_str):
                continue
            redacted[key_str] = _redact_volatile_payload_fields(child)
        return redacted
    if isinstance(value, list):
        return [_redact_volatile_payload_fields(item) for item in value]
    return value


def _stable_payload_hash(post_data: Optional[str]) -> str:
    raw = str(post_data or "").strip()
    if not raw:
        return ""
    normalized = raw
    try:
        parsed = json.loads(raw)
        parsed = _redact_volatile_payload_fields(parsed)
        normalized = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        normalized = raw
    return hashlib.sha1(normalized.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _extract_idempotency_values_from_payload(payload: Any, *, max_values: int = 8) -> list[str]:
    key_hints = (
        "idempotency",
        "idempotency_key",
        "idempotencykey",
    )
    results: list[str] = []

    def _visit(node: Any) -> None:
        if len(results) >= max_values:
            return
        if isinstance(node, dict):
            for key, val in node.items():
                key_l = str(key).lower()
                if any(h in key_l for h in key_hints) and isinstance(val, (str, int, float)):
                    text = str(val).strip()
                    if text and text not in results:
                        results.append(text)
                _visit(val)
                if len(results) >= max_values:
                    return
        elif isinstance(node, list):
            for item in node:
                _visit(item)
                if len(results) >= max_values:
                    return

    _visit(payload)
    return results


def _extract_request_dedup_keys(entry: dict) -> list[str]:
    headers = entry.get("headers") if isinstance(entry.get("headers"), dict) else {}
    keys: list[str] = []
    if headers:
        lower_headers = {str(k).lower(): str(v).strip() for k, v in headers.items() if v is not None}
        for header_name in (
            "idempotency-key",
            "x-idempotency-key",
        ):
            val = lower_headers.get(header_name)
            if val:
                keys.append(f"hdr:{header_name}:{val}")

    post_data = entry.get("post_data")
    raw = str(post_data or "").strip()
    if raw:
        try:
            payload = json.loads(raw)
            for payload_id in _extract_idempotency_values_from_payload(payload):
                keys.append(f"payload:{payload_id}")
        except Exception:
            pass

    deduped: list[str] = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
    return deduped


def _extract_response_effect_keys(entry: dict) -> list[str]:
    headers = entry.get("headers") if isinstance(entry.get("headers"), dict) else {}
    lower_headers = {str(k).lower(): str(v).strip() for k, v in headers.items() if v is not None}
    keys: list[str] = []

    for header_name in (
        "location",
        "x-order-id",
        "x-charge-id",
        "x-payment-id",
        "x-resource-id",
        "x-entity-id",
        "x-result-id",
        "idempotency-key",
        "x-idempotency-key",
    ):
        val = lower_headers.get(header_name)
        if val:
            keys.append(f"hdr:{header_name}:{val}")

    deduped: list[str] = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
    return deduped


def _build_double_submit_summary(*, base_url: str, network_logs: list[dict]) -> dict:
    request_entries = [entry for entry in network_logs if entry.get("event") == "request"]
    response_entries = [entry for entry in network_logs if entry.get("event") == "response"]

    mutating_methods = {"POST", "PUT", "PATCH", "DELETE"}
    op_buckets: dict[str, dict[str, Any]] = {}

    for entry in request_entries:
        method = str(entry.get("method") or "").upper()
        url = str(entry.get("url") or "")
        if method not in mutating_methods:
            continue
        if not _is_first_party_url(url, base_url):
            continue
        normalized_url = _normalize_operation_url(url)
        payload_hash = _stable_payload_hash(entry.get("post_data"))
        op_key = f"{method} {normalized_url}::{payload_hash}"
        bucket = op_buckets.setdefault(
            op_key,
            {
                "operation": f"{method} {normalized_url}",
                "payload_hash": payload_hash,
                "request_count": 0,
                "response_count": 0,
                "success_count": 0,
                "dedup_keys": set(),
                "effect_keys": set(),
            },
        )
        bucket["request_count"] += 1
        for dedup_key in _extract_request_dedup_keys(entry):
            bucket["dedup_keys"].add(dedup_key)

    for entry in response_entries:
        method = str(entry.get("method") or "").upper()
        url = str(entry.get("url") or "")
        status = int(entry.get("status") or 0)
        if method not in mutating_methods:
            continue
        if not _is_first_party_url(url, base_url):
            continue
        normalized_url = _normalize_operation_url(url)
        payload_hash = ""
        op_key = f"{method} {normalized_url}::{payload_hash}"

        # Prefer exact payload bucket if one exists; otherwise fold into
        # URL/method-only fallback bucket.
        matching_keys = [k for k in op_buckets.keys() if k.startswith(f"{method} {normalized_url}::")]
        if len(matching_keys) == 1:
            op_key = matching_keys[0]
        elif op_key not in op_buckets:
            op_buckets[op_key] = {
                "operation": f"{method} {normalized_url}",
                "payload_hash": payload_hash,
                "request_count": 0,
                "response_count": 0,
                "success_count": 0,
                "dedup_keys": set(),
                "effect_keys": set(),
            }

        bucket = op_buckets[op_key]
        bucket["response_count"] += 1
        if 200 <= status < 300:
            bucket["success_count"] += 1
            for effect_key in _extract_response_effect_keys(entry):
                bucket["effect_keys"].add(effect_key)

    operations: list[dict] = []
    duplicate_success_ops = 0
    distinct_effect_duplications = 0
    idempotent_replays = 0
    inconclusive_ops = 0

    for bucket in op_buckets.values():
        dedup_keys = sorted(bucket["dedup_keys"])
        effect_keys = sorted(bucket["effect_keys"])
        success_count = int(bucket["success_count"])

        distinct_effect_count: Optional[int] = None
        if effect_keys:
            distinct_effect_count = len(effect_keys)
        elif dedup_keys:
            distinct_effect_count = len(dedup_keys)

        has_duplicate_success = success_count >= 2
        has_distinct_duplicate_effect = bool(has_duplicate_success and isinstance(distinct_effect_count, int) and distinct_effect_count >= 2)
        is_idempotent_replay = bool(has_duplicate_success and isinstance(distinct_effect_count, int) and distinct_effect_count <= 1)
        is_inconclusive = bool(has_duplicate_success and distinct_effect_count is None)

        if has_duplicate_success:
            duplicate_success_ops += 1
        if has_distinct_duplicate_effect:
            distinct_effect_duplications += 1
        if is_idempotent_replay:
            idempotent_replays += 1
        if is_inconclusive:
            inconclusive_ops += 1

        operations.append(
            {
                "operation": bucket["operation"],
                "payload_hash": bucket["payload_hash"],
                "request_count": int(bucket["request_count"]),
                "response_count": int(bucket["response_count"]),
                "success_count": success_count,
                "distinct_effect_count": distinct_effect_count,
                "has_duplicate_success": has_duplicate_success,
                "has_distinct_duplicate_effect": has_distinct_duplicate_effect,
                "is_idempotent_replay": is_idempotent_replay,
                "is_inconclusive": is_inconclusive,
            }
        )

    if distinct_effect_duplications > 0:
        verdict = "fail"
        reason = "multiple_distinct_effects_from_duplicate_submit"
    elif duplicate_success_ops > 0 and inconclusive_ops > 0 and idempotent_replays == 0:
        verdict = "inconclusive"
        reason = "duplicate_success_without_effect_identity"
    else:
        verdict = "pass"
        reason = "duplicate_submit_idempotent_or_absent"

    return {
        "verdict": verdict,
        "reason": reason,
        "duplicate_success_operations": duplicate_success_ops,
        "distinct_effect_duplications": distinct_effect_duplications,
        "idempotent_replays": idempotent_replays,
        "inconclusive_operations": inconclusive_ops,
        "operations": operations,
    }


def _detect_silent_errors(
    *,
    step_time_windows: list[dict],
    network_logs: list[dict],
    console_logs: list[dict],
    base_url: str,
    network_noise_patterns: list[str] | None = None,
) -> list[dict]:
    """Cross-join passed steps with network/console errors in the same time window.

    A *silent error* is when a test step reports success but the underlying
    network layer returned an error response (4xx/5xx) or a request failed
    entirely, or the console logged an error.  These are bugs the test said
    didn't exist.
    """
    noise_domains = SILENT_ERROR_NOISE_DOMAINS
    noise_pats = network_noise_patterns or []

    # Pre-filter lists once for efficiency
    response_entries = [e for e in network_logs if e.get("event") == "response" and e.get("time") is not None]
    failed_entries = [e for e in network_logs if e.get("event") == "request_failed" and e.get("time") is not None]
    error_console = [e for e in console_logs if e.get("type") == "error" and e.get("time") is not None]

    findings: list[dict] = []

    for window in step_time_windows:
        if not window["passed"]:
            continue

        t_start = window["start_time"]
        t_end = window["end_time"]
        # 500ms grace after step ends — async responses may still be landing
        t_end_grace = t_end + 0.5
        step_order = window["step_order"]
        step_id = window.get("step_id", "")

        # ── Network error responses during this step ──
        for entry in response_entries:
            t = entry["time"]
            if t < t_start or t > t_end_grace:
                continue
            status = int(entry.get("status") or 0)
            if status < 400:
                continue
            url = str(entry.get("url") or "")
            url_lower = url.lower()
            if any(d in url_lower for d in noise_domains):
                continue
            if any(p in url_lower for p in noise_pats):
                continue

            is_fp = _is_first_party_url(url, base_url)
            severity = "critical" if (is_fp and status >= 500) else ("high" if status >= 500 else "medium")
            findings.append({
                "type": "silent_network_error",
                "severity": severity,
                "step_order": step_order,
                "step_id": step_id,
                "message": f"Step #{step_order} passed but API returned HTTP {status}",
                "detail": {
                    "url": url,
                    "method": entry.get("method"),
                    "status": status,
                    "first_party": is_fp,
                },
            })

        # ── Hard request failures during this step ──
        for entry in failed_entries:
            t = entry["time"]
            if t < t_start or t > t_end_grace:
                continue
            url = str(entry.get("url") or "")
            url_lower = url.lower()
            failure = str(entry.get("failure") or "").lower()
            if any(d in url_lower for d in noise_domains):
                continue
            # Check noise patterns against both URL and failure reason
            if any(p in url_lower or p in failure for p in noise_pats):
                continue
            # Skip framework-internal prefetch requests (Next.js RSC, Remix, etc.)
            # — these are speculatively fired and routinely aborted on navigation
            if any(p in url for p in _PREFETCH_URL_PATTERNS):
                continue
            findings.append({
                "type": "silent_request_failure",
                "severity": "high",
                "step_order": step_order,
                "step_id": step_id,
                "message": f"Step #{step_order} passed but a network request failed",
                "detail": {
                    "url": url,
                    "method": entry.get("method"),
                    "failure": entry.get("failure"),
                },
            })

        # ── Console errors during this step ──
        for entry in error_console:
            t = entry["time"]
            if t < t_start or t > t_end_grace:
                continue
            text = str(entry.get("text") or "")
            if len(text) < 5:
                continue
            findings.append({
                "type": "silent_console_error",
                "severity": "medium",
                "step_order": step_order,
                "step_id": step_id,
                "message": f"Step #{step_order} passed but console error occurred",
                "detail": {
                    "text": text[:500],
                    "location": entry.get("location"),
                },
            })

    # Deduplicate by (type, step_order, url_or_text)
    seen: set[str] = set()
    deduped: list[dict] = []
    for f in findings:
        parts = [f["type"], str(f["step_order"])]
        detail = f.get("detail", {})
        parts.append(detail.get("url") or detail.get("text", "")[:100])
        key = "|".join(parts)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return deduped


def _summarize_diagnostics(
    *,
    base_url: str,
    network_logs: list[dict],
    console_logs: list[dict],
    contract_violations: list[dict],
    cookie_added: list[dict],
    cookie_removed: list[dict],
    cookie_changed: list[dict],
    contract_allowlist: list[str],
    console_ignore_patterns: list[str],
    network_noise_patterns: Optional[list[str]] = None,
) -> dict:
    noise_patterns = network_noise_patterns or list(DEFAULT_NETWORK_NOISE_PATTERNS)
    response_entries = [entry for entry in network_logs if entry.get("event") == "response"]
    failed_entries = [entry for entry in network_logs if entry.get("event") == "request_failed"]
    request_entries = [entry for entry in network_logs if entry.get("event") == "request"]

    first_party_5xx = 0
    first_party_4xx = 0
    first_party_2xx = 0
    first_party_request_failed = 0
    all_4xx = 0
    all_5xx = 0
    network_hard_failure_count = 0
    network_noise_count = 0
    failing_url_counter: Counter[str] = Counter()
    for entry in response_entries:
        status = int(entry.get("status") or 0)
        url = str(entry.get("url") or "")
        is_first_party = _is_first_party_url(url, base_url)
        if 200 <= status < 300 and is_first_party:
            first_party_2xx += 1
        if 400 <= status < 500:
            all_4xx += 1
            if is_first_party:
                first_party_4xx += 1
        if status >= 500:
            all_5xx += 1
            failing_url_counter[url] += 1
            if is_first_party:
                first_party_5xx += 1

    for entry in failed_entries:
        url = str(entry.get("url") or "")
        failure_text = str(entry.get("failure") or "").lower()
        url_lower = url.lower()

        # Classify as noise if failure text or URL matches noise patterns
        is_noise = any(
            pattern in failure_text or pattern in url_lower
            for pattern in noise_patterns
        )
        if is_noise:
            network_noise_count += 1
        else:
            network_hard_failure_count += 1
            failing_url_counter[url] += 1
            if _is_first_party_url(url, base_url):
                first_party_request_failed += 1

    network_summary = {
        "request_count": len(request_entries),
        "response_count": len(response_entries),
        "request_failed_count": len(failed_entries),
        "network_hard_failure_count": network_hard_failure_count,
        "network_noise_count": network_noise_count,
        "status_4xx": all_4xx,
        "status_5xx": all_5xx,
        "first_party_status_2xx_count": first_party_2xx,
        "first_party_status_4xx_count": first_party_4xx,
        "first_party_request_failed_count": first_party_request_failed,
        "first_party_status_5xx_count": first_party_5xx,
        "top_failing_urls": _top_counter(failing_url_counter),
    }

    filtered_console: list[dict] = []
    message_counter: Counter[str] = Counter()
    first_party_error = 0
    first_party_warn = 0
    third_party_error = 0
    third_party_warn = 0
    for entry in console_logs:
        text = str(entry.get("text") or "")
        normalized_text = text.lower()
        if any(pattern in normalized_text for pattern in console_ignore_patterns):
            continue
        filtered_console.append(entry)
        message_counter[text] += 1

        level = str(entry.get("type") or "").lower()
        location = entry.get("location") if isinstance(entry.get("location"), dict) else {}
        location_url = location.get("url") if isinstance(location, dict) else ""
        first_party = _is_first_party_url(location_url, base_url) if location_url else False
        if level == "error":
            if first_party:
                first_party_error += 1
            else:
                third_party_error += 1
        if level in {"warning", "warn"}:
            if first_party:
                first_party_warn += 1
            else:
                third_party_warn += 1

    console_summary = {
        "first_party_error_count": first_party_error,
        "first_party_warn_count": first_party_warn,
        "third_party_error_count": third_party_error,
        "third_party_warn_count": third_party_warn,
        "top_messages": _top_counter(message_counter),
        "filtered_count": len(filtered_console),
    }

    allowlisted_violations = []
    for violation in contract_violations:
        violation_url = str(violation.get("url") or "")
        if _url_matches_allowlist(violation_url, contract_allowlist):
            allowlisted_violations.append(violation)

    contract_summary = {
        "allowlisted_violation_count": len(allowlisted_violations),
        "allowlist_size": len(contract_allowlist),
        "violations": allowlisted_violations[:20],
    }

    cookie_summary = {
        "added_count": len(cookie_added),
        "removed_count": len(cookie_removed),
        "changed_count": len(cookie_changed),
    }

    double_submit_summary = _build_double_submit_summary(
        base_url=base_url,
        network_logs=network_logs,
    )

    return {
        "network_summary": network_summary,
        "console_summary": console_summary,
        "contract_summary": contract_summary,
        "cookie_summary": cookie_summary,
        "double_submit_summary": double_submit_summary,
    }


def classify_failure_from_signals(
    *,
    final_status: str,
    diagnostics_summary: dict,
    step_failure_reasons: list[str],
    step_failure_messages: list[str],
    network_noise_patterns: Optional[list[str]] = None,
) -> tuple[str | None, str | None]:
    if final_status == "passed":
        return None, None

    # --- Priority 1: explicit step failures ---
    joined_failures = " ".join(step_failure_reasons + step_failure_messages).lower()
    if "timeout" in joined_failures:
        return "timeout", "step_timeout"

    if any(reason in RESOLVER_FAILURE_TOKENS for reason in step_failure_reasons):
        return "resolver_failure", "resolver_resolution_failure"

    # Check for non-timeout action failures before network signals
    has_action_failure = any(
        reason not in RESOLVER_FAILURE_TOKENS and reason != "timeout"
        for reason in step_failure_reasons
    )

    # --- Priority 2: contract violations ---
    contract_summary = diagnostics_summary.get("contract_summary", {})
    if int(contract_summary.get("allowlisted_violation_count", 0)) > 0:
        return "contract_violation", "allowlisted_contract_violation"

    # --- Priority 3: hard first-party network failures (excluding noise) ---
    network_summary = diagnostics_summary.get("network_summary", {})
    first_party_failed = int(network_summary.get("first_party_request_failed_count", 0))
    first_party_5xx = int(network_summary.get("first_party_status_5xx_count", 0))

    if (first_party_failed > 0 or first_party_5xx > 0) and not has_action_failure:
        return "network_error", "first_party_network_failure"

    # --- Priority 4: action failure (default for failed runs) ---
    if has_action_failure or step_failure_reasons:
        return "action_failure", "action_execution_failure"

    return "action_failure", "action_execution_failure"


async def generate_and_persist_test_cases(flow_id: str, regenerate: bool = True) -> list[dict]:
    backend = await get_backend()
    flow_repo = FlowRepo(backend)
    project_repo = ProjectRepo(backend)
    test_case_repo = TestCaseRepo(backend)

    flow = await flow_repo.get(flow_id)
    if not flow:
        raise ValueError(f"Flow {flow_id} not found")

    project = await project_repo.get(flow.get("project_id", "")) if flow.get("project_id") else None
    config = _extract_project_config(project)
    baseline_timeout_ms = None
    cfg_timeout = (project or {}).get("test_config_json", {}).get("default_timeout_ms") if isinstance(project, dict) else None
    if isinstance(cfg_timeout, (int, float)) and cfg_timeout > 0:
        baseline_timeout_ms = int(cfg_timeout)

    flow_payload = flow.get("flow_json", {}) if isinstance(flow.get("flow_json"), dict) else {}
    if _flow_is_mobile(flow):
        gs = flow_payload.setdefault("general_settings", {})
        gs["is_mobile"] = True

    generated = generate_test_cases(
        flow_id,
        flow_payload,
        input_mutation_rules=config["input_mutation_rules"],
        do_not_mutate_fields=config["do_not_mutate_fields"],
        baseline_timeout_ms=baseline_timeout_ms,
        mutation_relevance_threshold=config["mutation_relevance_threshold"],
    )
    flow_name = str(flow.get("name", "flow")).strip() or "flow"
    for case in generated:
        variation = str(case.get("variation_type", "baseline")).strip() or "baseline"
        case["name"] = f"{flow_name}__{variation}"

    if not regenerate:
        existing = await test_case_repo.list_by_flow(flow_id)
        if existing:
            return existing

    return await test_case_repo.upsert_many(flow_id, generated)


async def _run_single_test_case(
    *,
    flow_id: str,
    flow_name: str,
    project_id: str,
    flow_json: dict,
    run_id: str,
    headless: bool,
    timeout: int,
    environment_profile: str,
    on_step: Optional[StepCallback],
    diagnostics_policy: str = DEFAULT_DIAGNOSTICS_POLICY,
    timeout_policy: str = DEFAULT_TIMEOUT_POLICY,
    timeout_multipliers: Optional[dict] = None,
    contract_allowlist: Optional[list[str]] = None,
    console_ignore_patterns: Optional[list[str]] = None,
    replay_mode: str = DEFAULT_REPLAY_MODE,
    resolver_fallback_policy: str = DEFAULT_RESOLVER_FALLBACK_POLICY,
    network_noise_patterns: Optional[list[str]] = None,
    session_state: Optional[dict] = None,
) -> dict:
    backend = await get_backend()
    run_repo = TestRunRepo(backend)
    result_repo = TestResultRepo(backend)

    steps = flow_json.get("steps", []) if isinstance(flow_json.get("steps"), list) else []

    step_result_ids: list[str] = []
    for idx, step in enumerate(steps):
        s_id = step.get("step_id", "") if isinstance(step, dict) else ""
        a_type = step.get("action", "") if isinstance(step, dict) else ""
        t_name = ""
        if isinstance(step, dict):
            target = step.get("target")
            if isinstance(target, dict):
                t_name = target.get("friendly_name", "")
        sr = await result_repo.create(
            run_id=run_id,
            step_order=idx,
            step_id=s_id,
            action_type=a_type,
            target_name=t_name,
        )
        step_result_ids.append(sr["id"])

    try:
        resolver_flow = ResolverFlowDef.from_dict(flow_json)
    except Exception as e:
        await run_repo.update_status(
            run_id,
            "failed",
            finished_at=_now_iso(),
            failure_class=classify_failure(str(e)),
            failure_root_cause="flow_parse_failed",
            diagnostics_json={"policy": diagnostics_policy, "summary": {}},
        )
        raise ValueError(f"Failed to parse flow for execution: {e}")

    effective_timeout = _compute_effective_timeout(
        timeout_ms=timeout,
        environment_profile=environment_profile,
        timeout_policy=timeout_policy,
        timeout_multipliers=timeout_multipliers,
    )

    artifacts_dir = Path("artifacts") / "test_runs" / _safe_name(run_id)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # session_state can also be embedded in flow_json under general_settings.auth_session
    _auth_session = session_state or (flow_json.get("general_settings") or {}).get("auth_session")

    config = ExecutorConfig(
        headless=headless,
        timeout=effective_timeout,
        screenshot_on_failure=True,
        environment_profile=environment_profile,
        replay_mode=replay_mode,
        resolver_fallback_policy=resolver_fallback_policy,
        screenshots_dir=str(artifacts_dir),
        session_state=_auth_session,
    )
    executor = Executor(config)

    await run_repo.update_status(run_id, "running", started_at=_now_iso())

    start_time = time.time()
    actions_executed = 0
    actions_passed = 0
    actions_failed = 0

    console_logs: list[dict] = []
    network_logs: list[dict] = []
    contract_violations: list[dict] = []
    step_failure_reasons: list[str] = []
    step_failure_messages: list[str] = []
    step_confidence_values: list[float] = []
    fatal_error_text: str = ""
    request_starts: dict[str, float] = {}
    cookie_before: list[dict] = []
    cookie_after: list[dict] = []
    dom_snapshot_path: Optional[str] = None
    contract_allowlist = list(contract_allowlist or [])
    console_ignore_patterns = list(console_ignore_patterns or [])
    step_timeout_s = max(5.0, (effective_timeout / 1000.0) * 2.0)
    step_time_windows: list[dict] = []

    try:
        await executor.launch()

        # Inject auth session (cookies + storage) before any navigation
        if _auth_session:
            try:
                start_url = resolver_flow.start_url or ""
                await executor.inject_storage_state(start_url)
                print(f"[axiom] Injected auth session (cookies + storage) for {start_url}")
            except Exception as _se:
                print(f"[axiom] Warning: session injection failed: {_se}")

        page = executor._page
        context = executor._context
        attached_pages: set[int] = set()

        def _current_active_page():
            candidate = executor._page
            if candidate and not candidate.is_closed():
                return candidate
            if page and not page.is_closed():
                return page
            if context:
                for ctx_page in reversed(list(context.pages)):
                    if ctx_page and not ctx_page.is_closed():
                        return ctx_page
            return None

        def _on_console(msg):
            level = str(msg.type).lower()
            if level in {"error", "warning"}:
                console_logs.append(
                    {
                        "type": level,
                        "text": msg.text,
                        "location": msg.location,
                        "time": time.time(),
                    }
                )

        def _on_request(req):
            req_key = str(id(req))
            t_now = time.time()
            request_starts[req_key] = t_now
            post_data: Optional[str] = None
            try:
                raw_post_data = getattr(req, "post_data", None)
                if callable(raw_post_data):
                    raw_post_data = raw_post_data()
                if isinstance(raw_post_data, str):
                    post_data = raw_post_data
            except Exception:
                post_data = None
            network_logs.append(
                {
                    "event": "request",
                    "url": req.url,
                    "method": req.method,
                    "resource_type": req.resource_type,
                    "headers": dict(req.headers or {}),
                    "post_data": post_data,
                    "time": t_now,
                }
            )

        async def _check_response_contract(resp):
            req = resp.request
            status = resp.status
            if not _url_matches_allowlist(req.url, contract_allowlist):
                return
            header_ct = (resp.headers or {}).get("content-type", "")
            if status >= 500:
                contract_violations.append(
                    {
                        "url": req.url,
                        "method": req.method,
                        "status": status,
                        "reason": "server_error",
                    }
                )
            if "application/json" in header_ct and status < 400:
                try:
                    body = await resp.json()
                    if not isinstance(body, (dict, list)):
                        contract_violations.append(
                            {
                                "url": req.url,
                                "method": req.method,
                                "status": status,
                                "reason": "json_shape_invalid",
                            }
                        )
                except Exception:
                    contract_violations.append(
                        {
                            "url": req.url,
                            "method": req.method,
                            "status": status,
                            "reason": "json_parse_failed",
                        }
                    )

        async def _on_response(resp, t_arrived: float):
            req = resp.request
            req_key = str(id(req))
            started = request_starts.get(req_key)
            duration_ms = ((t_arrived - started) * 1000.0) if started else None
            network_logs.append(
                {
                    "event": "response",
                    "url": req.url,
                    "method": req.method,
                    "status": resp.status,
                    "duration_ms": duration_ms,
                    "headers": dict(resp.headers or {}),
                    "ok": resp.ok,
                    "time": t_arrived,
                }
            )
            await _check_response_contract(resp)

        def _on_request_failed(req):
            failure_text = "request_failed"
            try:
                failure_info = req.failure
                if isinstance(failure_info, str):
                    failure_text = failure_info
                elif isinstance(failure_info, dict):
                    failure_text = (
                        failure_info.get("errorText")
                        or failure_info.get("error_text")
                        or "request_failed"
                    )
                elif hasattr(failure_info, "error_text"):
                    failure_text = getattr(failure_info, "error_text") or "request_failed"
                elif failure_info:
                    failure_text = str(failure_info)
            except Exception:
                failure_text = "request_failed"
            network_logs.append(
                {
                    "event": "request_failed",
                    "url": req.url,
                    "method": req.method,
                    "failure": failure_text,
                    "time": time.time(),
                }
            )

        def _attach_page_listeners(target_page):
            if not target_page:
                return
            key = id(target_page)
            if key in attached_pages:
                return
            attached_pages.add(key)
            target_page.on("console", _on_console)
            target_page.on("request", _on_request)
            target_page.on("response", lambda resp: asyncio.create_task(_on_response(resp, time.time())))
            target_page.on("requestfailed", _on_request_failed)

        for existing_page in list(context.pages):
            _attach_page_listeners(existing_page)
        context.on("page", _attach_page_listeners)

        cookie_before = await context.cookies()

        await page.goto(
            resolver_flow.start_url,
            wait_until="domcontentloaded",
            timeout=effective_timeout,
        )

        for idx, action in enumerate(resolver_flow.actions):
            if on_step:
                step_data = steps[idx] if idx < len(steps) else {}
                target = step_data.get("target", {}) if isinstance(step_data, dict) else {}
                start_payload = {
                    "type": "step_start",
                    "run_id": run_id,
                    "step_order": idx,
                    "step_id": step_data.get("step_id", "") if isinstance(step_data, dict) else "",
                    "action_type": step_data.get("action", "") if isinstance(step_data, dict) else "",
                    "target_name": target.get("friendly_name", "") if isinstance(target, dict) else "",
                }
                try:
                    await on_step(start_payload)
                except Exception:
                    pass

            step_start = time.time()

            def _suppress_task_exc(t):
                """Retrieve & discard exceptions from orphaned Playwright tasks.

                When asyncio.wait_for cancels a task that is deep inside
                Playwright's own retry loop, Playwright may surface a
                TargetClosedError after the browser is closed.  Without this
                callback Python emits a noisy "Future exception was never
                retrieved" warning.
                """
                if not t.cancelled():
                    try:
                        t.exception()
                    except Exception:
                        pass

            _action_task = asyncio.ensure_future(executor._execute_action(action))
            _action_task.add_done_callback(_suppress_task_exc)
            try:
                action_result = await asyncio.wait_for(
                    asyncio.shield(_action_task),
                    timeout=step_timeout_s,
                )
            except asyncio.TimeoutError:
                _action_task.cancel()
                # Outer timeout means the element was never found / action never
                # completed — this is a genuine failure, not a slow-step warning.
                # success=False so actions_failed is incremented and the
                # expected_outcome inversion can fire correctly for negative-test
                # variants (e.g. input_validation whose post-login steps should
                # time out because the invalid credentials prevented login).
                action_result = ActionResult(
                    action_id=action.id,
                    success=False,
                    failure_reason=FailureReason.TIMEOUT,
                    failure_message=f"Step timed out after {step_timeout_s:.1f}s (element not found or action did not complete)",
                )

            if not action_result.success and action.on_failure == OnFailure.RETRY_ONCE:
                await asyncio.sleep(1.0)
                executor.router._dom_lookup = {}
                _retry_task = asyncio.ensure_future(executor._execute_action(action))
                _retry_task.add_done_callback(_suppress_task_exc)
                try:
                    action_result = await asyncio.wait_for(
                        asyncio.shield(_retry_task),
                        timeout=step_timeout_s,
                    )
                except asyncio.TimeoutError:
                    _retry_task.cancel()
                    action_result = ActionResult(
                        action_id=action.id,
                        success=False,
                        failure_reason=FailureReason.TIMEOUT,
                        failure_message=f"Step timed out after retry ({step_timeout_s:.1f}s)",
                    )

            elapsed_ms = int(round((time.time() - step_start) * 1000))
            actions_executed += 1
            # A step where success=True but failure_reason=TIMEOUT is a slow-step
            # warning — the flow continues but the UI shows the latency issue.
            _is_timeout_warning = (
                action_result.success
                and action_result.failure_reason == FailureReason.TIMEOUT
            )
            # An optional step that failed (e.g. second submit where app correctly
            # disabled the button) is promoted to a warning — flow continues and
            # the outcome does not count toward actions_failed.
            _is_optional_failure = (
                not action_result.success
                and action.on_failure == OnFailure.OPTIONAL
            )
            if _is_timeout_warning or _is_optional_failure:
                step_status = "warning"
            elif action_result.success:
                step_status = "passed"
            else:
                step_status = "failed"

            # Record time window for silent error correlation
            step_data_for_window = steps[idx] if idx < len(steps) else {}
            step_time_windows.append({
                "step_order": idx,
                "step_id": step_data_for_window.get("step_id", "") if isinstance(step_data_for_window, dict) else "",
                "start_time": step_start,
                "end_time": time.time(),
                "passed": action_result.success,
            })

            if action_result.success or _is_optional_failure:
                actions_passed += 1
            else:
                actions_failed += 1
                if action_result.failure_reason:
                    step_failure_reasons.append(action_result.failure_reason.value)
                if action_result.failure_message:
                    step_failure_messages.append(action_result.failure_message)

            update_fields: dict[str, Any] = {"time_taken_ms": elapsed_ms}
            if action_result.resolution:
                if action_result.resolution.selected_candidate:
                    selected_score = action_result.resolution.selected_candidate.score
                    update_fields["confidence"] = selected_score
                    if isinstance(selected_score, (float, int)):
                        step_confidence_values.append(float(selected_score))
                if action_result.resolution.resolver_path:
                    update_fields["resolver_path"] = " → ".join(action_result.resolution.resolver_path)
            if action_result.failure_reason:
                update_fields["failure_reason"] = action_result.failure_reason.value
            if action_result.failure_message:
                update_fields["failure_message"] = action_result.failure_message
            if action_result.screenshot_path:
                update_fields["screenshot_path"] = action_result.screenshot_path
            # Per-step low-quality screenshot (viewport only, ~30KB JPEG).
            # Only taken when the executor hasn't already captured one (failure shots
            # are higher-priority and already stored above).
            if not update_fields.get("screenshot_path"):
                try:
                    _ss_path = str(artifacts_dir / f"step_{idx:03d}.jpg")
                    screenshot_page = _current_active_page()
                    if screenshot_page:
                        await screenshot_page.screenshot(path=_ss_path, type="jpeg", quality=30, full_page=False)
                    else:
                        raise RuntimeError("No active page available for screenshot")
                    update_fields["screenshot_path"] = _ss_path
                except Exception:
                    pass
            # Persist selection_source and attempt_trace per step
            if hasattr(action_result, "selection_source") and action_result.selection_source:
                update_fields["selection_source"] = action_result.selection_source
            if hasattr(action_result, "attempt_trace") and action_result.attempt_trace:
                update_fields["attempt_trace_json"] = action_result.attempt_trace

            if idx < len(step_result_ids):
                await result_repo.update(step_result_ids[idx], step_status, **update_fields)

            if on_step:
                step_data = steps[idx] if idx < len(steps) else {}
                target = step_data.get("target", {}) if isinstance(step_data, dict) else {}
                payload = {
                    "run_id": run_id,
                    "step_order": idx,
                    "step_id": step_data.get("step_id", "") if isinstance(step_data, dict) else "",
                    "target_name": target.get("friendly_name", "") if isinstance(target, dict) else "",
                    "status": step_status,
                    "action_type": action.type.value,
                    "confidence": update_fields.get("confidence"),
                    "time_taken_ms": elapsed_ms,
                    "failure_reason": update_fields.get("failure_reason"),
                    "failure_message": update_fields.get("failure_message"),
                    "actions_executed": actions_executed,
                    "actions_passed": actions_passed,
                    "actions_failed": actions_failed,
                }
                try:
                    await on_step(payload)
                except Exception:
                    pass

            if not action_result.success and action.on_failure in (OnFailure.ABORT, OnFailure.RETRY_ONCE):
                break

        cookie_after = await context.cookies()

        if actions_failed > 0:
            dom_snapshot_path = str(artifacts_dir / "failure_dom.html")
            try:
                dom_page = _current_active_page()
                if not dom_page:
                    raise RuntimeError("No active page available for DOM snapshot")
                dom_content = await dom_page.content()
                Path(dom_snapshot_path).write_text(dom_content, encoding="utf-8")
            except Exception:
                dom_snapshot_path = None

    except Exception as e:
        print(f"Test execution error: {e}")
        actions_failed = max(actions_failed, 1)
        fatal_error_text = str(e)
    finally:
        # Flush any pending network response tasks before closing so that
        # responses triggered by the last few actions are captured.
        for _ in range(5):
            await asyncio.sleep(0)
        await executor.close()

    total_ms = int(round((time.time() - start_time) * 1000))
    final_status = "passed" if actions_failed == 0 and actions_executed > 0 else "failed"
    total_steps = actions_executed
    passed_steps = actions_passed
    confidence_score: Optional[float] = None
    if step_confidence_values:
        confidence_score = round((sum(step_confidence_values) / len(step_confidence_values)) * 100.0, 2)
    elif total_steps > 0:
        confidence_score = round((passed_steps / total_steps) * 100.0, 2)

    cookie_before_map = {f"{c.get('name')}@{c.get('domain')}{c.get('path')}": c for c in cookie_before}
    cookie_after_map = {f"{c.get('name')}@{c.get('domain')}{c.get('path')}": c for c in cookie_after}
    cookie_added = [cookie_after_map[k] for k in sorted(set(cookie_after_map) - set(cookie_before_map))]
    cookie_removed = [cookie_before_map[k] for k in sorted(set(cookie_before_map) - set(cookie_after_map))]
    cookie_changed = [
        {"before": cookie_before_map[k], "after": cookie_after_map[k]}
        for k in sorted(set(cookie_before_map).intersection(cookie_after_map))
        if cookie_before_map[k].get("value") != cookie_after_map[k].get("value")
    ]

    network_log_path = artifacts_dir / "network_logs.json"
    console_log_path = artifacts_dir / "console_logs.json"
    cookie_diff_path = artifacts_dir / "cookie_diff.json"
    contract_path = artifacts_dir / "contract_violations.json"

    network_log_path.write_text(json.dumps(network_logs, indent=2), encoding="utf-8")
    console_log_path.write_text(json.dumps(console_logs, indent=2), encoding="utf-8")
    cookie_diff_path.write_text(
        json.dumps({"added": cookie_added, "removed": cookie_removed, "changed": cookie_changed}, indent=2),
        encoding="utf-8",
    )
    contract_path.write_text(json.dumps(contract_violations, indent=2), encoding="utf-8")
    diagnostics_summary = _summarize_diagnostics(
        base_url=resolver_flow.start_url,
        network_logs=network_logs,
        console_logs=console_logs,
        contract_violations=contract_violations,
        cookie_added=cookie_added,
        cookie_removed=cookie_removed,
        cookie_changed=cookie_changed,
        contract_allowlist=contract_allowlist,
        console_ignore_patterns=console_ignore_patterns,
        network_noise_patterns=network_noise_patterns,
    )

    if fatal_error_text:
        step_failure_messages.append(fatal_error_text)

    if diagnostics_policy == "signal_gated":
        failure_class, failure_root_cause = classify_failure_from_signals(
            final_status=final_status,
            diagnostics_summary=diagnostics_summary,
            step_failure_reasons=step_failure_reasons,
            step_failure_messages=step_failure_messages,
            network_noise_patterns=network_noise_patterns,
        )
    else:
        failure_class = classify_failure(fatal_error_text or ("action_failure" if final_status == "failed" else None))
        failure_root_cause = "legacy_classification" if failure_class else None

    # Build secondary signals for diagnostic context
    failure_secondary_signals = {}
    if final_status == "failed":
        network_sum = diagnostics_summary.get("network_summary", {})
        console_sum = diagnostics_summary.get("console_summary", {})
        failure_secondary_signals = {
            "step_failure_reasons": step_failure_reasons,
            "step_failure_messages": step_failure_messages[:10],  # cap for storage
            "network_hard_failure_count": network_sum.get("network_hard_failure_count", 0),
            "network_noise_count": network_sum.get("network_noise_count", 0),
            "first_party_5xx_count": network_sum.get("first_party_status_5xx_count", 0),
            "console_first_party_errors": console_sum.get("first_party_error_count", 0),
            "contract_violation_count": diagnostics_summary.get("contract_summary", {}).get(
                "allowlisted_violation_count", 0
            ),
        }

    artifacts_json = {
        "network_logs": str(network_log_path),
        "console_logs": str(console_log_path),
        "cookie_diff": str(cookie_diff_path),
        "contract_violations": str(contract_path),
        "dom_snapshot": dom_snapshot_path,
    }
    diagnostics_json = {
        "policy": diagnostics_policy,
        "summary": diagnostics_summary,
    }

    # ── Silent Error Detection ──
    # Cross-join passed steps with network/console errors in the same window.
    silent_errors = _detect_silent_errors(
        step_time_windows=step_time_windows,
        network_logs=network_logs,
        console_logs=console_logs,
        base_url=resolver_flow.start_url,
        network_noise_patterns=network_noise_patterns,
    )
    if silent_errors:
        diagnostics_json["silent_errors"] = silent_errors
        diagnostics_json["silent_error_count"] = len(silent_errors)
        # Persist to artifact file too
        silent_err_path = artifacts_dir / "silent_errors.json"
        silent_err_path.write_text(json.dumps(silent_errors, indent=2), encoding="utf-8")
        artifacts_json["silent_errors"] = str(silent_err_path)

    await run_repo.update_status(
        run_id,
        final_status,
        finished_at=_now_iso(),
        actions_executed=actions_executed,
        actions_passed=actions_passed,
        actions_failed=actions_failed,
        total_steps=total_steps,
        passed_steps=passed_steps,
        confidence_score=confidence_score,
        total_time_ms=total_ms,
        failure_class=failure_class,
        failure_root_cause=failure_root_cause,
        blocked_reason=None,
        artifacts_json=artifacts_json,
        diagnostics_json=diagnostics_json,
        failure_secondary_signals_json=failure_secondary_signals,
    )

    return await run_repo.get(run_id)


async def run_test_group(
    flow_id: Optional[str] = None,
    *,
    flow_selections: Optional[list[dict]] = None,
    run_group_id: Optional[str] = None,
    test_case_ids: Optional[list[str]] = None,
    headless: bool = True,
    timeout: int = 10000,
    force_run_variations: bool = False,
    diagnostics_policy: Optional[str] = None,
    timeout_policy: Optional[str] = None,
    on_step: Optional[StepCallback] = None,
    session_state: Optional[dict] = None,
) -> dict:
    """Execute selected test-cases across one or more flows as a grouped run."""
    backend = await get_backend()
    flow_repo = FlowRepo(backend)
    project_repo = ProjectRepo(backend)
    run_group_repo = RunGroupRepo(backend)
    test_case_repo = TestCaseRepo(backend)
    run_repo = TestRunRepo(backend)
    result_repo = TestResultRepo(backend)

    normalized_selections = flow_selections or ([{"flow_id": flow_id, "test_case_ids": test_case_ids}] if flow_id else [])
    normalized_selections = [selection for selection in normalized_selections if selection.get("flow_id")]
    if not normalized_selections:
        raise ValueError("No flows selected")

    execution_plan: list[dict] = []
    for selection in normalized_selections:
        selected_flow_id = selection["flow_id"]
        flow = await flow_repo.get(selected_flow_id)
        if not flow:
            raise ValueError(f"Flow {selected_flow_id} not found")
        flow_is_mobile = _flow_is_mobile(flow)

        project = await project_repo.get(flow.get("project_id", "")) if flow.get("project_id") else None
        project_config = _extract_project_config(project)
        resolved_diagnostics_policy = (
            (diagnostics_policy or project_config["diagnostics_policy"] or DEFAULT_DIAGNOSTICS_POLICY)
            .strip()
            .lower()
        )
        resolved_timeout_policy = (
            (timeout_policy or project_config["timeout_policy"] or DEFAULT_TIMEOUT_POLICY)
            .strip()
            .lower()
        )
        timeout_multipliers = dict(project_config["timeout_multipliers"])
        contract_allowlist = list(project_config["contract_allowlist"])
        console_ignore_patterns = list(project_config["console_ignore_patterns"])
        resolved_replay_mode = str(project_config.get("replay_mode") or DEFAULT_REPLAY_MODE).strip().lower()
        resolved_resolver_policy = str(
            project_config.get("resolver_fallback_policy") or DEFAULT_RESOLVER_FALLBACK_POLICY
        ).strip().lower()
        network_noise_patterns = list(project_config.get("network_noise_patterns", DEFAULT_NETWORK_NOISE_PATTERNS))

        all_cases = await test_case_repo.list_by_flow(selected_flow_id)
        if not all_cases:
            all_cases = await generate_and_persist_test_cases(selected_flow_id, regenerate=True)

        selected = [tc for tc in all_cases if tc.get("active")]
        selection_test_case_ids = selection.get("test_case_ids") or []
        if selection_test_case_ids:
            selected_ids = set(selection_test_case_ids)
            selected = [tc for tc in all_cases if tc["id"] in selected_ids]

        if flow_is_mobile:
            selected = [tc for tc in selected if str(tc.get("environment_profile") or "").lower() == "mobile"]

        variation_mode = project_config.get("variation_mode", DEFAULT_VARIATION_MODE)
        if variation_mode == "compat_only" and not selection_test_case_ids:
            selected = [
                tc for tc in selected
                if tc.get("variation_type", "baseline") in COMPAT_SAFE_VARIATION_TYPES
            ]

        if not selected:
            if flow_is_mobile:
                raise ValueError(f"No mobile test cases available for mobile flow {flow.get('name') or selected_flow_id}")
            raise ValueError(f"No active test cases to execute for flow {flow.get('name') or selected_flow_id}")

        baseline_case = next((c for c in selected if c.get("is_baseline")), None)
        ordered_selected: list[dict] = []
        if baseline_case:
            ordered_selected.append(baseline_case)
        ordered_selected.extend(
            tc for tc in selected if not baseline_case or tc["id"] != baseline_case["id"]
        )

        execution_plan.append(
            {
                "flow": flow,
                "project": project,
                "ordered_selected": ordered_selected,
                "diagnostics_policy": resolved_diagnostics_policy,
                "timeout_policy": resolved_timeout_policy,
                "timeout_multipliers": timeout_multipliers,
                "contract_allowlist": contract_allowlist,
                "console_ignore_patterns": console_ignore_patterns,
                "replay_mode": resolved_replay_mode,
                "resolver_policy": resolved_resolver_policy,
                "network_noise_patterns": network_noise_patterns,
                "flow_is_mobile": flow_is_mobile,
            }
        )

    total_selected_cases = sum(len(plan["ordered_selected"]) for plan in execution_plan)
    if total_selected_cases == 0:
        raise ValueError("No active test cases to execute")

    primary_flow = execution_plan[0]["flow"]
    primary_project = execution_plan[0]["project"]

    if run_group_id:
        run_group = await run_group_repo.get(run_group_id)
        if not run_group:
            raise ValueError(f"Run group {run_group_id} not found")
    else:
        run_group = await run_group_repo.create(
            flow_id=primary_flow["id"],
            project_id=primary_flow.get("project_id", ""),
            config={
                "headless": headless,
                "timeout": timeout,
                "test_case_count": total_selected_cases,
                "force_run_variations": force_run_variations,
                "diagnostics_policy": diagnostics_policy,
                "timeout_policy": timeout_policy,
                "project_name": primary_project.get("name", "") if primary_project else "",
                "project_url": primary_project.get("url", "") if primary_project else "",
                "selected_flows": [
                    {
                        "flow_id": plan["flow"]["id"],
                        "flow_name": plan["flow"].get("name", ""),
                        "test_case_ids": [case["id"] for case in plan["ordered_selected"]],
                    }
                    for plan in execution_plan
                ],
            },
        )
        run_group_id = run_group["id"]

    await run_group_repo.update_status(
        run_group_id,
        "running",
        started_at=_now_iso(),
        total_runs=total_selected_cases,
    )

    start_group_time = time.time()
    passed = 0
    failed = 0
    blocked = 0
    child_run_ids: list[str] = []
    baseline_status_by_flow: dict[str, Optional[str]] = {}

    for plan in execution_plan:
        flow = plan["flow"]
        project = plan["project"]
        ordered_selected = plan["ordered_selected"]
        resolved_diagnostics_policy = plan["diagnostics_policy"]
        resolved_timeout_policy = plan["timeout_policy"]
        timeout_multipliers = plan["timeout_multipliers"]
        contract_allowlist = plan["contract_allowlist"]
        console_ignore_patterns = plan["console_ignore_patterns"]
        resolved_replay_mode = plan["replay_mode"]
        resolved_resolver_policy = plan["resolver_policy"]
        network_noise_patterns = plan["network_noise_patterns"]
        flow_is_mobile = bool(plan.get("flow_is_mobile", False))
        baseline_case = next((c for c in ordered_selected if c.get("is_baseline")), None)
        baseline_status: Optional[str] = None

        for test_case in ordered_selected:
            flow_payload = test_case.get("definition_json", {})
            step_count = len(flow_payload.get("steps", [])) if isinstance(flow_payload, dict) else 0
            run = await run_repo.create(
                flow_id=flow["id"],
                flow_name=flow.get("name", ""),
                project_id=flow.get("project_id", ""),
                config={
                    "headless": headless,
                    "timeout": timeout,
                    "diagnostics_policy": resolved_diagnostics_policy,
                    "timeout_policy": resolved_timeout_policy,
                    "project_name": project.get("name", "") if project else "",
                    "base_url": flow.get("base_url") or (project.get("url", "") if project else ""),
                    "expected_step_count": step_count,
                },
                run_group_id=run_group_id,
                test_case_id=test_case["id"],
                variation_type=test_case.get("variation_type", "baseline"),
                environment_profile="mobile" if flow_is_mobile else test_case.get("environment_profile", "normal"),
                is_baseline=bool(test_case.get("is_baseline", False)),
            )
            child_run_ids.append(run["id"])

            should_block = (
                baseline_case is not None
                and baseline_status == "failed"
                and not force_run_variations
                and not bool(test_case.get("is_baseline", False))
            )
            if should_block:
                await run_repo.update_status(
                    run["id"],
                    "blocked",
                    finished_at=_now_iso(),
                    failure_class=None,
                    failure_root_cause="blocked_by_baseline",
                    blocked_reason="baseline_failed",
                    diagnostics_json={"policy": resolved_diagnostics_policy, "summary": {}, "blocked": True},
                )
                blocked += 1
                continue

            async def _scoped_on_step(
                payload: dict,
                tc: dict = test_case,
                current_flow: dict = flow,
                current_step_count: int = step_count,
            ):
                if not on_step:
                    return
                enriched = dict(payload)
                enriched["run_group_id"] = run_group_id
                enriched["flow_id"] = current_flow["id"]
                enriched["flow_name"] = current_flow.get("name", "")
                enriched["project_id"] = current_flow.get("project_id", "")
                enriched["test_case_id"] = tc["id"]
                enriched["test_case_name"] = tc.get("name")
                enriched["variation_type"] = tc.get("variation_type")
                enriched["environment_profile"] = "mobile" if flow_is_mobile else tc.get("environment_profile")
                enriched["test_case_step_count"] = current_step_count
                await on_step(enriched)

            effective_timeout = _compute_effective_timeout(
                timeout_ms=timeout,
                environment_profile="mobile" if flow_is_mobile else test_case.get("environment_profile", "normal"),
                timeout_policy=resolved_timeout_policy,
                timeout_multipliers=timeout_multipliers,
            )
            run_timeout_seconds = _run_level_timeout_seconds(step_count, effective_timeout)
            try:
                result = await asyncio.wait_for(
                    _run_with_worker_slot(_run_single_test_case(
                        flow_id=flow["id"],
                        flow_name=flow.get("name", ""),
                        project_id=flow.get("project_id", ""),
                        flow_json=flow_payload,
                        run_id=run["id"],
                        headless=headless,
                        timeout=timeout,
                        environment_profile="mobile" if flow_is_mobile else test_case.get("environment_profile", "normal"),
                        on_step=_scoped_on_step,
                        diagnostics_policy=resolved_diagnostics_policy,
                        timeout_policy=resolved_timeout_policy,
                        timeout_multipliers=timeout_multipliers,
                        contract_allowlist=contract_allowlist,
                        console_ignore_patterns=console_ignore_patterns,
                        replay_mode=resolved_replay_mode,
                        resolver_fallback_policy=resolved_resolver_policy,
                        network_noise_patterns=network_noise_patterns,
                        session_state=session_state,
                    )),
                    timeout=run_timeout_seconds,
                )
            except asyncio.TimeoutError:
                await run_repo.update_status(
                    run["id"],
                    "failed",
                    finished_at=_now_iso(),
                    total_time_ms=run_timeout_seconds * 1000,
                    failure_class="timeout",
                    failure_root_cause="run_timeout",
                    diagnostics_json={"policy": resolved_diagnostics_policy, "summary": {}},
                )
                result = await run_repo.get(run["id"])
            except Exception as exc:
                await run_repo.update_status(
                    run["id"],
                    "failed",
                    finished_at=_now_iso(),
                    failure_class=classify_failure(str(exc)),
                    failure_root_cause="run_unhandled_exception",
                    diagnostics_json={"policy": resolved_diagnostics_policy, "summary": {}},
                )
                result = await run_repo.get(run["id"])

            status = result.get("status") if result else "failed"

            variation_type = test_case.get("variation_type", "baseline")
            expected_outcome = (
                _EXPECTED_OUTCOME_BY_TYPE.get(variation_type)
                or (test_case.get("expected_outcome") or "").strip()
                or "pass"
            )
            applicability_meta = test_case.get("applicability_meta_json") if isinstance(test_case, dict) else {}
            if not isinstance(applicability_meta, dict):
                applicability_meta = {}

            assertion_plan = applicability_meta.get("planned_assertions")
            if not isinstance(assertion_plan, list) or len(assertion_plan) == 0:
                intent = intent_for_variation(variation_type)
                assertion_plan = planned_assertions(intent.intent_id)

            step_rows = await result_repo.list_by_run(run["id"])
            mutation_efficacy = _compute_mutation_efficacy(
                applicability_meta=applicability_meta,
                step_rows=step_rows,
                run_status=status,
            )
            mutation_meaningful = bool(mutation_efficacy.get("meaningful"))
            assertion_results = evaluate_assertion_set(assertion_plan, result or {}, step_rows)
            semantic_decision = decide_semantic_verdict(
                expected_outcome=expected_outcome,
                mutation_meaningful=mutation_meaningful,
                assertion_results=assertion_results,
                fallback_status=status,
            )
            semantic_verdict = semantic_decision.get("verdict", "pass")

            if expected_outcome == "fail" and status in ("passed", "failed"):
                if semantic_verdict == "pass" and status == "failed":
                    await run_repo.update_status(
                        run["id"],
                        "passed",
                        failure_class=None,
                        failure_root_cause="expected_outcome_inversion",
                    )
                    status = "passed"
                elif semantic_verdict == "fail" and status == "passed":
                    await run_repo.update_status(
                        run["id"],
                        "failed",
                        failure_class="expected_failure_not_triggered",
                        failure_root_cause="expected_outcome_inversion",
                    )
                    status = "failed"

            latest_run = await run_repo.get(run["id"])
            diagnostics_json = latest_run.get("diagnostics_json", {}) if isinstance(latest_run, dict) else {}
            if not isinstance(diagnostics_json, dict):
                diagnostics_json = {}
            diagnostics_json["semantic_assertions"] = {
                "verdict": semantic_verdict,
                "reason": semantic_decision.get("reason"),
                "expected_outcome": expected_outcome,
                "mutation_meaningful": mutation_meaningful,
                "mutation_efficacy": mutation_efficacy,
                "assertion_results": assertion_results,
                "intent_id": applicability_meta.get("semantic_intent_id") or intent_for_variation(variation_type).intent_id,
            }
            await run_repo.update_status(
                run["id"],
                status,
                diagnostics_json=diagnostics_json,
            )

            if status == "passed":
                passed += 1
            elif status == "blocked":
                blocked += 1
            else:
                failed += 1

            if baseline_case and test_case["id"] == baseline_case["id"] and result:
                baseline_status = status

        baseline_status_by_flow[flow["id"]] = baseline_status

    finished_status = "passed" if failed == 0 and blocked == 0 else "failed"
    total_ms = int(round((time.time() - start_group_time) * 1000.0))

    await run_group_repo.update_status(
        run_group_id,
        finished_status,
        finished_at=_now_iso(),
        runs_passed=passed,
        runs_failed=failed + blocked,
        total_time_ms=total_ms,
    )

    runs = await run_repo.list_by_run_group(run_group_id)
    for run in runs:
        baseline_status = baseline_status_by_flow.get(run.get("flow_id"))
        if run.get("is_baseline"):
            run["failure_origin"] = "baseline"
        elif run.get("status") == "blocked":
            run["failure_origin"] = "blocked_by_baseline"
        else:
            run["failure_origin"] = "variation_induced" if baseline_status == "passed" else "baseline_degraded"

    return {
        "run_group": await run_group_repo.get(run_group_id),
        "runs": runs,
        "primary_run_id": child_run_ids[0] if child_run_ids else None,
    }


async def run_test(
    flow_id: str,
    *,
    run_id: Optional[str] = None,
    headless: bool = True,
    timeout: int = 10000,
    diagnostics_policy: Optional[str] = None,
    timeout_policy: Optional[str] = None,
    on_step: Optional[StepCallback] = None,
    session_state: Optional[dict] = None,
) -> dict:
    """Backward-compatible single run API preserved for existing callers."""
    backend = await get_backend()
    flow_repo = FlowRepo(backend)
    project_repo = ProjectRepo(backend)
    run_repo = TestRunRepo(backend)

    flow = await flow_repo.get(flow_id)
    if not flow:
        raise ValueError(f"Flow {flow_id} not found")
    flow_is_mobile = _flow_is_mobile(flow)

    project = await project_repo.get(flow.get("project_id", "")) if flow.get("project_id") else None
    project_config = _extract_project_config(project)
    resolved_diagnostics_policy = (
        (diagnostics_policy or project_config["diagnostics_policy"] or DEFAULT_DIAGNOSTICS_POLICY)
        .strip()
        .lower()
    )
    resolved_timeout_policy = (
        (timeout_policy or project_config["timeout_policy"] or DEFAULT_TIMEOUT_POLICY)
        .strip()
        .lower()
    )

    if run_id:
        run = await run_repo.get(run_id)
        if not run:
            raise ValueError(f"Test run {run_id} not found")
    else:
        run = await run_repo.create(
            flow_id=flow_id,
            flow_name=flow.get("name", ""),
            project_id=flow.get("project_id", ""),
            config={
                "headless": headless,
                "timeout": timeout,
                "diagnostics_policy": resolved_diagnostics_policy,
                "timeout_policy": resolved_timeout_policy,
            },
            run_group_id=None,
            test_case_id=None,
            variation_type="baseline",
            environment_profile="mobile" if flow_is_mobile else "normal",
            is_baseline=True,
        )

    return await _run_with_worker_slot(_run_single_test_case(
        flow_id=flow_id,
        flow_name=flow.get("name", ""),
        project_id=flow.get("project_id", ""),
        flow_json=flow.get("flow_json", {}),
        run_id=run["id"],
        headless=headless,
        timeout=timeout,
        environment_profile="mobile" if flow_is_mobile else "normal",
        on_step=on_step,
        diagnostics_policy=resolved_diagnostics_policy,
        timeout_policy=resolved_timeout_policy,
        timeout_multipliers=project_config["timeout_multipliers"],
        contract_allowlist=project_config["contract_allowlist"],
        console_ignore_patterns=project_config["console_ignore_patterns"],
        replay_mode=str(project_config.get("replay_mode") or DEFAULT_REPLAY_MODE).strip().lower(),
        resolver_fallback_policy=str(
            project_config.get("resolver_fallback_policy") or DEFAULT_RESOLVER_FALLBACK_POLICY
        ).strip().lower(),
        network_noise_patterns=list(
            project_config.get("network_noise_patterns", DEFAULT_NETWORK_NOISE_PATTERNS)
        ),
        session_state=session_state,
    ))
