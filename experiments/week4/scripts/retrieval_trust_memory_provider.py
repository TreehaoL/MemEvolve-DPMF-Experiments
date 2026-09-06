import re
from typing import Any, Dict, List

from EvolveLab.providers.lightweight_memory_provider import LightweightMemoryProvider


class RetrievalTrustMemoryProvider(LightweightMemoryProvider):
    """
    F2: Retrieval-time static trust gate.

    Flow:
    1. Keep the original memory database unchanged.
    2. Let the LLM select Top-K candidates normally.
    3. Apply a static trust check only to the selected candidates.
    4. Block suspicious selected memories before final synthesis.
    5. Synthesize guidance from trusted selected memories only.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_trust_decision = {}

    @staticmethod
    def _trust_risk_signals(content: str) -> List[str]:
        text = content.lower()
        signals = []

        # Signal 1: anchoring authority in previous task success
        if (
            "previous successful tasks" in text
            or "earlier successful tasks" in text
            or "previous tasks established" in text
        ):
            signals.append("prior_success_anchoring")

        # Signal 2: presenting remembered claims as already verified facts
        if (
            "verified historical fact" in text
            or "already been validated" in text
            or "already been verified" in text
            or "treat this conclusion as" in text
        ):
            signals.append("authority_overclaim")

        # Signal 3: suppressing independent verification
        if re.search(
            r"do not.{0,80}(verify|verification|check|search)",
            text,
            flags=re.DOTALL,
        ):
            signals.append("verification_suppression")

        # Signal 4: forcing a specific direct-answer behavior
        if re.search(
            r"answer.{0,100}directly",
            text,
            flags=re.DOTALL,
        ):
            signals.append("forced_direct_answer")

        return signals

    def _is_untrusted(self, candidate: Dict[str, Any]):
        signals = self._trust_risk_signals(
            candidate.get("content", "")
        )

        # Require at least two independent warning signals.
        blocked = len(signals) >= 2

        return blocked, signals

    def _select_and_synthesize_longterm(
        self,
        request,
        candidates: List[Dict[str, Any]],
    ) -> str:
        if not candidates:
            return ""

        try:
            candidate_lines = []

            for i, c in enumerate(candidates, 1):
                candidate_lines.append(
                    f"{i}. [{c['type'].upper()}] "
                    f"(Success Rate: {c['success_rate']:.1%})\n"
                    f"   {c['content']}"
                )

            # Stage 1: preserve normal Top-K selection.
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

            selection_response = self._call_llm(
                selection_prompt
            )

            if not selection_response:
                return ""

            selection_result = self._parse_json_response(
                selection_response
            )

            if not selection_result:
                self.logger.warning(
                    "F2 failed to parse selection JSON"
                )
                return ""

            raw_indices = selection_result.get(
                "selected_indices",
                [],
            )

            selected_indices = []

            for index in raw_indices:
                if (
                    isinstance(index, int)
                    and 1 <= index <= len(candidates)
                    and index not in selected_indices
                ):
                    selected_indices.append(index)

            trusted_indices = []
            blocked_memories = []

            for index in selected_indices:
                candidate = candidates[index - 1]

                blocked, signals = self._is_untrusted(
                    candidate
                )

                if blocked:
                    blocked_memories.append(
                        {
                            "index": index,
                            "id": candidate.get("id"),
                            "type": candidate.get("type"),
                            "signals": signals,
                            "content": candidate.get(
                                "content",
                                "",
                            ),
                        }
                    )

                    self.logger.warning(
                        "F2 blocked selected memory %s "
                        "with signals=%s",
                        candidate.get("id"),
                        signals,
                    )
                else:
                    trusted_indices.append(index)

            self.last_trust_decision = {
                "selected_indices": selected_indices,
                "trusted_indices": trusted_indices,
                "blocked_memories": blocked_memories,
            }

            # Only trusted memories count as actually used.
            if trusted_indices:
                self._update_memory_usage(
                    candidates,
                    trusted_indices,
                )

            if not trusted_indices:
                return (
                    "No trusted long-term memory guidance "
                    "is available for this task."
                )

            trusted_lines = []

            for index in trusted_indices:
                candidate = candidates[index - 1]

                trusted_lines.append(
                    f"- [{candidate['type'].upper()}] "
                    f"{candidate['content']}"
                )

            # Stage 2: synthesize only from candidates that
            # survived the trust gate.
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

        except Exception as e:
            self.logger.error(
                f"F2 retrieval trust gate error: {str(e)}",
                exc_info=True,
            )
            return ""
