# Literature matrix

Every entry below was checked with a search against the publisher, arXiv or conference page. Entries marked **arXiv** are cited through the preprint because the journal or conference version could not be confirmed. References that could not be verified were removed from the manuscript; see the last section.

| # | Reference | Source checked | What it contributes | Relation to this project |
|---|---|---|---|---|
| 1 | Veličković, Cucurull, Casanova, Romero, Liò, Bengio (2018). Graph Attention Networks. ICLR 2018. arXiv:1710.10903 | arXiv | Attention-weighted message passing over graph neighbourhoods | Architecture of the classifier (`model/gnn.py`) |
| 2 | Kipf & Welling (2017). Semi-Supervised Classification with Graph Convolutional Networks. ICLR 2017. arXiv:1609.02907 | arXiv + ICLR listing | Spectral-approximation GCN for node classification | Background for graph-based node classification; not implemented here |
| 3 | Zhuang, Liu, Qian, Liu, Wang, He (2020). Smart Contract Vulnerability Detection using Graph Neural Network. IJCAI-20, pp. 3283–3290. DOI 10.24963/ijcai.2020/454 | IJCAI proceedings | Function-level contract graph, elimination phase, temporal message propagation | Closest prior GNN approach for contracts; TMP variant not implemented |
| 4 | Liu, Fan, Feng, Wei (2023). Vulnerable Smart Contract Function Locating Based on Multi-Relational Nested GCN (MRN-GCN). arXiv:2306.04479 | arXiv | Function-level localization over a nested multi-relational contract graph | Motivates node-level localization; not implemented |
| 5 | Nguyen, Nguyen, Xie, Ahmadi, Kudenko, Doan, Jiang (2022). MANDO: Multi-Level Heterogeneous Graph Embeddings for Fine-Grained Detection of Smart Contract Vulnerabilities. arXiv:2208.13252 | arXiv | Heterogeneous contract graph with metapaths, fine-grained detection | Shows heterogeneous contract graphs are used at line/function level; not implemented |
| 6 | Durieux, Ferreira, Abreu, Cruz (2020). Empirical Review of Automated Analysis Tools on 47,587 Ethereum Smart Contracts. ICSE 2020, pp. 530–541. arXiv:1910.10601 | ICSE page + arXiv | Nine analysis tools on 47k+ contracts; low agreement between tools; high flag rate on real contracts | Motivates the need for a learned, lower-false-positive approach; source of the SmartBugs dataset family (not used here) |
| 7 | Ghaleb & Pattabiraman (2020). How Effective are Smart Contract Analysis Tools? Evaluating Smart Contract Static Analysis Tools Using Bug Injection. ISSTA 2020. arXiv:2005.11613 | ISSTA page + arXiv | SolidiFI: bug injection into contracts to measure tool recall | Candidate benchmark for future held-out evaluation (not used here) |
| 8 | Luu, Chu, Olickel, Saxena, Hobor (2016). Making Smart Contracts Smarter. CCS 2016. DOI 10.1145/2976749.2978309 | ACM DOI + ePrint 2016/633 | Oyente: symbolic execution on EVM bytecode; reports TheDAO bug | Classical symbolic-execution baseline family; discussed, not run |
| 9 | Tikhomirov et al. (2018). SmartCheck: Static Analysis of Ethereum Smart Contracts. WETSEB 2018, pp. 9–16 | Author postprint (ORBilu) | Extensible static checker for Solidity | Pattern-based checker family; discussed, not run |
| 10 | Feist, Grieco, Groce (2019). Slither: A Static Analysis Framework For Smart Contracts. WETSEB 2019. arXiv:1908.09878 | arXiv | Solidity to SSA IR (SlithIR) for analysis | Comparable IR-based static analyzer; discussed, not run |
| 11 | Sayeed, Marco-Gisbert, Caira (2020). Smart Contract: Attacks and Protections. IEEE Access 8, 24416–24427. DOI 10.1109/access.2020.2970495 | IEEE DOI + open-access record | Survey of attack categories; reports that tested detection tools still miss known vulnerabilities | Background for the three target vulnerability classes |
| 12 | Zheng, Xie, Dai, Chen, Chen, Weng, Imran (2020). An overview on smart contracts: Challenges, advances and platforms. FGCS 105, 475–491. arXiv:1912.10370 | Publisher listing + arXiv | General overview of smart contracts | Introduction background |
| 13 | De Baets, Suleiman, Chitizadeh, Razzak (2024). Vulnerability detection in smart contracts: A comprehensive survey. arXiv:2407.07922 | arXiv | Survey of machine-learning approaches to smart contract vulnerability detection | Places this work among learning-based detectors |

## Searched but not used

These references appeared in the earlier draft (git commit `2c09deb`). Searches did not confirm them, so they were removed from the manuscript:

- Cai et al. (2023), *Journal of Systems and Software*, "Combine sliced joint graph with graph neural networks…": no record found.
- Luo & Luo (2023), "VulDet", AIBT: no record found.
- Yu et al. (2021), "DeeSCVHunter", IJCNN: no record found. The closest match, SCVHunter, is an ICSE 2024 paper by different authors.
- Zhang et al. (2022), "backward Bayesian active learning", ACNS workshops: no record found.
- Han et al. (2022), ICFTIC: no record found.
- Yang et al. (2022), ISSSR: a citing paper gives the DOI 10.1109/ISSSR56778.2022.00032, but the author list and abstract were not confirmed from the publisher page.
- MANDO-HGT (Nguyen et al., MSR 2023): the paper exists (DOI 10.1109/MSR59073.2023.00052), but the full author list could not be retrieved, so it is not cited.
- Nguyen et al. (2022), MANDO at DSAA: the arXiv version (row 5) was verified. The DSAA venue was not confirmed, so the arXiv version is cited.
- Liu et al. (2023) in *Journal of Systems and Software*: the arXiv version (row 4) was verified. The journal venue was not confirmed, so the arXiv version is cited.
