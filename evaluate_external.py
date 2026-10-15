"""
Train on the six demo contracts, then score six new contracts in test_contracts/.

The test contracts were not used for training, and they differ from the demo set
in names, layout and compiler version. Run from the repository root:

    python evaluate_external.py
"""
import os
import csv
import json
import numpy as np
import torch

from parser.compiler import compile_contract
from parser.graph_builder import build_graph_from_ast
from slicing.slicer import find_interest_points, slice_graph
from data_loader import load_dataset, convert_graph_to_tensors
from trainer import fit_model, VULN_NAMES
from evaluate import binary_metrics, graph_feature_vector, SEEDS, EPOCHS, LR, GRAPH_THRESH, NODE_THRESH, SINK_KEYS
from sklearn.linear_model import LogisticRegression

TEST_DIR = "./test_contracts"
OUT_DIR = "results/external_test"

TEST_LABELS = {
    "VaultVulnerable.sol":  {"vuln_class": 0, "vulnerable_lines": [14, 15]},
    "VaultSafe.sol":        {"vuln_class": 0, "vulnerable_lines": []},
    "RaffleVulnerable.sol": {"vuln_class": 1, "vulnerable_lines": [13]},
    "RaffleSafe.sol":       {"vuln_class": 1, "vulnerable_lines": []},
    "LedgerVulnerable.sol": {"vuln_class": 2, "vulnerable_lines": [12]},
    "LedgerSafe.sol":       {"vuln_class": 2, "vulnerable_lines": []},
}


def build_test_items():
    items = []
    for file_name, info in TEST_LABELS.items():
        path = os.path.join(TEST_DIR, file_name)
        ast = compile_contract(path)
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        G = build_graph_from_ast(ast, source)
        sinks = find_interest_points(G)
        seeds = sinks["external_calls"] + sinks["timestamp_refs"] + sinks["arithmetic_ops"]
        if not seeds:
            seeds = [n for n, d in G.nodes(data=True) if d.get("node_type") in ("FunctionCall", "VariableDeclaration")]
        sliced = slice_graph(G, seeds, steps=3)
        tensors = convert_graph_to_tensors(sliced, vuln_class=info["vuln_class"],
                                           vulnerable_lines=info["vulnerable_lines"])
        tensors["file_name"] = file_name
        tensors["graph"] = sliced
        tensors["full_graph"] = G
        items.append(tensors)
    return items


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    train = load_dataset("./demo_contracts")
    test = build_test_items()

    print("Test contracts: slicing and line check")
    for item in test:
        g = item["graph"]
        lines = sorted({g.nodes[n].get("line", 0) for n in g.nodes()})
        print(f"  {item['file_name']:24s} sliced nodes={len(g.nodes()):3d} "
              f"truth={item['graph_y'].tolist()} gold_lines={TEST_LABELS[item['file_name']]['vulnerable_lines']}")

    gat_rows, loc_rows = [], []
    for seed in SEEDS:
        model = fit_model(train, epochs=EPOCHS, lr=LR, seed=seed, verbose=False)
        with torch.no_grad():
            for item in test:
                node_logits, graph_logits = model(item["x"], item["edge_index"])
                gp = torch.sigmoid(graph_logits).numpy()
                npb = torch.sigmoid(node_logits).numpy()
                for c in range(3):
                    gat_rows.append({"seed": seed, "contract": item["file_name"], "class": VULN_NAMES[c],
                                     "truth": int(item["graph_y"][c].item()), "prob": float(gp[c]),
                                     "pred": int(gp[c] > GRAPH_THRESH)})
                info = TEST_LABELS[item["file_name"]]
                if info["vulnerable_lines"]:
                    c = info["vuln_class"]
                    predicted = set()
                    for idx, node_id in enumerate(item["node_list"]):
                        line = item["graph"].nodes[node_id].get("line", 0)
                        if line > 0 and npb[idx, c] > NODE_THRESH:
                            predicted.add(line)
                    gold = set(info["vulnerable_lines"])
                    hit = gold & predicted
                    loc_rows.append({"seed": seed, "contract": item["file_name"],
                                     "gold_lines": " ".join(map(str, sorted(gold))),
                                     "predicted_lines": " ".join(map(str, sorted(predicted))),
                                     "precision": len(hit) / len(predicted) if predicted else 0.0,
                                     "recall": len(hit) / len(gold)})

    sink_rows = []
    for item in test:
        sinks = find_interest_points(item["full_graph"])
        for c in range(3):
            sink_rows.append({"contract": item["file_name"], "class": VULN_NAMES[c],
                              "truth": int(item["graph_y"][c].item()),
                              "pred": int(len(sinks[SINK_KEYS[c]]) > 0)})

    X_train = np.stack([graph_feature_vector(d) for d in train])
    logi_rows = []
    for item in test:
        x = graph_feature_vector(item).reshape(1, -1)
        for c in range(3):
            y = np.array([int(d["graph_y"][c].item()) for d in train])
            if len(set(y)) < 2:
                prob = float(y[0])
            else:
                clf = LogisticRegression(max_iter=1000).fit(X_train, y)
                prob = float(clf.predict_proba(x)[0, 1])
            logi_rows.append({"contract": item["file_name"], "class": VULN_NAMES[c],
                              "truth": int(item["graph_y"][c].item()), "prob": prob,
                              "pred": int(prob > GRAPH_THRESH)})

    per_seed = {s: binary_metrics([r["truth"] for r in gat_rows if r["seed"] == s],
                                  [r["pred"] for r in gat_rows if r["seed"] == s]) for s in SEEDS}
    keys = ["precision", "recall", "f1", "accuracy"]
    gat = {k: float(np.mean([per_seed[s][k] for s in SEEDS])) for k in keys}
    gat_std = {k: float(np.std([per_seed[s][k] for s in SEEDS])) for k in keys}
    sink = binary_metrics([r["truth"] for r in sink_rows], [r["pred"] for r in sink_rows])
    logi = binary_metrics([r["truth"] for r in logi_rows], [r["pred"] for r in logi_rows])

    def write_csv(name, rows):
        with open(os.path.join(OUT_DIR, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    write_csv("gat_decisions.csv", gat_rows)
    write_csv("sink_decisions.csv", sink_rows)
    write_csv("logistic_decisions.csv", logi_rows)
    write_csv("localization.csv", loc_rows)

    loc_summary = {"mean_precision": float(np.mean([r["precision"] for r in loc_rows])),
                   "mean_recall": float(np.mean([r["recall"] for r in loc_rows])),
                   "rows": len(loc_rows)}
    metrics = {"gat_mean": gat, "gat_std": gat_std, "sink_rule": sink, "logistic": logi,
               "gat_localization": loc_summary,
               "decisions_per_method": len(sink_rows), "positives": int(sum(r["truth"] for r in sink_rows))}
    with open(os.path.join(OUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\nExternal test: 18 decisions, 3 positive")
    print(f"  GAT (mean of 5 seeds)   P={gat['precision']:.3f} R={gat['recall']:.3f} "
          f"F1={gat['f1']:.3f} Acc={gat['accuracy']:.3f}")
    print(f"  Sink-presence rule      P={sink['precision']:.3f} R={sink['recall']:.3f} "
          f"F1={sink['f1']:.3f} Acc={sink['accuracy']:.3f}")
    print(f"  Logistic regression     P={logi['precision']:.3f} R={logi['recall']:.3f} "
          f"F1={logi['f1']:.3f} Acc={logi['accuracy']:.3f}")
    print(f"  GAT localization: mean precision={loc_summary['mean_precision']:.3f}, "
          f"mean recall={loc_summary['mean_recall']:.3f}, n={loc_summary['rows']}")
    print("\nGAT mean probability per decision:")
    for c in ["VaultVulnerable.sol", "VaultSafe.sol", "RaffleVulnerable.sol", "RaffleSafe.sol",
              "LedgerVulnerable.sol", "LedgerSafe.sol"]:
        vals = [f"{r['prob']:.3f}" for cls in VULN_NAMES
                for r in gat_rows if r["contract"] == c and r["class"] == cls and r["seed"] == SEEDS[0]]
        print(f"  {c:24s} {vals}")


if __name__ == "__main__":
    main()
