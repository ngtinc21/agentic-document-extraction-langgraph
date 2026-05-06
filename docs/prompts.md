# Prompt Design

This project does not include proprietary prompts. Public prompt examples should
be treated as implementation contracts: short, generic templates that explain
what each agentic step receives, what it must return, and how validation
feedback should be used on retry.

## Evidence Scout Contract

Goal: find candidate evidence for one dictionary entry across the provided
documents.

Inputs:

- dictionary entry id, label, definition, expected type, expected unit
- evidence keywords and evidence requirements
- source document id, title, fiscal year, and text

Output:

- source id
- snippet
- location
- confidence
- short rationale

Rules:

- return evidence only when the snippet supports the field definition
- prefer explicit values, units, dates, and entity names
- do not infer a value during evidence scouting

## Extraction Contract

Goal: extract one structured value from the selected evidence.

Inputs:

- dictionary entry and validation hints
- candidate evidence records
- previous extraction result and validation messages, when this is a retry

Output:

- value
- unit
- evidence id
- confidence
- status
- validation messages, if any

Rules:

- use the requested schema exactly
- return `missing` when evidence is absent
- return `needs_review` when evidence exists but the value is ambiguous
- on retry, explicitly address the validation message that caused the retry

## Validation Contract

Goal: verify whether a result satisfies the dictionary definition and validation
rules.

Checks:

- value type
- expected unit or allowed units
- required evidence
- confidence threshold
- min/max constraints where provided

Routing:

- pass valid results forward
- route failed or uncertain results back to extraction while retry budget remains
- send unresolved results to human review after retry budget is used
