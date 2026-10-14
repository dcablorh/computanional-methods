import os
import torch
from parser.compiler import compile_contract
from parser.graph_builder import build_graph_from_ast
from slicing.slicer import find_interest_points, slice_graph
from model.gnn import extract_node_features

# ground-truth labels for the demo contracts
DEMO_LABEL_INFO = {
    "ReentrancyVulnerable.sol": {
        "vuln_class": 0, # Reentrancy
        "vulnerable_lines": [15, 16] # Low-level call and verify
    },
    "ReentrancySafe.sol": {
        "vuln_class": 0,
        "vulnerable_lines": [] # Safe
    },
    "TimestampVulnerable.sol": {
        "vuln_class": 1, # Timestamp Dependency
        "vulnerable_lines": [10] # require(block.timestamp % 15 == 0)
    },
    "TimestampSafe.sol": {
        "vuln_class": 1,
        "vulnerable_lines": [] # Safe
    },
    "ArithmeticVulnerable.sol": {
        "vuln_class": 2, # Arithmetic Error
        "vulnerable_lines": [14] # totalAmount = receivers.length * amount
    },
    "ArithmeticSafe.sol": {
        "vuln_class": 2,
        "vulnerable_lines": [] # Safe
    }
}

def convert_graph_to_tensors(G, vuln_class=None, vulnerable_lines=None):
    """
    Converts a networkx graph into PyTorch tensors for GNN training.
    """
    node_list = list(G.nodes())
    node_to_idx = {node_id: idx for idx, node_id in enumerate(node_list)}
    num_nodes = len(node_list)

    # node features, [num_nodes, 25]
    x_features = []
    for node_id in node_list:
        feat = extract_node_features(G.nodes[node_id])
        x_features.append(feat)
    X = torch.tensor(x_features, dtype=torch.float32)

    # edge index, [2, num_edges]
    edge_sources = []
    edge_targets = []
    for u, v in G.edges():
        edge_sources.append(node_to_idx[u])
        edge_targets.append(node_to_idx[v])
    edge_index = torch.tensor([edge_sources, edge_targets], dtype=torch.long)

    if edge_index.numel() == 0:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    # node-level and graph-level targets
    # multi-label targets, one column per class
    # 0: Reentrancy, 1: Timestamp Dependency, 2: Arithmetic Error
    node_targets = torch.zeros((num_nodes, 3), dtype=torch.float32)
    graph_targets = torch.zeros(3, dtype=torch.float32)

    if vuln_class is not None:
        if vulnerable_lines:
            graph_targets[vuln_class] = 1.0
            
            for idx, node_id in enumerate(node_list):
                node_line = G.nodes[node_id].get("line", 0)
                if node_line in vulnerable_lines:
                    node_targets[idx, vuln_class] = 1.0

    return {
        "x": X,
        "edge_index": edge_index,
        "node_y": node_targets,
        "graph_y": graph_targets,
        "node_list": node_list # original node IDs, in row order
    }

def load_dataset(demo_dir):
    """
    Compiles the demo contracts, builds and slices their graphs, and packages them into tensors.
    """
    dataset = []
    print("[*] Processing contracts to build GNN dataset...")

    for file_name, label_info in DEMO_LABEL_INFO.items():
        contract_path = os.path.join(demo_dir, file_name)
        if not os.path.exists(contract_path):
            print(f"[!] Warning: Demo contract {file_name} not found at {contract_path}. Skipping.")
            continue
            
        try:
            ast = compile_contract(contract_path)
            
            with open(contract_path, "r", encoding="utf-8") as f:
                source_code = f.read()
                
            G = build_graph_from_ast(ast, source_code)
            
            sinks = find_interest_points(G)
            
            all_seeds = sinks["external_calls"] + sinks["timestamp_refs"] + sinks["arithmetic_ops"]
            
            # no sinks: fall back to calls and declarations
            if not all_seeds:
                all_seeds = [n for n, d in G.nodes(data=True) if d.get("node_type") in ("FunctionCall", "VariableDeclaration")]
                
            sliced_G = slice_graph(G, all_seeds, steps=3)
            
            tensors = convert_graph_to_tensors(
                sliced_G, 
                vuln_class=label_info["vuln_class"], 
                vulnerable_lines=label_info["vulnerable_lines"]
            )
            
            tensors["file_name"] = file_name
            tensors["graph"] = sliced_G
            tensors["full_graph"] = G
            dataset.append(tensors)
            print(f"[+] Loaded {file_name} (Nodes: {len(sliced_G.nodes())}, Edges: {len(sliced_G.edges())})")
            
        except Exception as e:
            print(f"[-] Failed to process {file_name}: {e}")

    return dataset
