"""
Resolver Pipeline for Deterministic Element Resolution.

Each resolver answers a specific question:
- SemanticResolver: "Does this element mean what the user intended?"
- ContextResolver: "Is this element in the right place?"
- SelectorResolver: "Can we identify this element by what it is?"
- AffordanceResolver: "Can this element perform this action?"
- IndexResolver: "Is this element identified by its position?"
"""

from .base import BaseResolver
from .semantic import SemanticResolver
from .context import ContextResolver
from .selector import SelectorResolver
from .affordance import AffordanceResolver
from .index import IndexResolver

__all__ = [
    "BaseResolver",
    "SemanticResolver",
    "ContextResolver",
    "SelectorResolver",
    "AffordanceResolver",
    "IndexResolver",
]
