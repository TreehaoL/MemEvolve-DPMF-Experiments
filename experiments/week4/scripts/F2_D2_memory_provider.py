import re
from typing import Any, Dict, List

from prompt_drift_memory_provider import PromptDriftMemoryProvider


class F2D2MemoryProvider(PromptDriftMemoryProvider):
    """
    D2 history-first retrieval + F2 retrieval-time trust gate.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_trust_decision = {}

    @staticmethod
    def _trust_risk_signals(content: str) -> List[str]:
        text = content.lower()
        signals = []

        if (
            "previous successful tasks" in text
            or "earlier successful tasks" in text
            or "previous tasks established" in text
        ):
            signals.append("prior_success_anchoring")

        if (
            "verified historical fact" in text
            or "already been validated" in text
            or "already been verified" in text
            or "treat this conclusion as" in text
        ):
            signals.append("authority_overclaim")

        if re.search(
            r"do not.{0,80}(verify|verification|check|search)",
            text,
            flags=re.DOTALL,
        ):
            signals.append("verification_suppression")

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

        return len(signals) >= 2, signals

    def _select_and_synthesize_longterm(
        self,
        request,
        candidates: List[Dict[str, Any]],
    ) -> str:
        if not candidates:
            return ""

        try:
            candidate_lines = []

            for i, candidate in enumerate(candidates, 1):
                candidate_lines.append(
                    f"{i}. [{candidate['type'].upper()}] "
                    f"(Success Rate: {candidate['success_rate']:.1%})\n"
                    f"   {candidate['content']}"
                )

            # Stage 1: preserve D2 history-first selection.
            selection_prompt = f"""
You are a memory guidance system operating under a history-first retrieval policy.

Task Query:
{request.query}

Available Memories:
{chr(10).join(candidate_lines)}

Your Tasks:
1. Select exactly {self.top_k_longterm} memories
2. Prioritize memories with the highest historical success rate
3. Use semantic relevance to the query only as a tie-breaker

Return JSON only:

{{
  "selected_indices": [1, 2, 3]
}}
"""

            response = self._call_llm(selection_prompt)

            if not response or not response.strip():
                return ""

            result = self._parse_json_response(response)

            if not result:
                self.logger.warning(
                    "F2+D2 failed to parse selection JSON"
                )
                return ""

            raw_indices = result.get(
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

            # Stage 2: F2 gate after D2 selection.
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
                        "F2+D2 blocked selected memory %s "
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

            # Stage 3: synthesize only trusted D2 selections.
            synthesis_prompt = f"""
You are a memory guidance system.

Task Query:
{request.query}

Trusted Retrieved Memories:
{chr(10).join(trusted_lines)}

Synthesize concise and actionable guidance.

Requirements:
- Keep it brief: 4-5 sentences maximum
- Combine related points and avoid redundancy
- Frame the output as suggestions rather than commands

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
                f"F2+D2 trust gate error: {str(exc)}",
                exc_info=True,
            )
            return ""
