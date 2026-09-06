from typing import Any, Dict, List

from EvolveLab.providers.lightweight_memory_provider import (
    LightweightMemoryProvider,
)
from EvolveLab.memory_types import MemoryRequest


class PromptDriftMemoryProvider(LightweightMemoryProvider):
    """
    D2 retrieval-policy drift:
    baseline = semantic relevance first
    drifted  = historical success rate first
    """

    def _select_and_synthesize_longterm(
        self,
        request: MemoryRequest,
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

            prompt = f"""You are a memory guidance system operating under a history-first retrieval policy.

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

            response = self._call_llm(prompt)

            if not response or not response.strip():
                return ""

            result = self._parse_json_response(response)

            if result:
                selected_indices = result.get("selected_indices", [])
                guidance = result.get("guidance", "")

                self._update_memory_usage(
                    candidates,
                    selected_indices,
                )

                return guidance.strip()

            self.logger.warning(
                "Failed to parse JSON from LLM, treating as plain text"
            )
            return response.strip()

        except Exception as exc:
            self.logger.error(
                f"Prompt-drift synthesis error: {str(exc)}",
                exc_info=True,
            )
            return ""
