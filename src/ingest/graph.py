import networkx as nx
import networkx as nx

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
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("The graph is not a Directed Acyclic Graph (DAG)")

    # Get the topological sort of the graph
    topological_order = list(nx.topological_sort(G))
    
    # Create a dictionary to store nodes grouped by their layer/level
    layers = {}
    for node in topological_order:
        level = len(list(nx.ancestors(G, node)))  # Number of ancestors gives the depth level
        if level not in layers:
            layers[level] = []
        layers[level].append(node)

    # Create positions for Cytoscape.js with nodes positioned row by row
    positions = {}
    layer_height = 100  # Height for each layer (adjust as needed)
    max_layer_width = max(len(layer) for layer in layers.values())  # Find the widest layer
    
    for level, nodes in layers.items():
        layer_width = len(nodes)  # Number of nodes in the current layer
        vertical_position = level * layer_height
        horizontal_spacing = 50 # Horizontal spacing between nodes in the same layer
        
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
