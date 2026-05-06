# Architecture

`agentic-document-extraction-langgraph` is organized around a domain-neutral
extraction engine and small domain packs.

```mermaid
flowchart LR
  job["ExtractionJob"]
  sources["Source documents"]
  dict["Dictionary entries"]
  graph["LangGraph workflow"]
  evidence["Evidence records"]
  results["Extraction results"]
  validation{"Validation passed?"}
  review["Human review queue"]
  eval["Evaluation summary"]

  job --> graph
  sources --> graph
  dict --> graph
  graph --> evidence
  evidence --> results
  results --> validation
  validation -- "retry" --> graph
  validation -- "continue" --> review
  review --> eval
```

## Workflow

The MVP graph runs these nodes:

1. `load_job`
2. `load_sources`
3. `evidence_scout`
4. `extract_values`
5. `validate_results`
6. conditional retry to `extract_values` when validation flags a result
7. `human_review_gate`
8. `aggregate_results`
9. `evaluate_against_ground_truth`

The graph is intentionally cyclic. Validation failures and low-confidence
results can be routed back to extraction with the previous result and validation
messages available in state. The retry budget is controlled by
`run_options.max_validation_retries`; unresolved fields move to human review
after the budget is used.

The same workflow can support other domains by swapping the dictionary, source
documents, validation hints, and optional provider configuration.

## Provider Boundary

The default fake provider is deterministic and used for demos and CI. Optional
providers, such as Gemini, implement the same `BaseLLMProvider` interface and
are configured through environment variables only.
