# Model card: GAT contract auditor

## Model details

- **Type:** Graph Attention Network (two layers, single attention head) with two linear heads: one for nodes and one for graph-level predictions. Outputs are sigmoids over 3 classes (Reentrancy, Timestamp dependency, Arithmetic error).
- **Implementation:** `model/gnn.py` (`GATLayer`, `SmartContractGNN`), in plain PyTorch.
- **Input:** a 25-dimensional feature vector per node of the sliced contract graph. Features: a 21-way one-hot AST node type and four keyword flags (call, timestamp, arithmetic, state write).
- **Graph:** the multi-relational graph from `parser/graph_builder.py` (AST, CFG and data-flow edges), sliced by `slicing/slicer.py` (3 steps).
- **Weights:** `model.pth` (about 28 KB).

## Training

| Setting | Value |
|---|---|
| Training data | the six demo contracts (`demo_contracts/`) |
| Epochs | 100, one optimizer step per graph |
| Optimizer | Adam, lr 0.005, weight decay 1e-4 |
| Loss | BCE-with-logits on graph level, plus 2 × the same loss on node level |
| Seed | 42 for `model.pth` (set in `trainer.py`) |
| Hidden size | 64 |
| Dropout | 0.1 in both GAT layers |

The committed `model.pth` was produced by `python trainer.py` on the corrected labels (see `FAILURE_LOG.md`, F1 and F2).

## Decision rules

- Class flagged when the graph-level probability is above 0.5.
- Lines localized when a node's probability for the flagged class is above 0.3.
  Both thresholds were set by hand and were not tuned on held-out data.

## Evaluation

Results are in `results/metrics.json` and `notebooks/02_loco_evaluation.ipynb`.

| Evaluation | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|
| Trained and tested on the same six contracts (saved weights, 18 decisions) | 1.000 | 1.000 | 1.000 | 1.000 |
| Leave-one-contract-out, mean of 5 seeds (18 decisions) | 0.000 | 0.000 | 0.000 | 0.778 (identical across seeds) |

The first row measures how well the model fits its training data. The second row is the number that matters for unseen contracts: the model does not flag any held-out vulnerable contract. Localization under leave-one-out is 0 for all 15 vulnerable-contract evaluations (3 contracts × 5 seeds).

## Intended use

- Research demonstration of the pipeline.
- Teaching how graph features and node-level heads are wired together.

## Out-of-scope use

- Auditing real contracts before deployment. The model does not generalize from the training set (leave-one-out recall = 0).
- Reporting a vulnerability as confirmed. Output is a classifier score.

## Caveats

- Confidences are sigmoid outputs and are not calibrated probabilities.
- Keyword features match substrings such as `"now"` and `"send"` anywhere in a node's text.
- Compiler coverage: 0.7.6 (legacy AST) and 0.8.20 (compact AST) were exercised. 0.4.x to 0.6.x are mapped but untested.
- Localization worked only for the Timestamp and Reentrancy contracts in-sample, and not at all under leave-one-out.
