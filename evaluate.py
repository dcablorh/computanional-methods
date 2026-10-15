"""
Leave-one-contract-out (LOCO) evaluation of the GAT auditor against two baselines.

For each held-out demo contract the GAT is retrained on the other five and
asked for a verdict on the held-out contract. Results are written to results/
and figures/. Run from the repository root:

    python evaluate.py
"""
import os
import csv
import json
import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression

from data_loader import load_dataset, DEMO_LABEL_INFO
from trainer import fit_model, VULN_NAMES
from slicing.slicer import find_interest_points
from model.gnn import SmartContractGNN

SEEDS = [0, 1, 2, 3, 4]
EPOCHS = 100
LR = 0.005
GRAPH_THRESH = 0.5   # contract-level decision threshold
NODE_THRESH = 0.3    # node-level localization threshold
SINK_KEYS = ["external_calls", "timestamp_refs", "arithmetic_ops"]

RESULTS_DIR = "results"
FIGURES_DIR = "figures"


def binary_metrics(truth, pred):
    truth = np.asarray(truth)
    pred = np.asarray(pred)
    tp = int(np.sum((truth == 1) & (pred == 1)))
    fp = int(np.sum((truth == 0) & (pred == 1)))
    tn = int(np.sum((truth == 0) & (pred == 0)))
    fn = int(np.sum((truth == 1) & (pred == 0)))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(truth)
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


def graph_feature_vector(data):
    # Non-graph baseline input: mean and max of the 25 node features over the sliced graph
    x = data["x"]
    return torch.cat([x.mean(dim=0), x.max(dim=0).values]).numpy()


def gat_loco(dataset, seed):
    """Returns per-decision rows and per-contract localization rows for one seed."""
    decisions, localization = [], []
    for i, held in enumerate(dataset):
        train = [d for j, d in enumerate(dataset) if j != i]
        model = fit_model(train, epochs=EPOCHS, lr=LR, seed=seed, verbose=False)
        with torch.no_grad():
            node_logits, graph_logits = model(held["x"], held["edge_index"])
        graph_probs = torch.sigmoid(graph_logits).numpy()
        node_probs = torch.sigmoid(node_logits).numpy()

        for c in range(len(VULN_NAMES)):
            decisions.append({
                "seed": seed,
                "contract": held["file_name"],
                "class": VULN_NAMES[c],
                "truth": int(held["graph_y"][c].item()),
                "prob": float(graph_probs[c]),
                "pred": int(graph_probs[c] > GRAPH_THRESH),
            })

        info = DEMO_LABEL_INFO[held["file_name"]]
        if info["vulnerable_lines"]:
            c = info["vuln_class"]
            gold = set(info["vulnerable_lines"])
            node_list = held["node_list"]
            predicted = set()
            for idx, node_id in enumerate(node_list):
                line = held["graph"].nodes[node_id].get("line", 0)
                if line > 0 and node_probs[idx, c] > NODE_THRESH:
                    predicted.add(line)
            hit = gold & predicted
            localization.append({
                "seed": seed,
                "contract": held["file_name"],
                "gold_lines": sorted(gold),
                "predicted_lines": sorted(predicted),
                "precision": len(hit) / len(predicted) if predicted else 0.0,
                "recall": len(hit) / len(gold),
                "flagged": int(graph_probs[c] > GRAPH_THRESH),
            })
    return decisions, localization


def sink_baseline(dataset):
    """Flags a class whenever the full graph contains any sink for it (no learning)."""
    decisions = []
    for held in dataset:
        sinks = find_interest_points(held["full_graph"])
        for c in range(len(VULN_NAMES)):
            decisions.append({
                "contract": held["file_name"],
                "class": VULN_NAMES[c],
                "truth": int(held["graph_y"][c].item()),
                "pred": int(len(sinks[SINK_KEYS[c]]) > 0),
            })
    return decisions


def logistic_loco(dataset):
    """Logistic regression on pooled node features; no message passing."""
    decisions = []
    for i, held in enumerate(dataset):
        train = [d for j, d in enumerate(dataset) if j != i]
        X_train = np.stack([graph_feature_vector(d) for d in train])
        X_test = graph_feature_vector(held).reshape(1, -1)
        for c in range(len(VULN_NAMES)):
            y_train = np.array([int(d["graph_y"][c].item()) for d in train])
            if len(set(y_train)) < 2:
                # A single label in the training folds: predict that label
                prob = float(y_train[0])
            else:
                clf = LogisticRegression(max_iter=1000)
                clf.fit(X_train, y_train)
                prob = float(clf.predict_proba(X_test)[0, 1])
            decisions.append({
                "contract": held["file_name"],
                "class": VULN_NAMES[c],
                "truth": int(held["graph_y"][c].item()),
                "prob": prob,
                "pred": int(prob > GRAPH_THRESH),
            })
    return decisions


def in_sample_gat(dataset, weights_path="./model.pth"):
    """Verification on the training contracts, using the saved weights."""
    model = SmartContractGNN(in_dim=25, hidden_dim=64, num_classes=3)
    model.load_state_dict(torch.load(weights_path))
    model.eval()
    decisions = []
    with torch.no_grad():
        for held in dataset:
            _, graph_logits = model(held["x"], held["edge_index"])
            probs = torch.sigmoid(graph_logits).numpy()
            for c in range(len(VULN_NAMES)):
                decisions.append({
                    "contract": held["file_name"],
                    "class": VULN_NAMES[c],
                    "truth": int(held["graph_y"][c].item()),
                    "prob": float(probs[c]),
                    "pred": int(probs[c] > GRAPH_THRESH),
                })
    return decisions


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def decision_metrics(decisions):
    return binary_metrics([d["truth"] for d in decisions], [d["pred"] for d in decisions])


def plot_slicing(dataset, path):
    names = [d["file_name"].replace(".sol", "") for d in dataset]
    full = [len(d["full_graph"].nodes()) for d in dataset]
    sliced = [len(d["graph"].nodes()) for d in dataset]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - 0.2, full, 0.4, label="full graph", color="lightgray", edgecolor="black")
    ax.bar(x + 0.2, sliced, 0.4, label="sliced graph", color="steelblue", edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("nodes")
    ax.set_title("Graph size before and after 3-step slicing")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_loco_heatmap(gat_decisions, dataset, path):
    contracts = [d["file_name"] for d in dataset]
    mean_prob = np.zeros((len(contracts), len(VULN_NAMES)))
    truth = np.zeros_like(mean_prob)
    for r, name in enumerate(contracts):
        for c, cls in enumerate(VULN_NAMES):
            vals = [d["prob"] for d in gat_decisions if d["contract"] == name and d["class"] == cls]
            mean_prob[r, c] = np.mean(vals)
            truth[r, c] = [d["truth"] for d in gat_decisions if d["contract"] == name and d["class"] == cls][0]
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(mean_prob, cmap="Reds", vmin=0, vmax=1)
    for r in range(len(contracts)):
        for c in range(len(VULN_NAMES)):
            mark = "V" if truth[r, c] == 1 else "S"
            ax.text(c, r, f"{mean_prob[r, c]:.2f}\n[{mark}]", ha="center", va="center", fontsize=9)
    ax.set_xticks(range(len(VULN_NAMES)))
    ax.set_xticklabels(VULN_NAMES, rotation=15, ha="right")
    ax.set_yticks(range(len(contracts)))
    ax.set_yticklabels([c.replace(".sol", "") for c in contracts])
    ax.set_title("GAT held-out probability (mean of 5 seeds)\n[V]=ground-truth vulnerable, [S]=safe")
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_method_comparison(summary, path):
    methods = list(summary.keys())
    metrics = ["precision", "recall", "f1"]
    x = np.arange(len(metrics))
    width = 0.8 / len(methods)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, method in enumerate(methods):
        vals = [summary[method][m] for m in metrics]
        ax.bar(x + k * width - 0.4 + width / 2, vals, width, label=method, edgecolor="black")
    ax.set_xticks(x)
    ax.set_xticklabels(["precision", "recall", "F1"])
    ax.set_ylim(0, 1.05)
    ax.set_title("Leave-one-contract-out, 18 class decisions (6 contracts x 3 classes)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    dataset = load_dataset("./demo_contracts")
    assert len(dataset) == 6, "expected the six demo contracts"

    gat_rows, loc_rows = [], []
    for seed in SEEDS:
        print(f"[*] LOCO GAT, seed {seed}")
        decisions, loc = gat_loco(dataset, seed)
        gat_rows += decisions
        loc_rows += loc

    per_seed = {}
    for seed in SEEDS:
        per_seed[seed] = decision_metrics([d for d in gat_rows if d["seed"] == seed])
    metric_keys = ["precision", "recall", "f1", "accuracy"]
    gat_summary = {k: float(np.mean([per_seed[s][k] for s in SEEDS])) for k in metric_keys}
    gat_std = {k: float(np.std([per_seed[s][k] for s in SEEDS])) for k in metric_keys}
    gat_counts_seed42 = per_seed[SEEDS[0]]

    sink_rows = sink_baseline(dataset)
    sink_metrics = decision_metrics(sink_rows)
    logi_rows = logistic_loco(dataset)
    logi_metrics = decision_metrics(logi_rows)

    in_sample = decision_metrics(in_sample_gat(dataset))

    loc_summary = {
        "mean_precision": float(np.mean([r["precision"] for r in loc_rows])),
        "mean_recall": float(np.mean([r["recall"] for r in loc_rows])),
        "rows": len(loc_rows),
    }

    write_csv(os.path.join(RESULTS_DIR, "loco_gat_decisions.csv"), gat_rows)
    write_csv(os.path.join(RESULTS_DIR, "loco_gat_localization.csv"),
              [{**r, "gold_lines": " ".join(map(str, r["gold_lines"])),
                "predicted_lines": " ".join(map(str, r["predicted_lines"]))} for r in loc_rows])
    write_csv(os.path.join(RESULTS_DIR, "loco_sink_baseline_decisions.csv"), sink_rows)
    write_csv(os.path.join(RESULTS_DIR, "loco_logistic_baseline_decisions.csv"), logi_rows)

    slicing = [{"contract": d["file_name"],
                "full_nodes": len(d["full_graph"].nodes()),
                "sliced_nodes": len(d["graph"].nodes()),
                "full_edges": len(d["full_graph"].edges()),
                "sliced_edges": len(d["graph"].edges())} for d in dataset]
    write_csv(os.path.join(RESULTS_DIR, "slicing_sizes.csv"), slicing)

    summary = {
        "GAT (LOCO, mean of 5 seeds)": gat_summary,
        "Sink-presence rule (no learning)": {k: sink_metrics[k] for k in metric_keys},
        "Logistic regression, pooled features": {k: logi_metrics[k] for k in metric_keys},
    }
    metrics = {
        "setup": {
            "contracts": [d["file_name"] for d in dataset],
            "decisions_per_method": len(gat_rows) // len(SEEDS),
            "seeds": SEEDS,
            "epochs": EPOCHS,
            "learning_rate": LR,
            "graph_threshold": GRAPH_THRESH,
            "node_threshold": NODE_THRESH,
        },
        "gat_loco_mean": gat_summary,
        "gat_loco_std": gat_std,
        "gat_loco_per_seed": {str(s): per_seed[s] for s in SEEDS},
        "sink_rule": sink_metrics,
        "logistic_loco": logi_metrics,
        "gat_in_sample_saved_weights": in_sample,
        "gat_localization_loco": loc_summary,
        "gat_seed0_counts": gat_counts_seed42,
    }
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    plot_slicing(dataset, os.path.join(FIGURES_DIR, "fig_slicing_sizes.png"))
    plot_loco_heatmap(gat_rows, dataset, os.path.join(FIGURES_DIR, "fig_loco_gat_heatmap.png"))
    plot_method_comparison(summary, os.path.join(FIGURES_DIR, "fig_method_comparison.png"))

    print("\nLOCO summary (18 class decisions per method)")
    for method, vals in summary.items():
        print(f"  {method:40s} P={vals['precision']:.3f} R={vals['recall']:.3f} "
              f"F1={vals['f1']:.3f} Acc={vals['accuracy']:.3f}")
    print(f"  GAT std across seeds: " + ", ".join(f"{k}={gat_std[k]:.3f}" for k in metric_keys))
    print(f"  GAT in-sample (saved weights): P={in_sample['precision']:.3f} "
          f"R={in_sample['recall']:.3f} F1={in_sample['f1']:.3f} Acc={in_sample['accuracy']:.3f}")
    print(f"  GAT localization (LOCO, vulnerable contracts): mean precision="
          f"{loc_summary['mean_precision']:.3f}, mean recall={loc_summary['mean_recall']:.3f}, n={loc_summary['rows']}")


if __name__ == "__main__":
    main()
