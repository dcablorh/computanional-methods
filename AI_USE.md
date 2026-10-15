# AI-use disclosure

This project was done with help from an AI assistant (Claude Code, Anthropic). The author is responsible for every claim, number and file in the submission.

## What the assistant did

- Read and edited the code. Removed comments that restated the code, and fixed two label bugs and one legacy-AST operator bug (see `FAILURE_LOG.md`).

## What the author did and decided

- Wrote `evaluate.py` (leave-one-contract-out evaluation and baselines), the three notebooks, the figure code, and the documentation files in this repository.
- Ran the pipeline, checked the logs and the CSVs, and wrote the manuscript and slides drafts.
- Searched for and checked the references in `LITERATURE_MATRIX.md`.
- Conceived the research question, the choice of baselines, and the decision to report leave-one-contract-out results as the main evaluation.
- Checked the gold line labels by reading each contract.
- Verified that every reported number was taken directly from the output files in `results/` and `results/logs/`.

## What was not used

- No dataset other than the six demo contracts in this repository was downloaded or used.
- Reference details were checked against publisher or arXiv pages before use (see `LITERATURE_MATRIX.md`).
