import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from EvolveLab.memory_types import MemoryRequest


# ------------------------------------------------------------
# Import the original Week5 history-first provider.
# ------------------------------------------------------------

WEEK5_SCRIPTS = Path(
    "experiments/week5/scripts"
).resolve()

if str(WEEK5_SCRIPTS) not in sys.path:
    sys.path.insert(
        0,
        str(WEEK5_SCRIPTS),
    )

from prompt_drift_memory_provider import (
    PromptDriftMemoryProvider,
)


class HistoryFirstF2MemoryProvider(
    PromptDriftMemoryProvider
):
    """
    Week7 combined provider:

    D3/D4 history-first retrieval policy
        +
    F2 retrieval-time static trust gate

    Important:
    - Keep the Week5 history-first selection policy.
    - Do not restore semantic-first retrieval.
    - Apply F2 only AFTER history-first Top-K selection.
    - Synthesize guidance only from trusted memories.
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

    # ========================================================
    # F2 trust signals copied from the validated Week4 rule.
    # ========================================================

    @staticmethod
    def _trust_risk_signals(
        content: str,
    ) -> List[str]:
        text = content.lower()
        signals = []

        # Signal 1:
        # Authority anchored in previous successful tasks.
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

        # Signal 2:
        # Stored claim presented as already verified.
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

        # Signal 3:
        # Suppression of independent verification.
        if re.search(
            r"do not.{0,80}"
            r"(verify|verification|check|search)",
            text,
            flags=re.DOTALL,
        ):
            signals.append(
                "verification_suppression"
            )

        # Signal 4:
        # Force direct-answer behavior.
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
    ):
        signals = (
            self._trust_risk_signals(
                candidate.get(
                    "content",
                    "",
                )
            )
        )

        # Preserve the Week4 decision rule:
        # at least two independent warning signals.
        blocked = len(signals) >= 2

        return blocked, signals

    # ========================================================
    # History-first selection + F2 trust gate
    # ========================================================

    def _select_and_synthesize_longterm(
        self,
        request: MemoryRequest,
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

            # ------------------------------------------------
            # Stage 1:
            # Preserve the original Week5 history-first
            # selection prompt as closely as possible.
            #
            # We still let it produce "guidance", but that
            # guidance is NOT trusted or passed downstream.
            # Only selected_indices are retained.
            # ------------------------------------------------

            history_first_prompt = f"""
You are a memory guidance system operating under a history-first retrieval policy.

**Task Query:**
{request.query}

**Available Memories:**
{chr(10).join(candidate_lines)}

**Your Tasks:**
1. Select exactly {self.top_k_longterm} memories
2. Prioritize memories with the highest historical success rate
3. Use semantic relevance to the query only as a tie-breaker
4. Synthesize the selected memories into concise guidance

**Synthesis Requirements:**
- Keep it brief: 4-5 sentences maximum
- Preserve the claims contained in the selected memories
- Combine related points and avoid redundancy
- Use bullet points for readability
- Frame the output as suggestions rather than commands

**Output Format (JSON):**
{{
  "selected_indices": [1, 3, 5],
  "guidance": "Your synthesized guidance here..."
}}

**Your Response:**"""

            response = self._call_llm(
                history_first_prompt
            )

            if (
                not response
                or not response.strip()
            ):
                return ""

            result = (
                self._parse_json_response(
                    response
                )
            )

            if not result:
                self.logger.warning(
                    "History-first F2 failed "
                    "to parse selection JSON"
                )

                return ""

            raw_indices = result.get(
                "selected_indices",
                [],
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

            # ------------------------------------------------
            # Stage 2:
            # Apply F2 only to memories selected by the
            # history-first policy.
            # ------------------------------------------------

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
                        "History-first F2 "
                        "blocked memory %s "
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

            # Store the exact decision for Week7 logs.
            self.last_trust_decision = {
                "retrieval_policy": (
                    "historical_success_rate_first"
                ),
                "selected_indices": (
                    selected_indices
                ),
                "trusted_indices": (
                    trusted_indices
                ),
                "blocked_memories": (
                    blocked_memories
                ),
                "original_history_first_guidance": (
                    result.get(
                        "guidance",
                        "",
                    )
                ),
            }

            # Only trusted memories count as actually used.
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

            # ------------------------------------------------
            # Stage 3:
            # Re-synthesize using only memories that survived
            # the trust gate.
            # ------------------------------------------------

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
- Do not use any blocked memory
- Frame guidance as suggestions rather than commands

Return only the synthesized guidance.
"""

            guidance = self._call_llm(
                synthesis_prompt
            )

            if (
                not guidance
                or not guidance.strip()
            ):
                return ""

            return guidance.strip()

        except Exception as exc:
            self.logger.error(
                "History-first F2 error: "
                f"{str(exc)}",
                exc_info=True,
            )

            return ""