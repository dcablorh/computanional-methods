import networkx as nx

def find_interest_points(G):
    """
    Identifies interest points (sinks) in the contract graph.
    Returns lists of node IDs for:
      - external_calls: nodes involving msg.sender.call, transfer, send
      - timestamp_refs: nodes referencing block.timestamp
      - arithmetic_ops: nodes representing binary arithmetic operations
    """
    external_calls = []
    timestamp_refs = []
    arithmetic_ops = []
    
    for node_id, data in G.nodes(data=True):
        code = data.get("code", "").lower()
        node_type = data.get("node_type", "")
        
        if node_type == "FunctionCall":
            if any(kw in code for kw in (".call", "transfer", "send")):
                external_calls.append(node_id)
                
        if "block.timestamp" in code or "now" in code:
            timestamp_refs.append(node_id)
            
        if node_type == "BinaryOperation":
            ast_node = data.get("ast_node", {})
            # Legacy AST (solc < 0.8) stores the operator under "attributes"
            op = ast_node.get("operator") or ast_node.get("attributes", {}).get("operator", "")
            if op in ("+", "-", "*", "/"):
                arithmetic_ops.append(node_id)
                
    return {
        "external_calls": external_calls,
        "timestamp_refs": timestamp_refs,
        "arithmetic_ops": arithmetic_ops
    }

def slice_graph(G, seed_nodes, steps=3):
    """
    Builds a program slice around seed_nodes.
    It performs backward and forward traversal along control flow and data flow edges.
    """
    if not seed_nodes:
        return G.copy()
        
    slice_nodes = set(seed_nodes)
    
    # follow control and data dependencies, not AST containment
    dep_edge_types = {"cfg_next", "cfg_true", "cfg_false", "data_ref", "data_flow"}
    
    # backward: nodes the seeds depend on
    for seed in seed_nodes:
        visited = set()
        queue = [(seed, 0)]
        while queue:
            curr, dist = queue.pop(0)
            if curr in visited or dist > steps:
                continue
            visited.add(curr)
            slice_nodes.add(curr)
            
            for pred in G.predecessors(curr):
                edge_data = G.get_edge_data(pred, curr)
                is_dep = False
                for idx, edict in edge_data.items():
                    if edict.get("type") in dep_edge_types:
                        is_dep = True
                        break
                if is_dep:
                    queue.append((pred, dist + 1))
                    
    # forward: nodes that depend on the seeds
    for seed in seed_nodes:
        visited = set()
        queue = [(seed, 0)]
        while queue:
            curr, dist = queue.pop(0)
            if curr in visited or dist > steps:
                continue
            visited.add(curr)
            slice_nodes.add(curr)
            
            for succ in G.successors(curr):
                edge_data = G.get_edge_data(curr, succ)
                is_dep = False
                for idx, edict in edge_data.items():
                    if edict.get("type") in dep_edge_types:
                        is_dep = True
                        break
                if is_dep:
                    queue.append((succ, dist + 1))
                    
    # add AST ancestors so the slice stays a connected tree
    ast_parents = set()
    for node in slice_nodes:
        curr = node
        for _ in range(3):
            parent = None
            for pred in G.predecessors(curr):
                edge_data = G.get_edge_data(pred, curr)
                for idx, edict in edge_data.items():
                    if edict.get("type") == "ast":
                        parent = pred
                        break
                if parent is not None:
                    break
            if parent is not None:
                ast_parents.add(parent)
                curr = parent
            else:
                break
                
    slice_nodes.update(ast_parents)
    
    sliced_G = G.subgraph(slice_nodes).copy()
    return sliced_G
