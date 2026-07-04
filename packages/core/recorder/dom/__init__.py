"""
DOM Module for Axiome Recording Engine.

Provides full DOM tree snapshot capture and diff computation.
"""

from .dom_snapshot_builder import DOMSnapshotBuilder
from .dom_diff_engine import DOMDiffEngine

__all__ = [
    "DOMSnapshotBuilder",
    "DOMDiffEngine",
]
