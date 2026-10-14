---
title: "Graph-Represented Smart Contract Auditing"
author: "[Author Name(s)]"
date: "[Date]"
---

# Abstract

Smart contracts on public blockchains such as Ethereum are immutable once deployed, so a single code-level flaw can lead to irreversible financial loss. Existing analysis tools rely on hand-written rules or symbolic execution, which tend to produce many false positives and miss vulnerabilities that span several functions. This paper presents a pre-deployment auditing prototype for Solidity that represents each contract as a multi-relational graph (Abstract Syntax Tree, Control Flow Graph and Program Dependency Graph), slices the graph around security-relevant statements, and classifies it with a Graph Attention Network (GAT) that produces both a contract-level and a node-level prediction. The prototype covers three vulnerability classes (Reentrancy, Timestamp Dependency and Arithmetic Error). It is trained and evaluated on six small demo contracts. On this set, the model separates vulnerable from safe contracts and localizes the Reentrancy flaw to its external call. These results are a functional check of the pipeline rather than evidence of generalization; Section 8 describes the limitations and the evaluation still required.

**Keywords:** smart contracts; Solidity; graph neural networks; graph attention network; program slicing; vulnerability detection

# 1. Introduction

Smart contracts are autonomous, self-executing digital agreements that govern billions of dollars in digital assets on decentralized ledger networks such as Ethereum. Because these agreements are immutable once deployed, any code-level vulnerability represents a permanent exploit vector that can cause immediate and irreversible financial loss. Traditional vulnerability scanners rely on rigid, manually written rule sets and symbolic execution engines that are computationally slow, produce excessive false positives, and fail to track complex multi-function logic. This research presents a pre-deployment vulnerability detection pipeline built on Graph Neural Networks (GNNs). By parsing smart contract source code into multi-relational semantic graphs that integrate Abstract Syntax Trees (ASTs), Control Flow Graphs (CFGs) and Program Dependency Graphs (PDGs), the system treats contract logic as an execution flowchart rather than as plain text. The approach targets topological vulnerabilities, such as Reentrancy, that continue to affect the decentralized ecosystem.

# 2. Research Background and Problem Statement

Ethereum smart contracts are primarily written in Solidity, a high-level, Turing-complete language. Although Solidity gives developers considerable architectural flexibility, it also introduces subtle execution behaviors that lead to serious security exploits (Zheng et al., 2020). When a contract is compiled and deployed to the Ethereum Virtual Machine (EVM), its state becomes public and cannot be altered. If an exploit is present, malicious actors can drain funds before developers can apply manual mitigations.

Two well-known incidents illustrate the problem:

- **The DAO exploit (2016).** A recursive-call flaw (Reentrancy) was used to repeatedly withdraw Ether before the contract's internal balance mapping was updated, draining millions of dollars within hours (Sayeed et al., 2020).
- **The Parity multisig wallet incidents.** Uninitialized state variables and public initialization functions allowed attackers to call administrative functions and take ownership of wallets, locking up large amounts of digital assets (Sayeed et al., 2020).

Automated scanning tools such as Oyente, Mythril, Securify and SmartCheck use symbolic execution, taint analysis or lexical pattern matching to explore execution paths (Durieux et al., 2020). These tools have several limitations: (1) they often fail to combine high accuracy with scalability, and they generate many false positives; (2) they lack a standardized lexicon and unified dataset, which makes comparative benchmarks inconsistent; and (3) they are slow, which makes them hard to use in real-time developer compilation pipelines (Durieux et al., 2020). Machine learning offers a data-driven alternative that is not bound by fixed rules.

# 3. The Flowchart Paradigm: Why Graph Neural Networks?

In smart contract security, a vulnerability is rarely a simple typographical error that a sequential text model (such as an RNN or LSTM) can catch. Vulnerabilities are usually topological properties involving inter-function calls, dependencies between state variables, and modified execution loops. Graph Neural Networks (GNNs) represent a major shift in learning-based vulnerability detection. In a survey of the peer-reviewed machine learning literature in this domain, GNN-based methods formed the largest single model group (De Baets et al., 2024).

GNNs suit smart contract auditing because they transform raw code into a graph. The network views a contract as a flowchart-like structure of nodes and edges, where nodes represent statements, variables or functions, and edges represent control flow, data dependency or hierarchical structure. Message passing along these edges lets the network learn relationships that flat token sequences do not expose, which matters for the non-linear execution flow of Turing-complete programs.

# 4. Proposed Research Methodology

The pipeline consists of four phases: multi-relational graph construction, program slicing, GNN learning, and node-level localization. Phases 1, 2 and 4, and one GNN variant (GAT), are implemented in the prototype described in Section 7. The other two GNN variants are planned comparisons.

## 4.1 Phase 1: Multi-Relational Graph Representation

The pipeline parses Solidity source code into three representation layers and merges them into one heterogeneous contract graph (Cai et al., 2023; Nguyen et al., 2022):

- **Abstract Syntax Tree (AST):** captures the grammatical structure, variable declarations and nesting of the contract (Yang et al., 2022).
- **Control Flow Graph (CFG):** represents execution paths, loop boundaries, conditional branches and external function calls (Han et al., 2022).
- **Program Dependency Graph (PDG):** maps data-flow dependencies, showing how variables are assigned, passed and modified across functions (Cai et al., 2023).

## 4.2 Phase 2: Joint Graph Slicing and Noise Reduction

To limit over-smoothing in deep networks and to remove redundant code such as comments, imports and unrelated library calls, the pipeline applies program slicing (Cai et al., 2023). Slicing starts from security interest points: external execution calls (`.call`, `transfer`, `send`), references to `block.timestamp`, and arithmetic operators (`+`, `-`, `*`, `/`). From each point it follows control-flow and data-flow edges up to three steps backward and forward, and then keeps the enclosing AST ancestors. The result is a smaller sliced joint graph. Slice-based inputs have also been used by DeeSCVHunter, which builds "vulnerability candidate slices" for deep learning models (Yu et al., 2021). In our prototype the reduction ranges from 6% to 92% of nodes depending on the contract (Section 7.2). That the slice discards no security-relevant context has not been formally verified, and it is an assumption of this work.

## 4.3 Phase 3: GNN Learning and Attention Propagation

The sliced graph is processed by a graph neural network. The literature suggests three propagation frameworks, and we plan to compare them:

- **Graph Attention Networks (GAT):** use multi-head self-attention to assign dynamic weights to important edges (Luo & Luo, 2023). In a reentrancy flow, attention can assign higher weight to the path from the external transfer to the subsequent balance update. *Implemented in the prototype (single attention head, two layers).*
- **Temporal Message Propagation (TMP):** tracks sequential changes in variables and states across graph edges over execution steps, capturing stateful vulnerabilities (Zhuang et al., 2020). *Planned; not implemented.*
- **Multi-Relational Nested GCN (MRN-GCN):** processes nested function execution scopes to learn structural dependencies across contract boundaries (Liu et al., 2023). *Planned; not implemented.*

## 4.4 Phase 4: High-Precision Localization

A simple GNN performs binary classification, declaring a contract "vulnerable" or "safe". Our model also predicts a probability for each node, so it can point to the lines responsible for a flagged vulnerability (Nguyen et al., 2022). This granularity matters to developers, because it turns a generic alert into an actionable fix.

# 5. Target Vulnerabilities and Experimental Benchmarking

The target vulnerabilities are among the most common and financially damaging smart contract vulnerabilities (De Baets et al., 2024). Table 1 summarizes how each is detected by the graph-based approach.

**Table 1.** Target vulnerability classes and graph-based detection patterns.

| Vulnerability Category | Core Exploit Mechanism | Graph-Based Detection Pattern |
|---|---|---|
| Reentrancy | An external contract call occurs before the internal state balance is updated, enabling recursive drain loops. | Locates a control-flow cycle containing an external call node that executes before a data-flow state-modification node. |
| Timestamp Dependency | Critical contract logic or authorization relies on `block.timestamp`, which miners can influence. | Triggers when the GNN detects a data-dependency edge between a `block.timestamp` node and a conditional execution branch. |
| Arithmetic Error | Integer overflow or underflow wraps variables back to zero or maximum values because no standard SafeMath-style check is applied. | Maps data-flow edges of arithmetic operations that lack boundary constraints or library safeguards. |

The planned evaluation uses three public datasets: (1) SmartBugs Wild, a collection of real deployed Ethereum contracts (Durieux et al., 2020); (2) SolidiFI-Benchmark, a bug-injection benchmark for systematic testing of analysis tools (Ghaleb & Pattabiraman, 2020); and (3) the SmartBugs Curated (SBcurated) dataset of manually checked vulnerable contracts (Durieux et al., 2020). **None of these datasets has been used yet.** The results in Section 7 come from six demo contracts written for this prototype (`demo_contracts/`). Precision, recall and F1-score on the public datasets, and comparison with previous GNN papers and traditional tools, remain future work.

# 6. Discussion of GNN Model Variants in the Literature

The following recent GNN papers are the main points of comparison for our design:

- **Cai et al. (2023)** apply a sliced joint graph representation to graph neural networks for smart contract vulnerability detection. Our slicing step follows the same idea.
- **MANDO-HGT (Nguyen et al., 2023)** uses heterogeneous graph transformers over control-flow and function-call structures. It does not require manually defined vulnerability patterns.
- **VulDet (Luo & Luo, 2023)** applies graph attention networks to smart contract vulnerability detection.

# 7. Empirical Prototype Implementation and Results

We built an end-to-end prototype that performs Solidity compilation, dual-format AST parsing, graph construction, program slicing and GAT inference in PyTorch. The code is organized as `parser/` (compilation and graph construction), `slicing/` (interest points and slicing), `model/` (GAT model), `data_loader.py`, `trainer.py` and `auditor.py`. All numbers in this section were reproduced by running `auditor.py` against the saved weights in `model.pth`.

## 7.1 Dual-Format AST Compatibility

Compiler version divergence is a known challenge in smart contract machine learning research. Solidity versions before `0.8.0` (for example `0.7.6`) emit a **Legacy AST**, which stores node types in a `name` key and nests children in flat `children` arrays. Versions `0.8.0` and later emit a **Compact AST**, which stores node types in `nodeType` and uses explicit named keys. The pipeline includes a normalization layer that extracts AST, CFG and PDG edges from both formats. The version selector maps pragmas to the compilers `0.4.25`, `0.5.17`, `0.6.12`, `0.7.6` and `0.8.20`. **Only `0.7.6` (Legacy AST) and `0.8.20` (Compact AST) were exercised in our experiments**. The legacy path was exercised by a single contract (`ArithmeticVulnerable.sol`). Support for `0.4.x` to `0.6.x` is implemented but untested.

## 7.2 Program Slicing and Noise Reduction

Forward and backward slicing around the security interest points reduces graph size. Table 2 lists the node counts for the six demo contracts.

**Table 2.** Graph size before and after slicing (3-step slice).

| Contract | Full graph (nodes) | Sliced graph (nodes) | Node reduction |
|---|---|---|---|
| ReentrancyVulnerable.sol | 59 | 23 | 61.0% |
| ReentrancySafe.sol | 59 | 25 | 57.6% |
| TimestampVulnerable.sol | 26 | 13 | 50.0% |
| TimestampSafe.sol | 25 | 19 | 24.0% |
| ArithmeticVulnerable.sol | 73 | 6 | 91.8% |
| ArithmeticSafe.sol | 73 | 20 | 72.6% |

The reduction depends on how many security sinks a contract contains. Contracts with few sinks shrink the most. The slice of `ArithmeticVulnerable.sol` keeps only 6 nodes, which leaves little context for the model (see Section 8).

## 7.3 GNN Detection Performance on the Demo Set

We trained the GAT (two layers, hidden dimension 64) for 100 epochs with Adam at learning rate 0.005 and weight decay 1e-4. The loss is `BCEWithLogitsLoss` at graph level plus twice the same loss at node level; the heavier node term encourages line-level localization. Table 3 shows the predictions of the saved model. **These six contracts were also used to train the model, so Table 3 measures how well the model fits its training data, not how it performs on unseen contracts.** A class is flagged when its graph-level probability exceeds 0.5.

**Table 3.** Graph-level predictions of the saved model on the six demo contracts.

| Contract | Target vulnerability | Ground truth | GNN flag | GNN confidence |
|---|---|---|---|---|
| ReentrancyVulnerable.sol | Reentrancy | Vulnerable | VULNERABLE | 99.10% |
| ReentrancySafe.sol | Reentrancy | Safe | SAFE | 0.28% |
| TimestampVulnerable.sol | Timestamp Dependency | Vulnerable | VULNERABLE | 99.83% |
| TimestampSafe.sol | Timestamp Dependency | Safe | SAFE | 0.07% |
| ArithmeticVulnerable.sol | Arithmetic Error | Vulnerable | VULNERABLE | 99.73% |
| ArithmeticSafe.sol | Arithmetic Error | Safe | SAFE | 0.26% |

Retraining changes the probabilities somewhat. In our runs, the Reentrancy confidence for `ReentrancyVulnerable.sol` was 97.73% for one unseeded retrain and 99.43% for a seeded retrain (`trainer.py` now fixes the seed), compared with 99.10% for the saved weights reported here. In the unseeded retrain, every contract's predicted label matched its ground truth.

With six contracts, the model can fit every label. This shows that the pipeline runs end to end and that the GAT can learn the labelled differences. It does not establish a detection rate or a false-positive rate, which require held-out contracts such as those in the public datasets listed in Section 5.

## 7.4 Node-Level Localization

Node-level probabilities let the auditor point to lines. For `ReentrancyVulnerable.sol`, the nodes whose Reentrancy probability exceeds 0.3 map to **Line 15** and **Line 16** (Figure 1):

```solidity
(bool sent, ) = msg.sender.call{value: bal}("");   // Line 15
require(sent, "Failed to send");                   // Line 16
```

Line 15 is the external call that executes before the balance is reset on line 18, and line 16 checks its result. The training labels (`data_loader.py`) mark the same two lines.

For the other two vulnerable contracts, the model flags the vulnerability at contract level but does not localize a line, because no node exceeds the 0.3 threshold, and the output reads "Unable to localize exact line". Localization is therefore demonstrated for one of the three classes.

The node values are per-node output probabilities from the classifier head. They are not gradient-based saliency maps or attention weights, and this paper does not describe them as such.

![Figure 1. Output of `auditor.py --visualize` for `ReentrancyVulnerable.sol`. Nodes flagged for the Reentrancy class (probability above 0.3) are shown in red; they correspond to Lines 15 and 16.](ReentrancyVulnerable_audit.png){width=90%}

# 8. Limitations and Open Challenges

The results above are a functional check, and the following limitations apply:

1. **Tiny dataset, with training and testing on the same contracts.** The model is trained on six contracts (one vulnerable and one safe contract per class) and evaluated on those same six. There is no held-out set, so Table 3 does not measure generalization.
2. **No baselines and no standard metrics.** Precision, recall and F1 are not computed on any dataset, and we have not compared against Oyente, Mythril, Securify, SmartCheck or previously published GNN models.
3. **Only one of the planned GNN variants is implemented.** TMP and MRN-GCN are described in Section 4.3 but have not been built.
4. **Feature extraction is heuristic.** Security flags are set by keyword matching, for example `"now"` and `"send"`. These substrings also match unrelated text such as `msg.sender` and `know`, which can add false signals. Changing the features requires retraining.
5. **Localization is limited and threshold-driven.** The 0.3 node threshold and the 0.5 graph threshold were chosen by hand. Localization succeeded only for the Reentrancy contract.
6. **Compiler coverage is narrow.** Legacy AST handling was tested on one contract, and versions `0.4.x` to `0.6.x` were not tested.
7. **Class imbalance and labelling cost are not addressed.** The demo set is balanced by construction. Real-world datasets contain far more safe contracts, and labelling vulnerabilities is expensive; active learning has been proposed to reduce this cost (Zhang et al., 2022). We have not implemented either mechanism.
8. **Slicing may discard context.** The slice of `ArithmeticVulnerable.sol` keeps only six nodes, and we have not shown that the removed nodes never matter.

# 9. Conclusion and Future Work

We built a working pre-deployment prototype that turns Solidity contracts into multi-relational graphs, slices them around security-relevant statements, and classifies them with a GAT that predicts contract-level and node-level vulnerabilities for three classes. On six demo contracts the pipeline reproduces the expected labels. For the Reentrancy contract it points to the external call and the result check on which the flaw depends.

Future work, in priority order: (1) evaluate on SmartBugs Wild, SolidiFI-Benchmark and SBcurated with a held-out split, reporting precision, recall and F1-score; (2) compare against Oyente, Mythril, Securify and SmartCheck on the same contracts; (3) implement and compare the TMP and MRN-GCN variants; (4) replace keyword-based features with parser-derived attributes; and (5) test compiler versions `0.4.x` to `0.6.x`.

# References

Cai, J., Li, B., Zhang, J., Sun, X., & Chen, B. (2023). Combine sliced joint graph with graph neural networks for smart contract vulnerability detection. *Journal of Systems and Software, 195*, Article 111550.

De Baets, C., Suleiman, B., Chitizadeh, A., & Razzak, I. (2024). *Vulnerability detection in smart contracts: A comprehensive survey* [Preprint]. arXiv:2407.07922.

Durieux, T., Ferreira, J. F., Abreu, R., & Cruz, P. (2020). Empirical review of automated analysis tools on 47,587 Ethereum smart contracts. In *Proceedings of the 42nd International Conference on Software Engineering (ICSE 2020)* (pp. 530–541). ACM/IEEE.

Ghaleb, A., & Pattabiraman, K. (2020). How effective are smart contract analysis tools? Evaluating smart contract static analysis tools using bug injection. In *Proceedings of the 29th ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA 2020)*. ACM.

Han, D., Li, Q., Zhang, L., & Xu, T. (2022). A smart contract vulnerability detection model based on graph neural networks. In *2022 4th International Conference on Frontiers Technology of Information and Computer (ICFTIC)* (pp. 834–837). IEEE.

Liu, H., Fan, Y., Feng, L., & Wei, Z. (2023). Vulnerable smart contract function locating based on multi-relational nested graph convolutional network. *Journal of Systems and Software, 204*, Article 111775.

Luo, F., & Luo, R. (2023). VulDet: Smart contract vulnerability detection based on graph attention networks. In *2023 2nd International Conference on Artificial Intelligence and Blockchain Technology (AIBT)* (pp. 88–92). IEEE.

Nguyen, H. H., Nguyen, N.-M., Xie, C., Ahmadi, Z., Kudenko, D., Doan, T.-N., & Jiang, L. (2022). MANDO: Multi-level heterogeneous graph embeddings for fine-grained detection of smart contract vulnerabilities. In *2022 IEEE 9th International Conference on Data Science and Advanced Analytics (DSAA)* (pp. 1–10). IEEE.

Nguyen, H. H., Nguyen, N.-M., Xie, C., Ahmadi, Z., Kudenko, D., Doan, T.-N., & Jiang, L. (2023). MANDO-HGT: Heterogeneous graph transformers for smart contract vulnerability detection. In *2023 IEEE/ACM 20th International Conference on Mining Software Repositories (MSR)* (pp. 334–346). IEEE.

Sayeed, S., Marco-Gisbert, H., & Caira, T. (2020). Smart contract: Attacks and protections. *IEEE Access, 8*, 24416–24427.

Yang, H., Zhang, J., Gu, X., & Cui, Z. (2022). Smart contract vulnerability detection based on abstract syntax tree. In *2022 8th International Symposium on System Security, Safety, and Reliability (ISSSR)* (pp. 169–170). IEEE.

Yu, X., Zhao, H., Hou, B., Ying, Z., & Wu, B. (2021). DeeSCVHunter: A deep learning-based framework for smart contract vulnerability detection. In *2021 International Joint Conference on Neural Networks (IJCNN)* (pp. 1–8). IEEE.

Zhang, J., Tu, L., Cai, J., Sun, X., Li, B., Chen, W., & Wang, Y. (2022). Vulnerability detection for smart contract via backward Bayesian active learning. In *Applied Cryptography and Network Security Workshops (ACNS 2022 Satellite Workshops)* (pp. 66–83). Springer.

Zheng, Z., Xie, S., Dai, H.-N., Chen, W., Chen, X., Weng, J., & Imran, M. (2020). An overview on smart contracts: Challenges, advances and platforms. *Future Generation Computer Systems, 105*, 475–491.

Zhuang, Y., Liu, Z., Qian, P., Liu, Q., Wang, X., & He, Q. (2020). Smart contract vulnerability detection using graph neural network. In *Proceedings of the Twenty-Ninth International Joint Conference on Artificial Intelligence (IJCAI-20)* (pp. 3283–3290). IJCAI.
