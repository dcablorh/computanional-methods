# GRAPH-REPRESENTED SMART CONTRACT AUDITING: Plain-English Version

**Project Title:** Graph-Based Smart Contract Security Checker

### What We Are Trying to Achieve

Smart contracts control large amounts of money on blockchains like Ethereum. Once they are deployed, they cannot be changed. If there is a bug (especially a complex one like Reentrancy), attackers can steal the money permanently.

Current tools that check for these bugs are slow, give too many false alarms, and often miss problems that involve how different parts of the code interact.

**Our goal** is to build a tool that finds these dangerous bugs **before** the smart contract is deployed. We turn the code into graphs (like flowcharts) and use Graph Neural Networks (AI that understands connections) to spot the problems.

### 1. Introduction (Simple Version)

Smart contracts are computer programs that automatically run agreements on the blockchain. They hold billions of dollars. Because they cannot be fixed after launch, even one small mistake can cause large losses.

Old checking tools look at the code line by line or try every possible path. This is slow and often wrong. They struggle with bugs that depend on how different functions call each other or change data.

We treat the smart contract as a connected flowchart instead of plain text. We build graphs from the code and train Graph Neural Networks on them, so the tool can detect hard-to-find bugs and show which lines are dangerous.

### 2. Why This Matters (Background & Problem)

Ethereum smart contracts are written in a language called Solidity. Once deployed, anyone can see and interact with them, but no one can change the code.

Famous disasters:

- **The DAO attack (2016):** Attackers used a Reentrancy bug to steal tens of millions of dollars by repeatedly calling a withdraw function before the balance was updated.

- **Parity Wallet hacks:** Bugs in ownership and initialization functions locked or stole large amounts of money.

Existing tools (Oyente, Mythril, Securify, SmartCheck, etc.) have known problems:

- Too many false alarms
- Slow
- Hard to use in everyday development
- Miss complex multi-function bugs

Machine learning, especially Graph Neural Networks, can learn patterns from examples instead of relying only on fixed rules.

### 3. Why Graphs and Graph Neural Networks?

Most bugs are not simple typing mistakes. They are problems in the **structure** of the code: how functions call each other, how data flows, and the order of operations.

We turn the smart contract into three kinds of graphs and combine them:

- **Abstract Syntax Tree (AST):** shows the grammar and structure of the code
- **Control Flow Graph (CFG):** shows the possible paths the program can take
- **Program Dependency Graph (PDG):** shows how data moves and depends on other parts

A Graph Neural Network can "walk" through these connections and learn which patterns are dangerous (for example, an external call that happens before a balance is updated).

### 4. Our Method

1. **Build the graphs:** Turn Solidity code into one combined graph using AST + CFG + PDG.
2. **Clean and focus the graphs (program slicing):** Remove unimportant parts (comments, unused code, libraries) so the model only looks at security-related pieces.
3. **Train Graph Neural Networks:** The prototype uses a Graph Attention Network (GAT), which pays special attention to the most important connections. Temporal Message Propagation and Multi-Relational Nested GCN are planned but not yet implemented.
4. **Pinpoint the problem:** Instead of only saying "this contract is dangerous," the tool marks the lines that most likely cause the bug.

### 5. What Bugs We Focus On

| Vulnerability | Simple explanation | How graphs help detect it |
|---|---|---|
| Reentrancy | External call happens before balance is updated | Finds a cycle where the call comes before the state change |
| Timestamp Dependency | Code trusts `block.timestamp` for important decisions (miners can influence it) | Detects a data dependency from the timestamp to a decision branch |
| Arithmetic Errors | Numbers overflow or underflow without proper safety checks | Finds math operations without boundary checks |

### 6. How We Will Test It

The prototype has so far been run only on six small demo contracts that we wrote (one vulnerable and one safe contract per class). The model was trained and checked on those same six, so the results show that the pipeline works end to end, not how well it finds bugs in unseen code.

Next, we will train and test on well-known public datasets:

- SmartBugs Wild (real contracts from Ethereum)
- SolidiFI-Benchmark (contracts with injected bugs)
- SBcurated (manually checked vulnerable contracts)

We will measure precision, recall, and F1-score, and compare against previous GNN papers and traditional tools.

### 7. Building on Previous Good Work

We aim to improve on recent results, for example:

- Cai et al. (2023) reported about 89% precision and 93% recall using sliced joint graphs with BiGGNN.
- MANDO-HGT and VulDet also showed that heterogeneous graphs and attention work well.
- Our system aims to combine these ideas and add line-level localization.

### 8. Challenges

- There are many more safe contracts than vulnerable ones (class imbalance). Not yet addressed.
- AI models are often "black boxes". Our tool shows per-line probabilities, which indicate where the model looks, but this is not a full explanation of its reasoning.
- Solidity and compilers keep changing. The tool handles both the legacy (pre-0.8) and the modern AST format, tested on Solidity 0.7.6 and 0.8.20.

### 9. What We Have Built and What the Results Show

We built a working prototype of the full pipeline:

1. **Two AST formats:** The parser handles older Solidity (`0.7.x`) and modern Solidity (`0.8.x`).
2. **Noise reduction:** The slicer shrinks each contract's graph by 24% to 92%, depending on how many security-relevant statements it contains. The largest reduction was on the Arithmetic contract (73 nodes down to 6).
3. **Detection on the demo set** (these contracts were also used for training, so this is not a measure of accuracy on new code):
   - **Reentrancy:** 99.10% on the vulnerable contract, 0.28% on the safe one.
   - **Timestamp Dependency:** 99.83% on the vulnerable contract, 0.07% on the safe one.
   - **Arithmetic Error:** 99.73% on the vulnerable contract, 0.26% on the safe one.
4. **Line localization:** For `ReentrancyVulnerable.sol`, the tool flags **Line 15** (the external call) and **Line 16** (the result check). For the Timestamp and Arithmetic contracts, it flags the contract but does not localize a line.

The next step is to evaluate on the public datasets with a held-out split, as described in Section 6 of the academic version.
