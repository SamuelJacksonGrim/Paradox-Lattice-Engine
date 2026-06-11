"""Paradox memory — append-only, permanent cognitive history.

Memory is not a log; it is structured cognitive history. Nothing stored here
may ever be deleted, overwritten, or altered (memory_contract.md §9).
"""

from __future__ import annotations

from ple.errors import ContractViolation
from ple.models.finding import Finding
from ple.models.memory import ParadoxMemoryEpisode, TensionSignature
from ple.models.paradox import ParadoxNode, ParadoxState
from ple.models.synthesis import SynthesisRecord
from ple.models.tension_field import TensionField

ACTOR = "memory"


class ParadoxMemoryBuffer:
    def __init__(self) -> None:
        self._episodes: list[ParadoxMemoryEpisode] = []
        self._snapshots: dict[str, dict] = {}
        self._signatures: dict[str, TensionSignature] = {}
        self._synthesis_history: list[SynthesisRecord] = []
        self._findings: dict[str, Finding] = {}
        self._paradoxes: dict[str, ParadoxNode] = {}

    # -- paradox tracking --------------------------------------------------
    def track_paradox(self, node: ParadoxNode) -> None:
        existing = self._paradoxes.get(node.paradox_id)
        if existing is not None and existing is not node:
            raise ContractViolation("memory objects must not be overwritten")
        self._paradoxes[node.paradox_id] = node

    def get_active_paradoxes(self) -> list[ParadoxNode]:
        return [
            p
            for p in self._paradoxes.values()
            if p.state in (ParadoxState.ACTIVE, ParadoxState.ATTENUATED)
            and p.state != ParadoxState.ARCHIVED
        ]

    def get_paradox(self, paradox_id: str) -> ParadoxNode | None:
        return self._paradoxes.get(paradox_id)

    def archive_paradox(self, node: ParadoxNode) -> None:
        """Only memory may archive. Archived paradoxes remain queryable forever."""
        node.transition(ParadoxState.ARCHIVED, actor=ACTOR)

    # -- episodes ----------------------------------------------------------
    def store_episode(
        self,
        paradox_ids: list[str],
        field: TensionField,
        lattice_snapshot: dict,
        synthesis_records: list[SynthesisRecord],
        attractor_ids: list[str] = (),
        finding_ids: list[str] = (),
        resolution_state: str = "unresolved",
        context: dict | None = None,
    ) -> ParadoxMemoryEpisode:
        snapshot_id = lattice_snapshot["snapshot_id"]
        self._snapshots[snapshot_id] = lattice_snapshot

        signature = self._compress_signature(field)
        self._signatures[signature.signature_id] = signature

        for record in synthesis_records:
            self._synthesis_history.append(record)

        episode = ParadoxMemoryEpisode(
            paradox_ids=tuple(paradox_ids),
            tension_signature=signature,
            lattice_snapshot_id=snapshot_id,
            synthesis_ids=tuple(r.synthesis_id for r in synthesis_records),
            attractor_ids=tuple(attractor_ids),
            finding_ids=tuple(finding_ids),
            resolution_state=resolution_state,
            context_window=dict(context or {}),
            lineage=tuple(paradox_ids),
        )
        self._episodes.append(episode)
        return episode

    def _compress_signature(self, field: TensionField) -> TensionSignature:
        """Compression preserves paradox density, tension distribution,
        coherence profile, and void ratio (memory_contract.md §4)."""
        total_regions = len(field.regions) + len(field.void_zones)
        return TensionSignature(
            paradox_density=len(field.paradox_ids) / max(1, len(field.regions)),
            tension_distribution={
                r.region_id: r.tension_density for r in field.regions
            },
            coherence_profile=dict(field.coherence_map),
            void_ratio=len(field.void_zones) / max(1, total_regions),
        )

    # -- findings ----------------------------------------------------------
    def store_finding(self, finding: Finding) -> None:
        if finding.finding_id in self._findings:
            raise ContractViolation("findings must never be overwritten")
        self._findings[finding.finding_id] = finding

    def findings_by_paradox(self, paradox_id: str) -> list[Finding]:
        return [
            f
            for f in self._findings.values()
            if paradox_id in f.source_paradoxes
        ]

    def findings_by_attractor(self, attractor_id: str) -> list[Finding]:
        return [
            f for f in self._findings.values() if f.attractor_id == attractor_id
        ]

    # -- read-only views ---------------------------------------------------
    @property
    def episodes(self) -> tuple[ParadoxMemoryEpisode, ...]:
        return tuple(self._episodes)

    @property
    def findings(self) -> tuple[Finding, ...]:
        return tuple(self._findings.values())

    @property
    def synthesis_history(self) -> tuple[SynthesisRecord, ...]:
        return tuple(self._synthesis_history)

    def get_snapshot(self, snapshot_id: str) -> dict | None:
        return self._snapshots.get(snapshot_id)

    def episodes_by_paradox(self, paradox_id: str) -> list[ParadoxMemoryEpisode]:
        return [e for e in self._episodes if paradox_id in e.paradox_ids]
