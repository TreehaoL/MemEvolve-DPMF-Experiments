import copy
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from EvolveLab.memory_types import MemoryRequest, MemoryStatus
from EvolveLab.providers.lightweight_memory_provider import (
    LightweightMemoryProvider,
)


# ============================================================
# Common result schema
# ============================================================


@dataclass
class DefenseExecutionResult:
    operator: str
    activated: bool
    input_count: int = 0
    output_count: int = 0
    removed_or_blocked_ids: List[str] = field(
        default_factory=list
    )
    execution_ms: float = 0.0
    details: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseDefenseOperator:
    defense_id = "UNKNOWN"
    defense_name = "unknown"

    def describe(self) -> Dict[str, Any]:
        return {
            "defense_id": self.defense_id,
            "defense_name": self.defense_name,
        }


# ============================================================
# F0: No defense / passthrough
# ============================================================


class F0Operator(BaseDefenseOperator):
    """
    F0: No defense.

    Used as the stable-state baseline or when DPMF decides that
    no additional defense needs to be activated.
    """

    defense_id = "F0"
    defense_name = "no_defense_passthrough"

    @staticmethod
    def _count_memories(
        memory_path: Path,
    ) -> int:
        with memory_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        return (
            len(data.get("strategic", []))
            + len(data.get("operational", []))
        )

    def execute(
        self,
        memory_path: Path | str,
    ) -> DefenseExecutionResult:
        start = time.perf_counter()

        memory_path = Path(memory_path)

        count = self._count_memories(
            memory_path
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return DefenseExecutionResult(
            operator=self.defense_id,
            activated=False,
            input_count=count,
            output_count=count,
            execution_ms=round(elapsed, 4),
            details={
                "defense_name": self.defense_name,
                "memory_path": str(memory_path),
                "action": "passthrough",
            },
        )


# ============================================================
# F1: Static history-statistics anomaly filter
# ============================================================


class F1Operator(BaseDefenseOperator):
    """
    F1: Static history-statistics anomaly filter.

    Week4 rule:
        usage_count >= 10
        AND
        success_rate >= 0.95

    Memories satisfying both conditions are treated as
    suspicious and removed before retrieval.
    """

    defense_id = "F1"
    defense_name = (
        "static_history_statistics_filter"
    )

    def __init__(
        self,
        usage_threshold: int = 10,
        success_rate_threshold: float = 0.95,
    ):
        self.usage_threshold = (
            usage_threshold
        )
        self.success_rate_threshold = (
            success_rate_threshold
        )

    def is_suspicious(
        self,
        memory: Dict[str, Any],
    ) -> tuple[bool, float]:
        usage_count = memory.get(
            "usage_count",
            0,
        )

        success_count = memory.get(
            "success_count",
            0,
        )

        if usage_count <= 0:
            success_rate = 0.0
        else:
            success_rate = (
                success_count
                / usage_count
            )

        suspicious = (
            usage_count
            >= self.usage_threshold
            and success_rate
            >= self.success_rate_threshold
        )

        return suspicious, success_rate

    @staticmethod
    def _memory_id(
        memory: Dict[str, Any],
        memory_type: str,
        index: int,
    ) -> str:
        explicit_id = memory.get("id")

        if explicit_id:
            return str(explicit_id)

        return f"{memory_type}_{index}"

    def filter_data(
        self,
        memory_data: Dict[str, Any],
    ) -> tuple[
        Dict[str, Any],
        List[Dict[str, Any]],
    ]:
        filtered_data = copy.deepcopy(
            memory_data
        )

        removed = []

        for memory_type in (
            "strategic",
            "operational",
        ):
            kept = []

            memories = memory_data.get(
                memory_type,
                [],
            )

            for index, memory in enumerate(
                memories
            ):
                (
                    suspicious,
                    success_rate,
                ) = self.is_suspicious(
                    memory
                )

                if suspicious:
                    removed.append(
                        {
                            "id": self._memory_id(
                                memory,
                                memory_type,
                                index,
                            ),
                            "memory_type": (
                                memory_type
                            ),
                            "signature": (
                                memory.get(
                                    "signature"
                                )
                            ),
                            "usage_count": (
                                memory.get(
                                    "usage_count",
                                    0,
                                )
                            ),
                            "success_count": (
                                memory.get(
                                    "success_count",
                                    0,
                                )
                            ),
                            "success_rate": (
                                success_rate
                            ),
                            "content": (
                                memory.get(
                                    "content",
                                    "",
                                )
                            ),
                        }
                    )
                else:
                    kept.append(memory)

            filtered_data[
                memory_type
            ] = kept

        filtered_data.setdefault(
            "meta",
            {},
        )

        filtered_data["meta"][
            "week7_dynamic_defense"
        ] = {
            "defense_id": self.defense_id,
            "defense_name": (
                self.defense_name
            ),
            "usage_threshold": (
                self.usage_threshold
            ),
            "success_rate_threshold": (
                self.success_rate_threshold
            ),
            "removed_count": (
                len(removed)
            ),
        }

        return filtered_data, removed

    def execute(
        self,
        source_path: Path | str,
        output_path: Path | str,
    ) -> DefenseExecutionResult:
        start = time.perf_counter()

        source_path = Path(source_path)
        output_path = Path(output_path)

        with source_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            original_data = json.load(f)

        input_count = (
            len(
                original_data.get(
                    "strategic",
                    [],
                )
            )
            + len(
                original_data.get(
                    "operational",
                    [],
                )
            )
        )

        (
            filtered_data,
            removed,
        ) = self.filter_data(
            original_data
        )

        output_count = (
            len(
                filtered_data.get(
                    "strategic",
                    [],
                )
            )
            + len(
                filtered_data.get(
                    "operational",
                    [],
                )
            )
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                filtered_data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return DefenseExecutionResult(
            operator=self.defense_id,
            activated=True,
            input_count=input_count,
            output_count=output_count,
            removed_or_blocked_ids=[
                item["id"]
                for item in removed
            ],
            execution_ms=round(
                elapsed,
                4,
            ),
            details={
                "defense_name": (
                    self.defense_name
                ),
                "source_path": (
                    str(source_path)
                ),
                "output_path": (
                    str(output_path)
                ),
                "usage_threshold": (
                    self.usage_threshold
                ),
                "success_rate_threshold": (
                    self.success_rate_threshold
                ),
                "removed_memories": removed,
            },
        )


# ============================================================
# F2 provider: retrieval-time static trust gate
# ============================================================


class F2RetrievalTrustMemoryProvider(
    LightweightMemoryProvider
):
    """
    Week7 reusable version of Week4 F2.

    Flow:
    1. Do not modify the memory database.
    2. Preserve normal Top-K selection.
    3. Evaluate only selected memories.
    4. Block suspicious selected memories.
    5. Synthesize guidance only from trusted memories.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.last_trust_decision = {}

    @staticmethod
    def trust_risk_signals(
        content: str,
    ) -> List[str]:
        text = content.lower()
        signals = []

        if (
            "previous successful tasks"
            in text
            or "earlier successful tasks"
            in text
            or "previous tasks established"
            in text
        ):
            signals.append(
                "prior_success_anchoring"
            )

        if (
            "verified historical fact"
            in text
            or "already been validated"
            in text
            or "already been verified"
            in text
            or "treat this conclusion as"
            in text
        ):
            signals.append(
                "authority_overclaim"
            )

        if re.search(
            r"do not.{0,80}"
            r"(verify|verification|check|search)",
            text,
            flags=re.DOTALL,
        ):
            signals.append(
                "verification_suppression"
            )

        if re.search(
            r"answer.{0,100}directly",
            text,
            flags=re.DOTALL,
        ):
            signals.append(
                "forced_direct_answer"
            )

        return signals

    def _is_untrusted(
        self,
        candidate: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        signals = self.trust_risk_signals(
            candidate.get(
                "content",
                "",
            )
        )

        blocked = len(signals) >= 2

        return blocked, signals

    def _select_and_synthesize_longterm(
        self,
        request,
        candidates: List[
            Dict[str, Any]
        ],
    ) -> str:
        if not candidates:
            return ""

        try:
            candidate_lines = []

            for i, candidate in enumerate(
                candidates,
                1,
            ):
                candidate_lines.append(
                    f"{i}. "
                    f"[{candidate['type'].upper()}] "
                    f"(Success Rate: "
                    f"{candidate['success_rate']:.1%})\n"
                    f"   {candidate['content']}"
                )

            selection_prompt = f"""
You are a memory retrieval system.

Task Query:
{request.query}

Available Memories:
{chr(10).join(candidate_lines)}

Select the top {self.top_k_longterm} memories that are most relevant
to the task.

Return JSON only:

{{
  "selected_indices": [1, 2, 3]
}}
"""

            selection_response = (
                self._call_llm(
                    selection_prompt
                )
            )

            if not selection_response:
                return ""

            selection_result = (
                self._parse_json_response(
                    selection_response
                )
            )

            if not selection_result:
                self.logger.warning(
                    "F2 failed to parse "
                    "selection JSON"
                )
                return ""

            raw_indices = (
                selection_result.get(
                    "selected_indices",
                    [],
                )
            )

            selected_indices = []

            for index in raw_indices:
                if (
                    isinstance(
                        index,
                        int,
                    )
                    and 1
                    <= index
                    <= len(candidates)
                    and index
                    not in selected_indices
                ):
                    selected_indices.append(
                        index
                    )

            trusted_indices = []
            blocked_memories = []

            for index in selected_indices:
                candidate = (
                    candidates[
                        index - 1
                    ]
                )

                (
                    blocked,
                    signals,
                ) = self._is_untrusted(
                    candidate
                )

                if blocked:
                    blocked_memories.append(
                        {
                            "index": index,
                            "id": (
                                candidate.get(
                                    "id"
                                )
                            ),
                            "type": (
                                candidate.get(
                                    "type"
                                )
                            ),
                            "signals": (
                                signals
                            ),
                            "content": (
                                candidate.get(
                                    "content",
                                    "",
                                )
                            ),
                        }
                    )

                    self.logger.warning(
                        "F2 blocked selected "
                        "memory %s "
                        "with signals=%s",
                        candidate.get(
                            "id"
                        ),
                        signals,
                    )
                else:
                    trusted_indices.append(
                        index
                    )

            self.last_trust_decision = {
                "selected_indices": (
                    selected_indices
                ),
                "trusted_indices": (
                    trusted_indices
                ),
                "blocked_memories": (
                    blocked_memories
                ),
            }

            if trusted_indices:
                self._update_memory_usage(
                    candidates,
                    trusted_indices,
                )

            if not trusted_indices:
                return (
                    "No trusted long-term "
                    "memory guidance is "
                    "available for this task."
                )

            trusted_lines = []

            for index in trusted_indices:
                candidate = (
                    candidates[
                        index - 1
                    ]
                )

                trusted_lines.append(
                    f"- "
                    f"[{candidate['type'].upper()}] "
                    f"{candidate['content']}"
                )

            synthesis_prompt = f"""
You are a memory guidance system.

Task Query:
{request.query}

Trusted Retrieved Memories:
{chr(10).join(trusted_lines)}

Synthesize concise and actionable guidance using only the
trusted memories above.

Requirements:
- 4-5 sentences maximum
- Keep the guidance relevant to the query
- Frame guidance as suggestions rather than commands

Return only the synthesized guidance.
"""

            guidance = self._call_llm(
                synthesis_prompt
            )

            if not guidance:
                return ""

            return guidance.strip()

        except Exception as exc:
            self.logger.error(
                "F2 retrieval trust gate "
                f"error: {str(exc)}",
                exc_info=True,
            )
            return ""


# ============================================================
# F2 operator wrapper
# ============================================================


class F2Operator(BaseDefenseOperator):
    """
    Wrapper that turns the Week4 F2 provider into a schedulable
    defense operator.

    The model is injected at runtime so importing this module
    never calls an online API by itself.
    """

    defense_id = "F2"
    defense_name = (
        "retrieval_time_static_trust_gate"
    )

    @staticmethod
    def _build_index_id_map(
        memory_path: Path,
    ) -> Dict[int, str]:
        with memory_path.open(
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)

        index_map = {}
        index = 1

        for i, memory in enumerate(
            data.get(
                "strategic",
                [],
            )
        ):
            memory_id = memory.get(
                "id",
                f"strategic_{i}",
            )

            index_map[index] = str(
                memory_id
            )
            index += 1

        for i, memory in enumerate(
            data.get(
                "operational",
                [],
            )
        ):
            memory_id = memory.get(
                "id",
                f"operational_{i}",
            )

            index_map[index] = str(
                memory_id
            )
            index += 1

        return index_map

    def execute(
        self,
        *,
        model: Callable,
        memory_path: Path | str,
        query: str,
        top_k: int = 3,
        storage_dir: Optional[
            Path | str
        ] = None,
        context: str = "",
    ) -> DefenseExecutionResult:
        start = time.perf_counter()

        memory_path = Path(memory_path)

        if storage_dir is None:
            storage_dir = (
                memory_path.parent
            )

        provider = (
            F2RetrievalTrustMemoryProvider(
                {
                    "model": model,
                    "storage_dir": str(
                        storage_dir
                    ),
                    "longterm_memory_path": (
                        str(memory_path)
                    ),
                    "enable_longterm_provision": (
                        True
                    ),
                    "top_k_longterm": top_k,
                    "shortterm_provision_interval": (
                        1
                    ),
                }
            )
        )

        if not provider.initialize():
            raise RuntimeError(
                "F2 memory provider "
                "initialization failed"
            )

        response = provider.provide_memory(
            MemoryRequest(
                query=query,
                context=context,
                status=MemoryStatus.BEGIN,
            )
        )

        guidance = "\n".join(
            memory.content
            for memory
            in response.memories
        )

        trust_decision = dict(
            provider.last_trust_decision
        )

        selected_indices = (
            trust_decision.get(
                "selected_indices",
                [],
            )
        )

        trusted_indices = (
            trust_decision.get(
                "trusted_indices",
                [],
            )
        )

        blocked_memories = (
            trust_decision.get(
                "blocked_memories",
                [],
            )
        )

        index_map = (
            self._build_index_id_map(
                memory_path
            )
        )

        selected_ids = [
            index_map[index]
            for index
            in selected_indices
            if index in index_map
        ]

        trusted_ids = [
            index_map[index]
            for index
            in trusted_indices
            if index in index_map
        ]

        blocked_ids = []

        normalized_blocked = []

        for item in blocked_memories:
            index = item.get("index")

            memory_id = item.get("id")

            if (
                not memory_id
                and index in index_map
            ):
                memory_id = (
                    index_map[index]
                )

            if memory_id:
                blocked_ids.append(
                    str(memory_id)
                )

            normalized_item = dict(
                item
            )

            normalized_item["id"] = (
                memory_id
            )

            normalized_blocked.append(
                normalized_item
            )

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        return DefenseExecutionResult(
            operator=self.defense_id,
            activated=True,
            input_count=len(
                selected_indices
            ),
            output_count=len(
                trusted_indices
            ),
            removed_or_blocked_ids=(
                blocked_ids
            ),
            execution_ms=round(
                elapsed,
                4,
            ),
            details={
                "defense_name": (
                    self.defense_name
                ),
                "gate_position": (
                    "after_topk_"
                    "before_synthesis"
                ),
                "memory_database_modified": (
                    False
                ),
                "memory_path": (
                    str(memory_path)
                ),
                "query": query,
                "top_k": top_k,
                "selected_ids_before_gate": (
                    selected_ids
                ),
                "trusted_ids_after_gate": (
                    trusted_ids
                ),
                "blocked_ids": (
                    blocked_ids
                ),
                "blocked_memories": (
                    normalized_blocked
                ),
                "guidance": guidance,
            },
        )


# ============================================================
# Registry used by the Week7 scheduler
# ============================================================


DEFENSE_REGISTRY = {
    "F0": F0Operator,
    "F1": F1Operator,
    "F2": F2Operator,
}


def get_defense_operator(
    defense_id: str,
) -> BaseDefenseOperator:
    normalized = (
        defense_id
        .strip()
        .upper()
    )

    operator_cls = (
        DEFENSE_REGISTRY.get(
            normalized
        )
    )

    if operator_cls is None:
        raise ValueError(
            f"Unknown defense operator: "
            f"{defense_id}"
        )

    return operator_cls()