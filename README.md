# Graph-Based Smart Contract Security Checker

A prototype that audits Solidity contracts for three vulnerability classes (Reentrancy, Timestamp Dependency, Arithmetic Error). It compiles the contract, builds an AST + CFG + PDG graph, slices the graph around security-relevant statements, and runs a Graph Attention Network (GAT) that gives a contract-level verdict and per-line localization. The accompanying paper is [reseach.md](reseach.md).

## Requirements

- Python 3.10 or newer (tested with Python 3.13)
- Internet access on first run, so that `py-solc-x` can download the Solidity compilers it needs (`0.7.6` and `0.8.20` are used by the demo contracts)

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

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
| `demo_contracts/` | Six demo contracts: a vulnerable and a safe version of each class |
| `model.pth` | Trained weights used for the results in the paper |

## Audit a contract

```bash
python auditor.py --contract demo_contracts/ReentrancyVulnerable.sol
```

The output shows the confidence for each class, and for each flagged class the lines that the model localizes. Add `--visualize` to save a graph image such as `ReentrancyVulnerable_audit.png` (flagged nodes in red). Use `--model path/to/weights.pth` to load other weights.

Expected output for the vulnerable Reentrancy contract, using the committed `model.pth`:

```
[Reentrancy] Confidence: 99.10%
  >>> ALERT: Potential Reentrancy vulnerability detected!
  >>> Vulnerable Code Localization (GNN Node Saliency):
      [Line 015]: (bool sent, ) = msg.sender.call{value: bal}("")
      [Line 016]: require(sent, "Failed to send")
```

## Train the model

```bash
python trainer.py
```

This rebuilds the dataset from `demo_contracts/`, trains for 100 epochs, overwrites `model.pth`, and prints a verification pass on the same contracts. The seed is fixed, so repeated runs give the same weights. Those weights differ from the committed `model.pth`, which was trained without a fixed seed, so retraining will change the confidence values reported in the paper.

## Limitations

- The model is trained and checked on the same six demo contracts. The printed verification pass is not a held-out evaluation.
- Localization was only observed for the Reentrancy contract. For the Timestamp and Arithmetic contracts, the tool flags the class but reports that it cannot localize a line.
- Node features use keyword matching (for example `"now"` and `"send"`), which also matches unrelated text such as `msg.sender`.
- Only the GAT variant is implemented. Compiler versions `0.4.x` to `0.6.x` are mapped but untested.
