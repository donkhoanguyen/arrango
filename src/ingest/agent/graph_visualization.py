import json
import re
from st_link_analysis import EdgeStyle, NodeStyle, st_link_analysis
import streamlit as st
from typing import Any, Union
from langchain_openai import ChatOpenAI
import networkx as nx

from langchain_core.tools import tool
from agent import env
from agent.graph_cache import GraphWrapper

PRESET_LAYOUT_OPTION = set(["cose", "random", "grid", "circle", "concentric", "breadthfirst", "fcose", "cola"])

class GraphVisualizationRequest:
    def __init__(
        self,
        graph_wrapper: GraphWrapper,
        elements: dict,
        layout: Union[str, dict],
        node_styles: list[NodeStyle],
        edge_styles: list[EdgeStyle],
    ):
        self.graph_wrapper = graph_wrapper
        self.elements = elements
        self.layout = layout
        self.node_styles = node_styles
        self.edge_styles = edge_styles 
    
    def render(self):
        st_link_analysis(self.elements, self.layout, self.node_styles, self.edge_styles)

graph_viz_template = env.get_template("graph_visualization_prompt.jinja")
@tool
def visualize_graph(graph_wrapper: Any, query: str, context: str):
    """
    This tool is for visualizing a graph based on the user query. 
    
    You have to make sure you already choose a graph before visualizing it.
     
    Given a chosen graph, user's query, and original context on why this is asked,
    choose the most appropriate nodes, edges and their respective styles, along with
    their layout to visualize the graph.
    
    Args:
        graph_wrapper: An instance of GraphWrapper containing the graph, its name, schema, and description
        query: The original query of the user
        context: The original context for this chatbot
        
    Returns:
        An instance of GraphVisualizationRequest, to be saved into state later
    """
    # Initialize llm
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    
    G = graph_wrapper.graph
    
    # Preparing node and edge and their styles
    nodes = []
    edges = []
    
    for task_node, task_info in G.nodes(data=True):
        nodes.append({
            "data": {
                "id": task_node, 
                "label": task_info["Status"],
                "name": task_info["TaskID"],
                **task_info
            }
        })
    # Style node & edge groups
    node_styles = [
        NodeStyle("Planned", "#d3d3d3", "name", "person"),           # Orange
        NodeStyle("In Progress", "#f39c12", "name", "person"), # Green
        NodeStyle("Completed", "#2ecc71", "name", "person"), # Blue
        NodeStyle("Blocked", "#e74c3c", "name", "person"), # Amber
    ]
    for task_from, task_to in G.edges:
        edges.append({
            "data": {
                "id": f"{task_from}->{task_to}",
                "label": "Depends On",
                "source": task_from,
                "target": task_to,
            }
        })
    
    edge_styles = [
        EdgeStyle("Depends On", caption='label', directed=True),
    ]
    elements = {
        "nodes": nodes,
        "edges": edges,
    }

    # Prepare layout
    prompt = graph_viz_template.render({
        "query": query,
        "context": context,
        "full_schema": graph_wrapper.get_full_schema()
    })
    
    response = llm.invoke(prompt)
    layout = response.content
    
    # Option 1: Choose preset layout
    if layout in PRESET_LAYOUT_OPTION:
        return GraphVisualizationRequest(
            graph_wrapper,
            elements,
            layout,
            node_styles,
            edge_styles
        )
    
    # Option 2: Generate using python code
    print('-'*10)
    print("\n2) Executing NetworkX code")
    
    layout_code =  re.sub(r"^```python\n|```$", "", layout, flags=re.MULTILINE).strip()
    
    global_vars = {"G": G, "nx": nx}
    local_vars = {}

    MAX_ATTEMPTS = 3
    attempt = 1
    while attempt <= MAX_ATTEMPTS:
        print(f"Attempt #{attempt}: Running for effect...")
        try:
            exec(layout_code, global_vars, local_vars)
            break
        except Exception as e:
            print(f"EXEC ERROR: {e}")
            if attempt == MAX_ATTEMPTS:
                return "Error"
            attempt += 1

    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)
    
    return GraphVisualizationRequest(
        graph_wrapper,
        elements,
        FINAL_RESULT,
        node_styles,
        edge_styles
    ) 
