# Agent Roles

This repository describes agent roles as clean-room contracts. The names and
responsibilities are generic and interview-safe; they do not include company
prompts, private ranking rules, internal source lists, client examples, or
proprietary methodology.

## Role Map

| Role | Mode | Responsibility |
| --- | --- | --- |
| `deterministic_orchestrator` | deterministic | Controls LangGraph state, routing, retry budget, aggregation, and human review handoff. |
| `url_extraction` | LLM | Proposes candidate public source URLs for the entity, domain, and dictionary. |
| `url_ranking` | tool | Ranks candidate URLs using deterministic, explainable source-quality signals. |
| `url_verification` | LLM | Verifies whether ranked sources appear relevant to the entity, reporting period, and extraction task. |
| `inside_out_extraction` | LLM | Extracts fields from entity-authored or entity-published sources. |
| `outside_in_extraction` | LLM | Extracts or corroborates fields from independent public sources. |

## Public-Safe Boundary

It is appropriate for this GitHub project to include:

- generic agent names and responsibilities
- clean-room input and output schemas
- synthetic examples
- public-safe prompt contracts
- deterministic demo behavior for CI
- optional provider integrations configured only through environment variables

It should not include:

- copied company prompts or prompt wording
- private source lists or internal URL ranking weights
- client, issuer, ISIN, portfolio, or internal entity examples
- generated outputs from private work
- cloud project IDs, bucket names, API keys, or local company paths
- proprietary ESG scoring, materiality, or validation methodology

## MVP Scope

The runnable demos start from synthetic local markdown reports. The procurement
demo includes synthetic source references so URL extraction, ranking, and
verification can run deterministically in CI. A later version can add public web
fetching behind the same contracts.
