# Week 3: Controlled Memory-Architecture Drift

## Objective

Construct controlled drift scenarios on the Week 2 poisoning baseline and
compare retrieval behavior before and after drift.

## Completed Scenarios

### D1: Top-K Configuration Drift

- Before: top_k_longterm = 3
- After: top_k_longterm = 5
- Clean correctness: 1.0 -> 0.6
- Poison hit rate: 1.0 -> 1.0
- Attack success rate: 1.0 -> 1.0
- Clean retrieval overlap: 0.6
- Poisoned retrieval overlap: 0.6

### D2: Retrieval-Policy Drift

- Before: semantic relevance first
- After: historical success rate first
- Top-K remained fixed at 3
- Clean correctness: 1.0 -> 0.0
- Poison hit rate: 1.0 -> 1.0
- Attack success rate: 1.0 -> 1.0
- Clean retrieval overlap: 0.44
- Poisoned retrieval overlap: 0.8

## Controlled Variables

- Query remained unchanged.
- Each clean and poisoned group contained five trials.
- Clean and poisoned memory files remained unchanged.
- API model configuration remained unchanged.
- Only the specified drift parameter changed in each scenario.

## Directory Structure

- configs/: drift configurations
- snapshots/: before-and-after architecture snapshots
- scripts/: experiment and custom provider scripts
- logs/: execution logs
- results/: raw results, comparisons and overlap metrics

## Key Result Files

- results/D1_comparison.json
- results/D2_comparison.json
- results/retrieval_overlap.json
- results/drift_scenarios.md

## Current Conclusion

Both drift scenarios reduced clean-task correctness in the observed runs while
the poisoning attack remained fully successful. D2 changed clean retrieval
sets more strongly than poisoned retrieval sets. Results remain preliminary
because retrieval selection is LLM-driven and should be validated through
additional repeated experiments.
