# Reproducibility checklist

Tick each item after running it on a clean clone.

## Environment

- [x] Python 3.13.3 (Windows 10 Pro 10.0.21996)
- [x] torch 2.13.0+cpu, networkx 3.6.1, matplotlib 3.11.1, scikit-learn 1.9.0, py-solc-x 2.0.5, nbconvert 7.17.1, nbformat 5.10.4, ipykernel 7.1.0
- [x] Dependencies are listed in `requirements.txt` (versions above are the ones used; newer versions may change floating-point results)
- [x] First run downloads solc 0.7.6 and 0.8.20 through py-solc-x (needs internet once)

## Determinism

- [x] Training is seeded (`trainer.py`, seed 42). Two runs on this machine gave identical per-epoch and per-contract logs.
- [x] LOCO uses seeds 0 to 4 (`evaluate.py`).
- [x] Logistic regression is deterministic (lbfgs).
- [ ] Not tested on GPU or other operating systems. Results may differ in the last decimal places.

## Commands and expected outputs

| Step | Command | Output checked |
|---|---|---|
| Audit one contract | `python auditor.py --contract demo_contracts/ReentrancyVulnerable.sol` | Reentrancy 99.21%; lines 15 and 16 |
| Retrain | `python trainer.py` | Final loss 0.2870 at epoch 100; saves `model.pth` |
| Full evaluation | `python evaluate.py` | `results/metrics.json`; GAT LOCO recall 0.000; sink rule recall 1.000 |
| Notebooks | run `notebooks/01_reproduce_audit.ipynb` to `03_error_analysis.ipynb` in order | No error outputs (checked) |

- [x] Each command above was run and its output matches the table.
- [x] Committed outputs (`results/`, `figures/`) match the last run.

## Data and provenance

- [x] All inputs are in `demo_contracts/` (see `DATA_CARD.md`).
- [x] Labels were checked by reading each contract (see F1 in `FAILURE_LOG.md`).
- [x] No data was downloaded for the results.

## Failure and change tracking

- [x] Every defect that changed a result is in `FAILURE_LOG.md`.
- [x] Pre-fix logs are kept in `results/logs/before_fixes/`.

## Release

- [x] Submitted version is tagged `submission-v1` (see `README.md`, "Submitted version").
