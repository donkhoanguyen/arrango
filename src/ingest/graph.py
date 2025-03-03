from collections import deque
import networkx as nx
import networkx as nx

def layered_topo_sort(G):
    """
    Performs a topological sort on a directed acyclic graph (DAG) using the peeling technique.
    
    :param G: Directed graph (DiGraph) from NetworkX
    :return: A list of layers, where each layer is a list of nodes.
    """
    # Ensure the graph is a DAG
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("The graph is not a Directed Acyclic Graph (DAG)")
    
    # In-degree calculation: count the number of incoming edges for each node
    in_degree = {node: G.in_degree(node) for node in G.nodes}
    
    layers = []
    
    # Use a queue to keep track of nodes with zero in-degree (ready to be processed)
    queue = deque([node for node, degree in in_degree.items() if degree == 0])
    
    while queue:
        layer = []
        
        # Process all nodes with zero in-degree at the current level
        for _ in range(len(queue)):
            node = queue.popleft()
            layer.append(node)
            
            # For all outgoing edges, reduce in-degree of target nodes
            for neighbor in G.neighbors(node):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Add the processed layer to the result
        layers.append(layer)
    
    return layers

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
    layers = layered_topo_sort(G.copy())  # Get the layers from the peeling method
    
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
