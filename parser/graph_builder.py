import os
import networkx as nx
import matplotlib.pyplot as plt

def compute_line_offsets(source_code):
    offsets = [0]
    for idx, char in enumerate(source_code):
        if char == '\n':
            offsets.append(idx + 1)
    return offsets

def get_line_number(src_str, line_offsets):
    if not src_str:
        return 1
    parts = src_str.split(':')
    if not parts:
        return 1
    try:
        offset = int(parts[0])
        for idx, start_offset in enumerate(line_offsets):
            if offset < start_offset:
                return idx
        return len(line_offsets)
    except ValueError:
        return 1

def get_node_code(src_str, source_code):
    if not src_str:
        return ""
    parts = src_str.split(':')
    if len(parts) < 2:
        return ""
    try:
        offset = int(parts[0])
        length = int(parts[1])
        return source_code[offset:offset+length]
    except ValueError:
        return ""

def is_ast_node(node):
    return isinstance(node, dict) and "id" in node and ("nodeType" in node or "name" in node)

def get_node_type(node):
    if "nodeType" in node:
        return node["nodeType"]
    # In legacy AST, node type is stored in 'name', but check it is a string
    name_val = node.get("name")
    if isinstance(name_val, str) and name_val not in ("", None):
        return name_val
    return "Other"

def get_user_name(node):
    if "nodeType" in node:
        return node.get("name", "")
    return node.get("attributes", {}).get("name", "")

def get_node_value(node):
    if "nodeType" in node:
        return node.get("value", "")
    return node.get("attributes", {}).get("value", "")

def get_referenced_declaration(node):
    if "nodeType" in node:
        return node.get("referencedDeclaration")
    return node.get("attributes", {}).get("referencedDeclaration")

def get_sub_node(node, key_compact, child_index_legacy):
    if "nodeType" in node:
        return node.get(key_compact)
    else:
        children = node.get("children", [])
        if 0 <= child_index_legacy < len(children):
            return children[child_index_legacy]
        return None

def get_ast_children(node):
    children = []
    if not isinstance(node, dict):
        return children
        
    # Legacy AST children list
    if "children" in node:
        for child in node["children"]:
            if is_ast_node(child):
                children.append(child)
        return children
        
    # Compact AST fields
    for k, v in node.items():
        if k in ("nodeType", "id", "src"):
            continue
        if isinstance(v, dict) and is_ast_node(v):
            children.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and is_ast_node(item):
                    children.append(item)
    return children

def get_block_statements(node):
    if "nodeType" in node:
        return node.get("statements", [])
    # In legacy AST, statements are simply children of Block
    return node.get("children", [])

def get_call_arguments(node):
    if "nodeType" in node:
        return node.get("arguments", [])
    # In legacy AST, first child is callee, others are arguments
    children = node.get("children", [])
    if len(children) > 1:
        return children[1:]
    return []

def build_cfg_edges(node, follow_ids, G):
    """
    Recursively adds CFG edges in graph G for the given AST node.
    Returns a list of entry node IDs for this node.
    """
    if not isinstance(node, dict):
        return follow_ids
        
    node_type = get_node_type(node)
    node_id = node.get("id")
    
    if not node_id:
        return follow_ids
        
    if node_type == "Block":
        statements = get_block_statements(node)
        if not statements:
            return follow_ids
        current_follow = follow_ids
        for stmt in reversed(statements):
            current_follow = build_cfg_edges(stmt, current_follow, G)
        return current_follow
        
    elif node_type == "IfStatement":
        condition = get_sub_node(node, "condition", 0)
        true_body = get_sub_node(node, "trueBody", 1)
        false_body = get_sub_node(node, "falseBody", 2)
        
        cond_entry = build_cfg_edges(condition, [], G)
        cond_id = cond_entry[0] if cond_entry else node_id
        
        G.add_edge(node_id, cond_id, type="cfg_next")
        
        true_entry = build_cfg_edges(true_body, follow_ids, G)
        if true_entry:
            G.add_edge(cond_id, true_entry[0], type="cfg_true")
        elif follow_ids:
            G.add_edge(cond_id, follow_ids[0], type="cfg_true")
            
        if false_body:
            false_entry = build_cfg_edges(false_body, follow_ids, G)
            if false_entry:
                G.add_edge(cond_id, false_entry[0], type="cfg_false")
            elif follow_ids:
                G.add_edge(cond_id, follow_ids[0], type="cfg_false")
        else:
            for fid in follow_ids:
                G.add_edge(cond_id, fid, type="cfg_false")
                
        return [node_id]
        
    elif node_type == "ForStatement":
        condition = get_sub_node(node, "condition", 1)
        body = get_sub_node(node, "body", 3)
        loop_expr = get_sub_node(node, "loopExpression", 2)
        
        cond_entry = build_cfg_edges(condition, [], G)
        cond_id = cond_entry[0] if cond_entry else node_id
        
        G.add_edge(node_id, cond_id, type="cfg_next")
        
        if loop_expr:
            loop_expr_entry = build_cfg_edges(loop_expr, [cond_id], G)
            body_entry = build_cfg_edges(body, loop_expr_entry, G)
        else:
            body_entry = build_cfg_edges(body, [cond_id], G)
            
        if body_entry:
            G.add_edge(cond_id, body_entry[0], type="cfg_true")
        else:
            G.add_edge(cond_id, cond_id, type="cfg_true")
            
        for fid in follow_ids:
            G.add_edge(cond_id, fid, type="cfg_false")
            
        return [node_id]
        
    elif node_type == "WhileStatement":
        condition = get_sub_node(node, "condition", 0)
        body = get_sub_node(node, "body", 1)
        
        cond_entry = build_cfg_edges(condition, [], G)
        cond_id = cond_entry[0] if cond_entry else node_id
        
        G.add_edge(node_id, cond_id, type="cfg_next")
        
        body_entry = build_cfg_edges(body, [cond_id], G)
        if body_entry:
            G.add_edge(cond_id, body_entry[0], type="cfg_true")
        else:
            G.add_edge(cond_id, cond_id, type="cfg_true")
            
        for fid in follow_ids:
            G.add_edge(cond_id, fid, type="cfg_false")
            
        return [node_id]
        
    elif node_type == "ExpressionStatement":
        expr = get_sub_node(node, "expression", 0)
        expr_entry = build_cfg_edges(expr, follow_ids, G)
        if expr_entry:
            G.add_edge(node_id, expr_entry[0], type="cfg_next")
        else:
            for fid in follow_ids:
                G.add_edge(node_id, fid, type="cfg_next")
        return [node_id]
        
    elif node_type == "VariableDeclarationStatement":
        init = get_sub_node(node, "initialValue", 1)
        if init:
            init_entry = build_cfg_edges(init, follow_ids, G)
            if init_entry:
                G.add_edge(node_id, init_entry[0], type="cfg_next")
        else:
            for fid in follow_ids:
                G.add_edge(node_id, fid, type="cfg_next")
        return [node_id]
        
    elif node_type == "Return":
        val = get_sub_node(node, "expression", 0)
        if val:
            val_entry = build_cfg_edges(val, [], G)
            if val_entry:
                G.add_edge(node_id, val_entry[0], type="cfg_next")
        return [node_id]
        
    children = get_ast_children(node)
    if children:
        current_follow = follow_ids
        for child in reversed(children):
            current_follow = build_cfg_edges(child, current_follow, G)
        if current_follow:
            G.add_edge(node_id, current_follow[0], type="cfg_next")
    else:
        for fid in follow_ids:
            G.add_edge(node_id, fid, type="cfg_next")
            
    return [node_id]

def build_graph_from_ast(ast, source_code):
    """
    Builds a MultiDiGraph combining AST hierarchy, CFG next flow, and PDG data references.
    Supports both legacy AST and compact AST formats.
    """
    line_offsets = compute_line_offsets(source_code)
    G = nx.MultiDiGraph()
    
    def traverse_ast(node, parent_id=None):
        if not isinstance(node, dict):
            return
            
        node_id = node.get("id")
        if node_id is None:
            return
            
        node_type = get_node_type(node)
        src = node.get("src", "")
        
        line = get_line_number(src, line_offsets)
        code = get_node_code(src, source_code)
        
        name = get_user_name(node)
        value = get_node_value(node)
        label = f"{node_type}"
        if name:
            label += f" ({name})"
        elif value:
            label += f" ({value})"
            
        G.add_node(
            node_id,
            node_type=node_type,
            line=line,
            code=code,
            label=label,
            ast_node=node
        )
        
        if parent_id is not None:
            G.add_edge(parent_id, node_id, type="ast")
            
        for child in get_ast_children(node):
            traverse_ast(child, node_id)
            
    traverse_ast(ast)
    
    def traverse_for_cfg(node):
        if not isinstance(node, dict):
            return
        node_type = get_node_type(node)
        if node_type == "FunctionDefinition":
            body = get_sub_node(node, "body", 2) if "nodeType" in node else get_sub_node(node, "body", 1) # Block is usually index 2 in compact parameters, 1 in legacy if no outputs
            if not body:
                for child in get_ast_children(node):
                    if get_node_type(child) == "Block":
                        body = child
                        break
            if body:
                build_cfg_edges(body, [], G)
        else:
            for child in get_ast_children(node):
                traverse_for_cfg(child)
                
    traverse_for_cfg(ast)
    
    def traverse_for_pdg(node):
        if not isinstance(node, dict):
            return
        node_id = node.get("id")
        if node_id is None:
            return
            
        node_type = get_node_type(node)
        
        # variable reads point to their declaration
        if node_type == "Identifier":
            ref_decl = get_referenced_declaration(node)
            if ref_decl and G.has_node(ref_decl):
                G.add_edge(ref_decl, node_id, type="data_ref")
                
        elif node_type == "Assignment":
            lhs = get_sub_node(node, "leftHandSide", 0)
            rhs = get_sub_node(node, "rightHandSide", 1)
            if lhs and rhs:
                lhs_id = lhs.get("id")
                rhs_id = rhs.get("id")
                if lhs_id and rhs_id and G.has_node(lhs_id) and G.has_node(rhs_id):
                    G.add_edge(rhs_id, lhs_id, type="data_flow")
                    
        elif node_type == "VariableDeclaration":
            init = get_sub_node(node, "initialValue", 0)
            if not init and "nodeType" in node:
                init = node.get("initialValue")
            if init:
                init_id = init.get("id")
                if init_id and G.has_node(init_id):
                    G.add_edge(init_id, node_id, type="data_flow")
                    
        elif node_type == "FunctionCall":
            arguments = get_call_arguments(node)
            for arg in arguments:
                arg_id = arg.get("id")
                if arg_id and G.has_node(arg_id):
                    G.add_edge(arg_id, node_id, type="data_flow")
                    
        for child in get_ast_children(node):
            traverse_for_pdg(child)
            
    traverse_for_pdg(ast)
    
    return G

def visualize_graph(G, save_path=None):
    """
    Helper function to visualize the graph layout using matplotlib.
    """
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.15, seed=42)
    
    nx.draw_networkx_nodes(G, pos, node_size=300, node_color="lightblue", alpha=0.8)
    
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
            width=1.5, alpha=0.7, arrowsize=10
        )
        
    labels = {}
    for n, d in G.nodes(data=True):
        ntype = d.get("node_type", "")
        if ntype in ("FunctionDefinition", "ContractDefinition", "VariableDeclaration"):
            labels[n] = d.get("label", str(n))
            
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_color="black")
    
    plt.title("Contract Multi-Relational Semantic Graph")
    plt.axis("off")
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
    plt.close()
