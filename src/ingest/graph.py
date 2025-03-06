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

def topo_sort_layered_layout(G, fit=True, padding=30, spacing_factor=1, animate=False, animation_duration=500):
    """
    Converts a NetworkX directed graph's topological sort into a layered layout for Cytoscape.js.
    
    :param G: A directed graph (DiGraph) from NetworkX
    :param fit: Whether to fit the layout to the viewport (default True)
    :param padding: Padding on fit (default 30)
    :param spacing_factor: Factor for spacing between nodes (default 1)
    :param animate: Whether to animate the node positioning (default False)
    :param animation_duration: Duration of animation in ms (default 500)
    :return: A dictionary with Cytoscape.js layout options
    """
    # layers = layered_topo_sort(G)# Get the layers from the peeling method
    layers = nx.topological_generations(G) 
    print(layers)
    # Create positions for Cytoscape.js with nodes positioned row by row
    positions = {}
    layer_height = -100  # Height for each layer (adjust as needed)
    
    for level, nodes in enumerate(layers):
        layer_width = len(nodes)  # Number of nodes in the current layer
        vertical_position = level * layer_height
        horizontal_spacing = 100  # Horizontal spacing between nodes in the same layer
        
        for i, node in enumerate(nodes):
            positions[node] = {
                'x': (i - (layer_width // 2)) * horizontal_spacing,  # Position nodes evenly within the layer
                'y': vertical_position  # Position layers vertically
            }
    
    # Cytoscape.js layout options
    layout_options = {
        'name': 'preset',
        'positions': positions,  # Map of node ids to positions
        'zoom': None,  # Default zoom level
        'pan': None,  # Default pan level
        'fit': fit,  # Whether to fit to viewport
        'padding': padding,  # Padding on fit
        'spacingFactor': spacing_factor,  # Expand or compress the layout area
        'animate': animate,  # Whether to animate node positions
        'animationDuration': animation_duration,  # Duration of animation
        'animationEasing': None,  # Default easing for animation
        'ready': None,  # Callback when layout is ready
        'stop': None,  # Callback when layout stops
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
