import torch
import torch.nn as nn
import torch.nn.functional as F

# AST node types for the one-hot node features
NODE_TYPES = [
    'ContractDefinition', 'FunctionDefinition', 'VariableDeclaration', 
    'Block', 'IfStatement', 'ForStatement', 'WhileStatement', 
    'ExpressionStatement', 'VariableDeclarationStatement', 'Return', 
    'Identifier', 'Assignment', 'FunctionCall', 'BinaryOperation', 
    'MemberAccess', 'Literal', 'ParameterList', 'Parameter', 
    'ElementaryTypeName', 'Mapping'
]
NODE_TYPE_TO_IDX = {nt: idx for idx, nt in enumerate(NODE_TYPES)}
NUM_NODE_TYPES = len(NODE_TYPES) + 1 # +1 for 'Other'

class GATLayer(nn.Module):
    """
    Pure PyTorch implementation of the Graph Attention Network (GAT) layer.
    Requires no C++ compilation dependencies (like torch-scatter or torch-geometric).
    """
    def __init__(self, in_features, out_features, dropout=0.1, alpha=0.2):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.dropout = dropout
        self.alpha = alpha

        self.W = nn.Linear(in_features, out_features, bias=False)
        self.a = nn.Parameter(torch.empty(size=(2 * out_features, 1)))
        
        nn.init.xavier_uniform_(self.W.weight.data, gain=1.414)
        nn.init.xavier_uniform_(self.a.data, gain=1.414)

        self.leakyrelu = nn.LeakyReLU(self.alpha)

    def forward(self, x, edge_index):
        # x: [N, in_features]
        # edge_index: [2, E] where edge_index[0] is source, edge_index[1] is target
        N = x.size(0)
        h = self.W(x) # [N, out_features]

        if edge_index.size(1) == 0:
            # no edges: return the projection as is
            return h

        source, target = edge_index[0], edge_index[1] # [E], [E]

        h_source = h[source] # [E, out_features]
        h_target = h[target] # [E, out_features]

        a_input = torch.cat([h_source, h_target], dim=1) # [E, 2 * out_features]
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(1)) # [E]

        # softmax over the incoming edges of each target node
        e_exp = torch.exp(e - e.max())
        sum_exp = torch.zeros(N, device=x.device)
        sum_exp.index_add_(0, target, e_exp)
        sum_exp = sum_exp + 1e-10
        
        alpha = e_exp / sum_exp[target] # [E]
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)

        weighted_h = h_source * alpha.unsqueeze(1) # [E, out_features]
        out = torch.zeros(N, self.out_features, device=x.device)
        out.index_add_(0, target, weighted_h)

        return out

class SmartContractGNN(nn.Module):
    """
    GNN Model for smart contract vulnerability classification (node level and graph level).
    """
    def __init__(self, in_dim=25, hidden_dim=64, num_classes=3):
        super().__init__()
        self.gat1 = GATLayer(in_dim, hidden_dim, dropout=0.1)
        self.gat2 = GATLayer(hidden_dim, hidden_dim, dropout=0.1)
        
        # node-level head
        self.node_classifier = nn.Linear(hidden_dim, num_classes)
        
        # graph-level head
        self.graph_classifier = nn.Linear(hidden_dim, num_classes)

    def forward(self, x, edge_index):
        # x: [N, in_dim]
        # edge_index: [2, E]
        h1 = F.elu(self.gat1(x, edge_index))
        h2 = self.gat2(h1, edge_index) # [N, hidden_dim]

        node_logits = self.node_classifier(h2) # [N, num_classes]

        graph_emb = torch.mean(h2, dim=0, keepdim=True) # [1, hidden_dim]
        graph_logits = self.graph_classifier(graph_emb).squeeze(0) # [num_classes]

        return node_logits, graph_logits

def extract_node_features(node_data):
    """
    Utility to convert networkx node attribute dict to a 25-dimensional feature list.
    """
    node_type = node_data.get("node_type", "Other")
    code = node_data.get("code", "").lower()
    
    # one-hot AST node type (21 dims)
    features = [0.0] * NUM_NODE_TYPES
    idx = NODE_TYPE_TO_IDX.get(node_type, len(NODE_TYPES))
    features[idx] = 1.0
    
    # four keyword indicator flags
    has_call = 1.0 if any(kw in code for kw in (".call", "transfer", "send")) else 0.0
    has_timestamp = 1.0 if "block.timestamp" in code or "now" in code else 0.0
    has_arithmetic = 1.0 if (node_type == "BinaryOperation" and any(op in code for op in ("+", "-", "*", "/"))) else 0.0
    has_state_write = 1.0 if node_type in ("Assignment", "VariableDeclaration") and any(op in code for op in ("=", "+=", "-=")) else 0.0
    
    features.extend([has_call, has_timestamp, has_arithmetic, has_state_write])
    return features
