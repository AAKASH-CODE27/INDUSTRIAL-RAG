# Evaluation and RAG Quality

## Scope

This repository includes a retrieval evaluation dataset and script for checking whether the system finds relevant maintenance evidence for a representative question set.

## Dataset

The evaluation questions live in:

- backend/data/rag_evaluation.json

They cover categories such as:

- equipment identification
- maintenance procedure questions
- fault diagnosis
- troubleshooting assistance
- safety-related guidance
- sensor interpretation
- irrelevant or low-confidence cases
- insufficient evidence cases

## Methodology

The script in:

- backend/scripts/evaluate_retrieval.py

loads the evaluation dataset, runs the retriever, and records:

- retrieved documents or sources
- whether the expected document was hit
- expected vs actual abstention behavior
- hit-rate style metrics

This evaluation is intentionally conservative and does not invent outcomes.

## Metrics

The current script reports:

- total queries
- retrieval hits
- retrieval hit rate
- abstention accuracy

These metrics are valid as far as the repository’s current retriever and dataset support them.

## Interpretation

- A high retrieval hit rate means the relevant document is commonly surfaced.
- An abstention match indicates the system behaves consistently when evidence is weak or missing.
- Poor retrieval does not imply the chat answer is necessarily wrong, because the chat layer may still abstain and remain safe.

## Limitations

This project does not include a full production answer-evaluation harness with human-labelled truth data for all generated responses. Therefore:

- exact answer correctness is not fabricated
- groundedness is reasoned about operationally rather than claimed as a fixed benchmark number
- metrics should be interpreted as local quality signals, not universal validation

## Running the evaluation

From the backend folder:

python scripts/evaluate_retrieval.py

## Recommended future work

- expand the benchmark with more real maintenance records and human-labelled answers
- score answer faithfulness and source coverage automatically
- log retrieval metrics per query for product review and regression checking
