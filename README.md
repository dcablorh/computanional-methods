# Graph-Based Smart Contract Security Checker

A research prototype that audits Solidity contracts for three vulnerability classes (Reentrancy, Timestamp Dependency, Arithmetic Error). It compiles the contract, builds an AST + CFG + PDG graph, slices the graph around security-relevant statements, and classifies it with a Graph Attention Network (GAT) that produces a contract-level verdict and node-level localization.

**Author:** [Student Name], Student ID [Student ID]. The manuscript is `manuscript/FINAL_PROJECT_StudentID_FullName.pdf`; the slides are in `slides/`.

**Short version of the result:** the model fits its six training contracts perfectly, but under leave-one-contract-out it flags none of the held-out vulnerable contracts. A rule that flags any contract containing the relevant sink has higher recall. See `results/metrics.json` and `notebooks/02_loco_evaluation.ipynb`.

## Submitted version

The submitted version is the commit tagged `submission-v1`. To check out exactly that version: `git checkout submission-v1`.

## Requirements

- Python 3.10 or newer (tested with Python 3.13.3)
- Internet access on first run, so that `py-solc-x` can download the Solidity compilers it needs (`0.7.6` and `0.8.20`)

```bash
pip install -r requirements.txt
```

Notebooks additionally need Jupyter (`pip install nbconvert ipykernel`) if you want to re-execute them.

## Reproduce

Run from the repository root.

```bash
python auditor.py --contract demo_contracts/ReentrancyVulnerable.sol
python trainer.py
python evaluate.py
```

| Step | What it writes | Expected |
|---|---|---|
| `auditor.py` | console report | Reentrancy 99.21%; lines 015 and 016 flagged |
| `trainer.py` | `model.pth`, console log | final loss 0.2870 at epoch 100 |
| `evaluate.py` | `results/`, `figures/` | GAT leave-one-out recall 0.000; sink rule recall 1.000 |

Add `--visualize` to `auditor.py` to save `<name>_audit.png` in the current directory (copies of the three committed images are in `figures/`).

## Notebooks

| Notebook | Purpose |
|---|---|
| `notebooks/01_reproduce_audit.ipynb` | Audits all six demo contracts with the saved weights |
| `notebooks/02_loco_evaluation.ipynb` | Runs the leave-one-contract-out evaluation against two baselines and shows the tables and figures |
| `notebooks/03_error_analysis.ipynb` | Lists each error by method, and compares audit outputs before and after the label fix |

All three are executed and their outputs are saved in the files.

## Evidence

| Item | Location |
|---|---|
| Manuscript (PDF) | `manuscript/FINAL_PROJECT_StudentID_FullName.pdf` (source: `manuscript/manuscript.html`) |
| Slides (PDF) | `slides/` |
| Metrics (all numbers in the manuscript) | `results/metrics.json`, `results/*.csv` |
| Logs (training, audits, evaluation, notebook runs) | `results/logs/` |
| Pre-fix logs (for comparison) | `results/logs/before_fixes/` |
| Figures | `figures/` |
| Literature matrix (verified references) | `LITERATURE_MATRIX.md` |
| Data card | `DATA_CARD.md` |
| Model card | `MODEL_CARD.md` |
| Ethics statement | `ETHICS.md` |
| AI-use disclosure | `AI_USE.md` |
| Failure log | `FAILURE_LOG.md` |
| Reproducibility checklist | `REPRODUCIBILITY_CHECKLIST.md` |
| Earlier draft (superseded) | `archive/` |

## Project layout

| Path | Purpose |
|---|---|
| `parser/compiler.py` | Picks the solc version from the pragma and returns the AST |
| `parser/graph_builder.py` | Builds the multi-relational graph (AST, CFG and data-flow edges) |
| `slicing/slicer.py` | Finds security sinks and slices the graph around them |
| `model/gnn.py` | GAT layers and the `SmartContractGNN` model |
| `data_loader.py` | Converts the labelled demo contracts into tensors |
| `trainer.py` | Trains the model and writes `model.pth` |
| `auditor.py` | Audits a single contract with the trained model |
| `evaluate.py` | Leave-one-contract-out evaluation, baselines, figures |
| `demo_contracts/` | Six demo contracts: a vulnerable and a safe version of each class |
| `model.pth` | Trained weights (corrected labels; see `FAILURE_LOG.md`) |

## Limitations

- Six demo contracts, one vulnerable and one safe per class. There is no held-out set in the training sense; the leave-one-out evaluation holds out one contract at a time, which leaves no positive example for that class.
- Under leave-one-contract-out the GAT never flags a held-out vulnerable contract. The in-sample result does not show generalization.
- Node features use keyword matching (for example `"now"` and `"send"`), which also matches unrelated text such as `msg.sender`.
- Only the GAT variant is implemented. Compiler versions `0.4.x` to `0.6.x` are mapped but untested.
- The public datasets named in the manuscript (SmartBugs, SolidiFI) are not used. Using them requires a separate decision about downloading them.
