# Failure log

Problems found while preparing this project, what they affected, and what was done. Results from before the fixes are kept under `results/logs/before_fixes/` so the change can be checked.

## Code defects

### F1. Training labels for two contracts pointed at the wrong lines

- **Found:** while checking the node labels used for training.
- **Cause:** `data_loader.py` listed `TimestampVulnerable.sol` line 10 (the line is `require(block.timestamp % 15 == 0)` on line 9; line 10 is `winner = msg.sender;`) and `ArithmeticVulnerable.sol` line 14 (a blank line; the overflow multiplication is on line 12).
- **Fix:** labels changed to lines 9 and 12. `ReentrancyVulnerable.sol` lines 15–16 were already correct.
- **Effect:** the Timestamp contract is now localized to line 9. Before the fix the auditor reported "Unable to localize exact line". The Arithmetic contract is still not localized. Before the fix, the Arithmetic node-level labels were empty, so the model had only graph-level supervision for that class.

### F2. Arithmetic operators were not read from legacy (solc 0.7.6) ASTs

- **Found:** the sink-presence baseline never flagged `ArithmeticVulnerable.sol`, which should have had a sink.
- **Cause:** `slicing/slicer.py` read `operator` from the top level of the AST node. Legacy ASTs store it under `attributes`. Only compact (0.8.x) ASTs were handled, so the solc 0.7.6 contract had zero arithmetic sinks.
- **Fix:** the lookup falls back to `attributes`.
- **Effect:** the arithmetic slice of `ArithmeticVulnerable.sol` grew from 6 to 8 nodes and from 7 to 9 edges. The sink baseline went from recall 0.667 (2/3) to recall 1.000 (3/3). The model was retrained with the corrected slice.

### F3. The reported retraining figures could not be reproduced from the repository

- **Found:** the earlier draft (`archive/reseach.md`) reported two retrain confidences (97.73% unseeded, 99.43% seeded) for `ReentrancyVulnerable.sol`. No log or script in the repository produced them.
- **Cause:** those runs were made by hand and were not saved.
- **Fix:** the figures were removed from the manuscript. Training now uses a fixed seed (`trainer.py` seeds before model creation), and the training output is saved (`results/logs/train.txt`).

### F4. Stale visualizations

- **Found:** during review, the `*_audit.png` images at the repository root were the ones committed earlier, made with the pre-fix weights.
- **Fix:** all three were regenerated with `auditor.py --visualize` against the current weights and are in `figures/`.

## Evaluation problems

### F5. The first LOCO run used stale code

- The first leave-one-contract-out run was made before F2 was fixed. Its sink-rule row (precision 0.333, recall 0.667) was superseded by the re-run after the fix (precision 0.429, recall 1.000). The notebooks were executed again after the fix; the outputs in the repository come from the final run.

### F6. The GAT does not detect held-out vulnerable contracts (negative result)

- Leave-one-contract-out recall is 0 for every seed (see `results/metrics.json`). This is a result, not a code defect. With one vulnerable and one safe contract per class, holding out the vulnerable contract leaves no positive example for its class.
- Logistic regression on pooled node features predicts "safe" for every decision. Its accuracy (0.833) comes from class imbalance.

### F7. Keyword features match unrelated text (known, not fixed)

- `"now"` matches inside words such as `know`, and `"send"` matches inside `msg.sender` (both noted in the README). This was not isolated by an ablation, so its effect on the errors above is unknown.

### F8. Localization fails outside the Reentrancy contract (known)

- Node probabilities for the Arithmetic contract stay below the 0.3 threshold in every run.

## Documentation and process errors

### F9. Unverifiable references

- The earlier draft cited six works that could not be found in any search (Cai 2023, Luo & Luo 2023, DeeSCVHunter 2021, Zhang 2022, Han 2022, Yang 2022). They were removed (`LITERATURE_MATRIX.md`). Two more could be found only partially (MANDO-HGT author list; the JSS version of MRN-GCN). They were replaced with the verified arXiv or DOI record, or dropped.

### F10. Stray task chip

- During the work, a placeholder background-task suggestion was created by mistake. It was withdrawn right away with `dismiss_task`. It did not start any session.

### F11. Claims in the README were out of date

- The README's expected output (confidence 99.10%) and paper figures came from the pre-fix weights. They were updated after the retrain.
