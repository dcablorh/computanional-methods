import os
import torch
import torch.nn as nn
from data_loader import load_dataset
from model.gnn import SmartContractGNN

criterion = nn.BCEWithLogitsLoss()

def train_model(epochs=100, lr=0.005, seed=42):
    # Fix the random seed so that retraining reproduces the same weights
    torch.manual_seed(seed)

    demo_dir = "./demo_contracts"
    dataset = load_dataset(demo_dir)
    
    if not dataset:
        print("[-] Error: Empty dataset. Make sure demo contracts are created and compile successfully.")
        return
        
    model = SmartContractGNN(in_dim=25, hidden_dim=64, num_classes=3)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    
    print("\n[*] Starting GNN model training...")
    print(f"[*] Training on {len(dataset)} graphs for {epochs} epochs...")
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        total_graph_loss = 0.0
        total_node_loss = 0.0
        
        for data in dataset:
            x = data["x"]
            edge_index = data["edge_index"]
            node_y = data["node_y"]
            graph_y = data["graph_y"]
            
            optimizer.zero_grad()
            
            node_logits, graph_logits = model(x, edge_index)
            
            loss_graph = criterion(graph_logits, graph_y)
            loss_node = criterion(node_logits, node_y)
            
            # Weigh node-level loss heavily to encourage line-level localization
            loss = loss_graph + 2.0 * loss_node
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            total_graph_loss += loss_graph.item()
            total_node_loss += loss_node.item()
            
        if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
            avg_loss = total_loss / len(dataset)
            avg_gl = total_graph_loss / len(dataset)
            avg_nl = total_node_loss / len(dataset)
            print(f"Epoch {epoch:03d}/{epochs:03d} | Total Loss: {avg_loss:.4f} (Graph Loss: {avg_gl:.4f}, Node Loss: {avg_nl:.4f})")
            
    print("\n[+] Training complete!")
    
    model_path = "./model.pth"
    torch.save(model.state_dict(), model_path)
    print(f"[+] Saved trained model weights to {model_path}")
    
    print("\n[*] Evaluating model predictions on training set (verification check)...")
    model.eval()
    
    vuln_names = ["Reentrancy", "Timestamp Dependency", "Arithmetic Error"]
    
    with torch.no_grad():
        for data in dataset:
            file_name = data["file_name"]
            x = data["x"]
            edge_index = data["edge_index"]
            graph_y = data["graph_y"]
            sliced_G = data["graph"]
            
            _, graph_logits = model(x, edge_index)
            probs = torch.sigmoid(graph_logits).numpy()
            
            print(f"\n--- Contract: {file_name} ---")
            for class_idx, class_name in enumerate(vuln_names):
                pred_prob = probs[class_idx]
                true_label = graph_y[class_idx].item()
                status = "VULNERABLE (True)" if true_label == 1.0 else "SAFE (True)"
                pred_status = "VULNERABLE" if pred_prob > 0.5 else "SAFE"
                print(f"  [{class_name}] True: {status} | Pred: {pred_status} (Prob: {pred_prob:.4f})")
                
    return model

if __name__ == "__main__":
    train_model(epochs=100)
