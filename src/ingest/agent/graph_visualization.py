import json
from st_link_analysis import EdgeStyle, NodeStyle, st_link_analysis
import streamlit as st
from typing import Any, Union
from langchain_openai import ChatOpenAI
import nx_arangodb as nxadb

from langchain_core.tools import tool
from agent import env
from agent.graph_cache import GraphWrapper

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

graph_visualization = env.get_template("graph_visualization_prompt.jinja")
@tool
def choose_graph(graph_wrapper: Any, query: str, context: str):
    """
    This tool is for visualizing a graph based on the user query. 
    
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
    llm = llm.bind(response_format={"type": "json_object"})
    
    graph_list = [str(graph_cache[graph_name]) for graph_name in graph_cache] 
      
    prompt = choose_graph_template.render({
        "query": query,
        "context": context,
        "NODE_SCHEMA": NODE_SCHEMA,
        "EDGE_SCHEMA": EDGE_SCHEMA,
        "graph_list": graph_list,
    })
    
    response = llm.invoke(prompt)
    response_json = json.loads(response.content)
    
    return response_json["name"], response_json["reason"] 
    