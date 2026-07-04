"""Execution environment profiles for generated test-cases."""

from __future__ import annotations


ENV_NORMAL = "normal"
ENV_MOBILE = "mobile"
ENV_3G = "3g"


def profile_for_environment(name: str) -> dict:
    env = (name or ENV_NORMAL).lower()
    if env == ENV_MOBILE:
        return {
            "name": ENV_MOBILE,
            "viewport": {"width": 375, "height": 812},
        }
    if env == ENV_3G:
        return {
            "name": ENV_3G,
            "network": {
                "offline": False,
                "latency": 300,
                "downloadThroughput": 75000,
                "uploadThroughput": 25000,
            },
        }
    return {"name": ENV_NORMAL}
