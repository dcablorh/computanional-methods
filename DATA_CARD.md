# Data card: demo contracts

## Summary

| Item | Value |
|---|---|
| Contents | 6 Solidity files in `demo_contracts/` |
| Authorship | Written for this project by the author |
| Origin | Hand-written, minimal contracts. Not copied from deployed code |
| Real-world data | None. No deployed contract, no user data, no personal data |
| Licence | MIT (matches the `SPDX-License-Identifier` line in each file) |
| Labels | One class per contract, set in `data_loader.py` (`DEMO_LABEL_INFO`) |

## Files and labels

| File | Compiler | Vulnerable class | Label | Vulnerable line(s) |
|---|---|---|---|---|
| `ReentrancyVulnerable.sol` | 0.8.x | Reentrancy | vulnerable | 15, 16 |
| `ReentrancySafe.sol` | 0.8.x | Reentrancy | safe | none |
| `TimestampVulnerable.sol` | 0.8.x | Timestamp dependency | vulnerable | 9 |
| `TimestampSafe.sol` | 0.8.x | Timestamp dependency | safe | none |
| `ArithmeticVulnerable.sol` | 0.7.6 | Arithmetic error | vulnerable | 12 |
| `ArithmeticSafe.sol` | 0.8.x | Arithmetic error | safe | none |

Line numbers were checked by reading each file. Two labels were wrong in an earlier version (see `FAILURE_LOG.md`, F1).

## Intended use

- Smoke-testing and reproducing the pipeline (compile, graph, slice, classify).
- Illustrating the three vulnerability patterns.

## Not intended for

- Estimating detection or false-positive rates on real contracts. Six contracts cannot support that.
- Training a general-purpose classifier.

## Known limitations

- **Size:** 6 contracts; 3 positive and 15 negative class decisions.
- **Balance:** each class has exactly one vulnerable and one safe contract, so the classes are balanced by construction. Real data is not.
- **Style:** the contracts are short and written to show one pattern each. They are not representative of production code.
- **Labels:** they are the author's annotations, not independent expert labels.

## External test set (`test_contracts/`)

Six further contracts written after the first results, used only for the external test (`evaluate_external.py`).

| File | Compiler | Vulnerable class | Label | Vulnerable line(s) |
|---|---|---|---|---|
| `VaultVulnerable.sol` | 0.8.19 | Reentrancy | vulnerable | 14, 15 |
| `VaultSafe.sol` | 0.8.19 | Reentrancy | safe | none |
| `RaffleVulnerable.sol` | 0.8.19 | Timestamp dependency | vulnerable | 13 |
| `RaffleSafe.sol` | 0.8.19 | Timestamp dependency | safe | none |
| `LedgerVulnerable.sol` | 0.7.6 | Arithmetic error (unchecked `-=`) | vulnerable | 12 |
| `LedgerSafe.sol` | 0.8.19 | Arithmetic error | safe | none |

- **Not independent:** the arithmetic fix (compound assignments, `FAILURE_LOG.md` F12) was made after `LedgerVulnerable.sol` was missed. The external result after the fix is therefore optimistic.
- Written by the author, so this set tests generalization across the author's own styles, not real deployed code.

## Planned datasets (not used)

The manuscript lists public datasets for future held-out evaluation: SmartBugs Wild and Curated (Durieux et al., 2020) and SolidiFI (Ghaleb & Pattabiraman, 2020). None has been downloaded or used. Downloading them needs a separate decision and was not done for this submission.
