# Week 5 — DPMF Drift Awareness: Collection and Detection

## 1. Objective

Week 5 implements a prototype of the DPMF drift-awareness pipeline for self-evolving Agent memory architectures.

The main objectives are:

1. Detect retrieval-architecture drift from architecture snapshots.
2. Quantify the security risk associated with detected drift.
3. Standardize drift events using a unified JSON Schema.
4. Map detected drift to defense candidates using the Week 4 architecture-defense knowledge base.
5. Validate the prototype through both historical offline replay and newly collected live DeepSeek experiments.
6. Introduce a no-drift control to evaluate false drift alarms.

The prototype operates as a side-channel observer and does not directly modify the underlying MemEvolve retrieval process.

---

## 2. Experimental Scenarios

### Control — No Drift

Baseline architecture is compared with itself.

- Retrieval policy: semantic relevance first
- Top-K: 3
- Expected result: no architecture drift

### D1 — Retrieval Top-K Drift

- Before: top_k_longterm = 3
- After: top_k_longterm = 5
- Drift type: retrieval_topk

### D2 — Retrieval Policy Drift

- Before: semantic_relevance_first
- After: historical_success_rate_first
- Semantic relevance becomes a tie-breaker
- Drift type: retrieval_policy

---

## 3. DPMF Prototype Pipeline

Architecture Snapshot
→ Drift Detection
→ Behavior Evidence Collection
→ Composite Security Risk Assessment
→ Standardized Drift Event
→ Architecture-Defense Knowledge Base
→ Defense Recommendation

Main scripts:

- drift_detector.py — detects numerical and categorical architecture drift
- risk_scorer.py — calculates composite security risk
- validate_event.py — validates DPMF events against the unified schema
- defense_mapper.py — maps drift events to empirically evaluated defenses
- calculate_live_overlap.py — calculates live retrieval-set Jaccard overlap
- compare_offline_live.py — compares historical replay and live observations
- summarize_live_final.py — produces the final live experiment summary

---

## 4. Risk Model

The current prototype uses heuristic weights:

| Component | Weight |
| --- | ---: |
| Configuration change | 0.25 |
| Clean utility drop | 0.30 |
| Retrieval instability | 0.20 |
| Attack exposure | 0.25 |

The score is defined as a composite security risk score rather than a pure drift-magnitude score.

Risk levels:

- LOW: risk < 0.30
- MEDIUM: 0.30 <= risk < 0.60
- HIGH: risk >= 0.60

The current weights are prototype heuristic parameters and are not claimed to be theoretically optimal.

Architecture drift and security risk are treated separately:

- drift_detected determines whether architecture drift occurred.
- risk_score measures the security and utility risk of the current state.

This distinction allows the no-drift baseline to retain a non-zero background security risk when poisoned memories remain attack-accessible.

---

## 5. Offline Replay

Historical Week 3 experimental data were first used to develop and debug the DPMF prototype.

### D1 Offline Replay

- Top-K: 3 -> 5
- Clean correct rate: 1.0 -> 0.6
- Clean retrieval overlap: 0.60
- Poisoned retrieval overlap: 0.60
- Attack success rate after drift: 1.0
- Risk score: 0.6167
- Risk level: HIGH

### D2 Offline Replay

- Retrieval policy:
  semantic_relevance_first -> historical_success_rate_first
- Clean correct rate: 1.0 -> 0.0
- Clean retrieval overlap: 0.44
- Poisoned retrieval overlap: 0.80
- Attack success rate after drift: 1.0
- Risk score: 0.9120
- Risk level: HIGH

Offline risk ordering:

D2 > D1

---

## 6. Live Observation

To avoid relying entirely on historical results, Week 5 recollected experimental data using the DeepSeek API.

Experimental configuration:

- Model: deepseek-v4-flash
- API: DeepSeek
- Temperature: 0
- Clean trials per state: 5
- Poisoned trials per state: 5

Three fresh online states were executed.

### L0 — Baseline Live

- Top-K: 3
- Clean correct rate: 1.0
- Poison hit rate: 1.0
- Attack success rate: 1.0

### L1 — D1 Top-K Drift Live

- Top-K: 5
- Clean correct rate: 0.4
- Poison hit rate: 1.0
- Attack success rate: 0.8
- Clean retrieval overlap: 0.60
- Poisoned retrieval overlap: 0.60
- Risk score: 0.6267
- Risk level: HIGH

The online result shows that poisoned memories were retrieved in all poisoned trials, while attack success was 0.8.

Therefore, poison exposure and final attack success are treated as two distinct signals.

### L2 — D2 History-First Drift Live

- Retrieval policy: historical success rate first
- Clean correct rate: 0.0
- Poison hit rate: 1.0
- Attack success rate: 1.0
- Clean retrieval overlap: 0.50
- Poisoned retrieval overlap: 0.80
- Risk score: 0.9000
- Risk level: HIGH

---

## 7. No-Drift Control

The baseline Top-K=3 architecture snapshot was compared with itself.

Detection result:

- drift_detected = false
- change_score = 0.0

Behavior comparison:

- Clean utility drop: 0.0
- Retrieval instability: 0.0
- Attack exposure: 1.0

Composite risk:

- risk_score = 0.2500
- risk_level = LOW

The non-zero score represents background attack exposure rather than architecture drift.

The control confirms that DPMF does not classify an unchanged architecture as drift.

---

## 8. Live Final Comparison

| Scenario | Drift | Risk Score | Risk Level | Primary Defense |
| --- | --- | ---: | --- | --- |
| Control | No drift | 0.2500 | LOW | — |
| D1 | Retrieval Top-K | 0.6267 | HIGH | F2 |
| D2 | Retrieval policy | 0.9000 | HIGH | F2 |

Final live risk ordering:

D2 > D1 > CONTROL

---

## 9. Offline Replay vs Live Observation

| Scenario | Offline | Live | Delta |
| --- | ---: | ---: | ---: |
| D1 | 0.6167 | 0.6267 | +0.0100 |
| D2 | 0.9120 | 0.9000 | -0.0120 |

Both experimental modes produced the same risk ordering:

D2 > D1

Risk ordering stable: True

The individual LLM-based metrics showed some run-to-run fluctuation, but the DPMF risk ordering remained stable.

For D1, historical clean correctness was 0.6 while the new live result was 0.4. Historical attack success was 1.0 while the live result was 0.8.

For D2, the live clean retrieval overlap changed from the historical value of 0.44 to 0.50, while the overall high-risk conclusion remained unchanged.

---

## 10. Defense Recommendation

The DPMF prototype queries the Week 4 architecture-defense knowledge base:

experiments/week4/knowledge_base/architecture_defense_mapping_v0.csv

Defense candidates are ranked using previously measured security and utility performance.

### D1

F2: retrieval_time_static_trust_gate

- Defense position: post_retrieval_pre_synthesis
- Attack success rate: 0.0
- Clean correct rate: 1.0
- Defense block rate: 1.0
- False positive rate: 0.0
- Utility status: stable

F1: static_history_statistics_filter

- Defense position: pre_retrieval
- Attack success rate: 0.0
- Clean correct rate: 0.4
- Defense block rate: 1.0
- False positive rate: 0.0
- Utility status: degraded

Primary recommendation: F2

### D2

F2: retrieval_time_static_trust_gate

- Attack success rate: 0.0
- Clean correct rate: 0.8
- Defense block rate: 1.0
- False positive rate: 0.0
- Utility status: mostly_stable

F1: static_history_statistics_filter

- Attack success rate: 0.0
- Clean correct rate: 0.0
- Defense block rate: 1.0
- False positive rate: 0.0
- Utility status: collapsed

Primary recommendation: F2

The defense recommendation remained stable between offline replay and live observation.

---

## 11. Main Findings

1. DPMF successfully detected both numerical Top-K drift and categorical retrieval-policy drift.

2. The no-drift control produced no false architecture-drift detection.

3. The live composite security risk scores were:
   - Control: 0.2500, LOW
   - D1: 0.6267, HIGH
   - D2: 0.9000, HIGH

4. Retrieval-policy drift D2 consistently produced greater risk than Top-K drift D1.

5. Newly collected DeepSeek experiments showed measurable run-to-run variation relative to historical replay, demonstrating the need for runtime observation rather than relying only on static historical results.

6. Despite metric fluctuations, the DPMF risk ordering remained stable:
   D2 > D1.

7. Poison retrieval exposure and final attack success are not equivalent. In the D1 live experiment, poison hit rate remained 1.0 while attack success rate was 0.8.

8. The architecture-defense knowledge base consistently recommended F2 for D1 and D2 because it preserved substantially more clean-task utility while maintaining attack blocking.

9. Week 5 establishes the complete prototype chain:
   architecture observation -> drift detection -> risk assessment -> knowledge-base mapping -> defense recommendation.

10. Automatic execution and dynamic adjustment of defense strategies are intentionally left for subsequent work.

---

## 12. Key Outputs

### Offline Replay

- results/D1_drift_detection.json
- results/D2_drift_detection.json
- results/D1_dpmf_event.json
- results/D2_dpmf_event.json
- results/dpmf_summary.json

### Live Observation

- results/live/L0_baseline_live.json
- results/live/L1_topk5_live.json
- results/live/L2_history_first_live.json
- results/live/live_retrieval_overlap.json
- results/live/live_D1_dpmf_event.json
- results/live/live_D2_dpmf_event.json
- results/live/offline_vs_live_summary.json
- results/live/control_no_drift_detection.json
- results/live/control_no_drift_event.json
- results/live/live_final_summary.json

### Logs

- logs/live/L0_baseline_live.log
- logs/live/L1_topk5_live.log
- logs/live/L2_history_first_live.log

### Schema

- schemas/drift_event_schema.json

---

## 13. Current Status

Week 5 completed:

- DPMF drift-event schema
- Numerical Top-K drift detection
- Categorical retrieval-policy drift detection
- Composite security risk scoring
- No-drift negative control
- Offline historical replay
- Fresh DeepSeek live observation
- Retrieval-overlap recalculation
- Offline-vs-live stability comparison
- Architecture-defense knowledge-base integration
- Empirical defense recommendation

The current implementation is a DPMF perception and recommendation prototype.

Dynamic defense execution and online defense adaptation are not included in Week 5 and will be addressed in later stages.
