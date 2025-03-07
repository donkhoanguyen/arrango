from collections import deque
import networkx as nx

SENIORITY_LAYER_MAP = {
    "Director": 0,
    "Vice-Director": 0,
    "Lead": 1,
    "Senior": 2,
    "Mid-Level": 3,
    "Junior": 4
}

def extract_dag_subgraphs(G):
    """Extracts all DAG subgraphs from a directed graph."""
    dag_subgraphs = []
    single_nodes = []
    
    for component in nx.weakly_connected_components(G):
        subgraph = G.subgraph(component).copy()
        if len(subgraph) == 1:
            single_nodes.append(next(iter(subgraph.nodes())))
        elif nx.is_directed_acyclic_graph(subgraph):
            dag_subgraphs.append(subgraph)

    return dag_subgraphs, single_nodes

def topo_sort_layered_layout(G, fit=True, padding=30, spacing_factor=1, animate=False, animation_duration=500):
    """
    Converts a NetworkX directed graph into a layered layout for Cytoscape.js, 
    extracting and visualizing separate DAGs distinctly.
    
    :param G: A directed graph (DiGraph) from NetworkX
    :return: A dictionary with Cytoscape.js layout options
    """
    dag_subgraphs, single_nodes = extract_dag_subgraphs(G.copy())
    positions = {}
    
    layer_height = -100  # Vertical spacing between layers
    dag_x_offset = 0      # Horizontal offset for separating DAGs
    dag_spacing = 100     # Spacing between DAGs
    single_node_spacing = -100  # Spacing for single-node grid

    # Process each DAG separately
    for dag in dag_subgraphs:
        layers = list(nx.topological_generations(dag))
        
        max_layer_width = max(len(layer) for layer in layers)  # Widest layer
        horizontal_spacing = 100  # Spacing between nodes in the same layer
        
        for level, nodes in enumerate(layers):
            vertical_position = level * layer_height
            layer_width = len(nodes)
            
            for i, node in enumerate(nodes):
                positions[node] = {
                    'x': dag_x_offset + (i - layer_width // 2) * horizontal_spacing,
                    'y': vertical_position
                }
        
        dag_x_offset += max_layer_width * horizontal_spacing + dag_spacing  # Shift for next DAG

    # Position single nodes in a grid
    grid_width = int(len(single_nodes) ** 0.5) or 1  # Square-like grid
    for i, node in enumerate(single_nodes):
        row, col = divmod(i, grid_width)
        positions[node] = {
            'x': dag_x_offset + col * single_node_spacing,
            'y': row * single_node_spacing
        }

    # Cytoscape.js layout options
    layout_options = {
        'name': 'preset',
        'positions': positions,
        'fit': fit,
        'padding': padding,
        'spacingFactor': spacing_factor,
        'animate': animate,
        'animationDuration': animation_duration,
    }

    return layout_options

def layered_topo_sort_by_seniority(G):
    """
    Layer employees based on their seniority in a hierarchical topological order.

    :param G: NetworkX DiGraph representing employee hierarchy
    :return: List of layers where each layer is a list of employee nodes at the same level
    """
    layers = {0: [], 1: [], 2: [], 3: [], 4: []}  # Map to store layers based on seniority levels
    
    # Process each node and place it into the appropriate layer
    for node, data in G.nodes(data=True):
        layer = SENIORITY_LAYER_MAP.get(data['Seniority'], 3)  # Default to JuniorEmployee layer
        layers[layer].append(node)
    
    # Sort nodes within each layer if necessary (for example, by name or any other attribute)
    # Here we just return the layers as is
    return [layers[i] for i in range(5) if layers[i]]

def get_layout_for_seniority_layers(G):
    """
    Convert the layered employee graph into a layout dict for Cytoscape.js based on seniority layers.

    :param G: NetworkX DiGraph representing the employee hierarchy
    :return: Cytoscape.js layout dict with positions of nodes for visualization
    """
    layers = layered_topo_sort_by_seniority(G)  # Get employees layered by seniority
    
    # Define the layout
    positions = {}
    layer_height = 100  # Vertical distance between layers
    horizontal_spacing = 100  # Horizontal spacing between nodes in the same layer
    
    for level, nodes in enumerate(layers):
        layer_width = len(nodes)
        vertical_position = level * layer_height
        
        for i, node in enumerate(nodes):
            # Position nodes evenly within the layer
            positions[node] = {
                'x': (i - (layer_width // 2)) * horizontal_spacing,
                'y': vertical_position
            }
    
    # Return Cytoscape layout options
    layout_options = {
        'name': 'preset',
        'positions': positions,
        'zoom': None,
        'pan': None,
        'fit': True,
        'padding': 30,
        'spacingFactor': 1,
        'animate': False,
        'animationDuration': 500,
        'animationEasing': None,
        'ready': None,
        'stop': None,
    }

    return layout_options
