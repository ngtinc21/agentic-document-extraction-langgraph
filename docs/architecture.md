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
  review["Human review queue"]
  eval["Evaluation summary"]

  job --> graph
  sources --> graph
  dict --> graph
  graph --> evidence
  evidence --> results
  results --> review
  results --> eval
```

## Workflow

The MVP graph runs these nodes:

1. `load_job`
2. `load_sources`
3. `evidence_scout`
4. `extract_values`
5. `validate_results`
6. `human_review_gate`
7. `aggregate_results`
8. `evaluate_against_ground_truth`

The same workflow can support other domains by swapping the dictionary, source
documents, validation hints, and optional provider configuration.

## Provider Boundary

The default fake provider is deterministic and used for demos and CI. Optional
providers, such as Gemini, implement the same `BaseLLMProvider` interface and
are configured through environment variables only.
