# Architecture

`agentic-document-extraction-langgraph` is organized around a domain-neutral
extraction engine and small domain packs.

```mermaid
flowchart LR
  job["ExtractionJob"];
  source_docs["Source documents"];
  dictionary_entries["Dictionary entries"];
  workflow_node["LangGraph workflow"];
  evidence_records["Evidence records"];
  extraction_results["Extraction results"];
  validation_check{"Validation passed?"};
  review_queue["Human review queue"];
  evaluation_summary["Evaluation summary"];

  job --> workflow_node;
  source_docs --> workflow_node;
  dictionary_entries --> workflow_node;
  workflow_node --> evidence_records;
  evidence_records --> extraction_results;
  extraction_results --> validation_check;
  validation_check -- "retry" --> workflow_node;
  validation_check -- "continue" --> review_queue;
  review_queue --> evaluation_summary;
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

## Agent Roles

The public project uses clean-room agent role contracts. These are generic role
definitions, not copied internal prompts or proprietary implementation details.

```mermaid
flowchart TD
  orchestrator["deterministic_orchestrator"];
  url_extraction["url_extraction LLM"];
  url_ranking["url_ranking tool"];
  url_verification["url_verification LLM"];
  inside_out["inside_out_extraction LLM"];
  outside_in["outside_in_extraction LLM"];
  validation["validation and retry routing"];

  orchestrator --> url_extraction;
  url_extraction --> url_ranking;
  url_ranking --> url_verification;
  url_verification --> inside_out;
  url_verification --> outside_in;
  inside_out --> validation;
  outside_in --> validation;
  validation -- "retry" --> inside_out;
  validation -- "retry" --> outside_in;
  validation -- "continue" --> orchestrator;
```

The current runnable MVP starts from local synthetic markdown documents, so URL
discovery is represented as an extension contract rather than live web fetching.
This keeps the demo deterministic, safe for CI, and free of private source
selection rules.

## Provider Boundary

The default fake provider is deterministic and used for demos and CI. Optional
providers, such as Gemini, implement the same `BaseLLMProvider` interface and
are configured through environment variables only.
