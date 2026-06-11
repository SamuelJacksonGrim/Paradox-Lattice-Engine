"""Paradox Lattice Engine (PLE).

A machine that turns contradictions into usable cognitive structure.

>>> from ple import ParadoxLatticeEngine
>>> engine = ParadoxLatticeEngine()
>>> result = engine.process(
...     {"name": "wave", "claims": {"light_is": "a wave"}},
...     {"name": "particle", "claims": {"light_is": "a particle"}},
... )
>>> result.triggered
True
"""

from ple.core.paradox_pipeline import ParadoxLatticeEngine, PipelineResult
from ple.errors import ContractViolation

__version__ = "0.1.0"

__all__ = ["ContractViolation", "ParadoxLatticeEngine", "PipelineResult"]
