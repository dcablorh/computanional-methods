import os
import sys
import argparse
import torch
import networkx as nx
import matplotlib.pyplot as plt
from parser.compiler import compile_contract
from parser.graph_builder import build_graph_from_ast
from slicing.slicer import find_interest_points, slice_graph
from data_loader import convert_graph_to_tensors
from model.gnn import SmartContractGNN

VULN_CLASSES = ["Reentrancy", "Timestamp Dependency", "Arithmetic Error"]

def visualize_audited_graph(G, node_probs, vuln_class_idx, save_path=None):
    """
    Visualizes the audited graph and highlights vulnerable nodes in red.
    """
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.2, seed=42)

    node_colors = []
    labels = {}
    
    for idx, (node_id, data) in enumerate(G.nodes(data=True)):
        line = data.get("line", 0)
        node_type = data.get("node_type", "")
        
        prob = node_probs[idx, vuln_class_idx].item()
        
        if prob > 0.3 and line > 0:
            node_colors.append("red")
            snippet = data.get("code", "").strip()[:20]
            labels[node_id] = f"Line {line}: {snippet}"
        elif node_type in ("FunctionDefinition", "ContractDefinition"):
            node_colors.append("orange")
            labels[node_id] = data.get("label", "")
        else:
            node_colors.append("lightblue")

    nx.draw_networkx_nodes(G, pos, node_size=400, node_color=node_colors, alpha=0.85)

    edge_types = {}
    for u, v, key, data in G.edges(keys=True, data=True):
        etype = data.get("type", "other")
        edge_types.setdefault(etype, []).append((u, v))
        
    colors = {
        "ast": "lightgray",
        "cfg_next": "green",
        "cfg_true": "darkgreen",
        "cfg_false": "red",
        "data_ref": "blue",
        "data_flow": "purple"
    }
    
    for etype, edges in edge_types.items():
        color = colors.get(etype, "orange")
        nx.draw_networkx_edges(
            G, pos, edgelist=edges, edge_color=color,
            width=1.5, alpha=0.6, arrowsize=10
        )

    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color="black")
    
    class_name = VULN_CLASSES[vuln_class_idx]
    plt.title(f"GNN Audit Flowchart - Flagged {class_name} Path (Red Nodes)")
    plt.axis("off")
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
        print(f"[+] Saved audit graph visualization to {save_path}")
    else:
        plt.show()
    plt.close()

def audit_contract(contract_path, model_path="./model.pth", visualize=False):
    if not os.path.exists(contract_path):
        print(f"[-] Error: File not found: {contract_path}")
        return
        
    print(f"\n[*] Starting security audit on: {contract_path}")
    
    try:
        ast = compile_contract(contract_path)
    except Exception as e:
        print(f"[-] Compilation error: {e}")
        return
        
    with open(contract_path, "r", encoding="utf-8") as f:
        source_code = f.read()
        
    print("[*] Generating contract semantic graph (AST + CFG + PDG)...")
    G = build_graph_from_ast(ast, source_code)
    print(f"[+] Complete graph constructed: {len(G.nodes())} nodes, {len(G.edges())} edges.")
    
    print("[*] Performing Program Slicing around security interest points...")
    sinks = find_interest_points(G)
    all_seeds = sinks["external_calls"] + sinks["timestamp_refs"] + sinks["arithmetic_ops"]
    if not all_seeds:
        all_seeds = [n for n, d in G.nodes(data=True) if d.get("node_type") in ("FunctionCall", "VariableDeclaration")]
        
    sliced_G = slice_graph(G, all_seeds, steps=3)
    print(f"[+] Sliced graph: {len(sliced_G.nodes())} nodes, {len(sliced_G.edges())} edges (removed {len(G.nodes()) - len(sliced_G.nodes())} clutter nodes).")
    
    tensor_data = convert_graph_to_tensors(sliced_G)
    x = tensor_data["x"]
    edge_index = tensor_data["edge_index"]
    node_list = tensor_data["node_list"]
    
    model = SmartContractGNN(in_dim=25, hidden_dim=64, num_classes=3)
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        print(f"[+] Loaded GNN model weights from {model_path}")
    else:
        print("[!] Warning: No trained model weights found. Using default initialized weights.")
        
    model.eval()
    with torch.no_grad():
        node_logits, graph_logits = model(x, edge_index)
        node_probs = torch.sigmoid(node_logits)
        graph_probs = torch.sigmoid(graph_logits)
        
    print("\n" + "="*50)
    print("                 AUDIT SCAN REPORT                 ")
    print("="*50)
    
    vuln_found = False
    
    for class_idx, class_name in enumerate(VULN_CLASSES):
        prob = graph_probs[class_idx].item()
        print(f"[{class_name}] Confidence: {prob*100:.2f}%")
        
        if prob > 0.5:
            vuln_found = True
            print(f"  >>> ALERT: Potential {class_name} vulnerability detected!")
            
            localized_lines = {}
            for idx, node_id in enumerate(node_list):
                node_prob = node_probs[idx, class_idx].item()
                if node_prob > 0.3:
                    node_data = sliced_G.nodes[node_id]
                    line = node_data.get("line", 0)
                    code = node_data.get("code", "").strip()
                    
                    if line > 0 and code:
                        localized_lines[line] = code
                        
            if localized_lines:
                print("  >>> Vulnerable Code Localization (GNN Node Saliency):")
                for line in sorted(localized_lines.keys()):
                    print(f"      [Line {line:03d}]: {localized_lines[line]}")
            else:
                print("      Unable to localize exact line (low node confidence).")
                
            if visualize:
                output_image = f"{os.path.splitext(os.path.basename(contract_path))[0]}_audit.png"
                visualize_audited_graph(sliced_G, node_probs, class_idx, save_path=output_image)
                
            print("-" * 50)
            
    if not vuln_found:
        print("[+] SUCCESS: No vulnerabilities detected. Contract is clean.")
        print("="*50)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GNN-Based Smart Contract Security Auditor")
    parser.add_argument("--contract", required=True, help="Path to Solidity smart contract file")
    parser.add_argument("--model", default="./model.pth", help="Path to trained model weights")
    parser.add_argument("--visualize", action="store_true", help="Generate and save visual GNN graph of contract")
    
    args = parser.parse_args()
    audit_contract(args.contract, args.model, args.visualize)
