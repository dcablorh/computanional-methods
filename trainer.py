import os
import torch
import torch.nn as nn
from data_loader import load_dataset
from model.gnn import SmartContractGNN

criterion = nn.BCEWithLogitsLoss()

VULN_NAMES = ["Reentrancy", "Timestamp Dependency", "Arithmetic Error"]

def fit_model(dataset, epochs=100, lr=0.005, seed=42, verbose=True):
    # Seeding before model creation makes the initial weights and dropout masks repeatable
    torch.manual_seed(seed)

    model = SmartContractGNN(in_dim=25, hidden_dim=64, num_classes=3)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total_graph_loss = 0.0
        total_node_loss = 0.0

        # One optimizer step per graph (no mini-batching)
        for data in dataset:
            optimizer.zero_grad()

            node_logits, graph_logits = model(data["x"], data["edge_index"])
            loss_graph = criterion(graph_logits, data["graph_y"])
            loss_node = criterion(node_logits, data["node_y"])

            # Weigh node-level loss heavily to encourage line-level localization
            loss = loss_graph + 2.0 * loss_node
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_graph_loss += loss_graph.item()
            total_node_loss += loss_node.item()

        if verbose and (epoch == 1 or epoch % 10 == 0 or epoch == epochs):
            n = len(dataset)
            print(f"Epoch {epoch:03d}/{epochs:03d} | Total Loss: {total_loss / n:.4f} "
                  f"(Graph Loss: {total_graph_loss / n:.4f}, Node Loss: {total_node_loss / n:.4f})")

    model.eval()
    return model

def train_model(epochs=100, lr=0.005, seed=42, model_path="./model.pth"):
    demo_dir = "./demo_contracts"
    dataset = load_dataset(demo_dir)

    if not dataset:
        print("[-] Error: Empty dataset. Make sure demo contracts are created and compile successfully.")
        return None

    print("\n[*] Starting GNN model training...")
    print(f"[*] Training on {len(dataset)} graphs for {epochs} epochs (seed={seed})...")
    model = fit_model(dataset, epochs=epochs, lr=lr, seed=seed)
    print("\n[+] Training complete!")

    torch.save(model.state_dict(), model_path)
    print(f"[+] Saved trained model weights to {model_path}")

    # In-sample check: the same six contracts were used for training
    print("\n[*] Evaluating model predictions on training set (verification check)...")
    with torch.no_grad():
        for data in dataset:
            _, graph_logits = model(data["x"], data["edge_index"])
            probs = torch.sigmoid(graph_logits).numpy()

            print(f"\n--- Contract: {data['file_name']} ---")
            for class_idx, class_name in enumerate(VULN_NAMES):
                pred_prob = probs[class_idx]
                true_label = data["graph_y"][class_idx].item()
                status = "VULNERABLE (True)" if true_label == 1.0 else "SAFE (True)"
                pred_status = "VULNERABLE" if pred_prob > 0.5 else "SAFE"
                print(f"  [{class_name}] True: {status} | Pred: {pred_status} (Prob: {pred_prob:.4f})")

    return model

if __name__ == "__main__":
    train_model(epochs=100)
