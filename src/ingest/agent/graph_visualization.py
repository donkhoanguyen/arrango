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

extract_subgraph_template = env.get_template("extract_subgraph_prompt.jinja")
@tool
def extract_subgraph(graph_wrapper: Any, query: str, context: str):
    """
    This tool extracts a subgraph from a given NetworkX ArangoDB graph based on
    a natural language query when we need to use NetworkX Algorithm.
    The tool dynamically generates and executes NetworkX code to retrieve
    relevant nodes and edges. 
    Additional context and tool-specific instructions help refine the extraction
    process.
    
    Args:
        graph_wrapper: A wrapper containing the graph, its schema, and its description.
        query: The original query from the user.
        context: The original context for why the user asked this query.
        tool_instruction: Further instructions derived from previous tool interactions.
        
    Returns:
        A modified graph_wrapper containing:
            - graph: The extracted subgraph.
            - schema: The schema of the extracted subgraph.
            - description: A natural language summary of the extracted subgraph.
    """
    # Initialize llm
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    
    G = graph_wrapper.graph
   

    # Prepare layout
    prompt = extract_subgraph_template.render({
        "query": query,
        "context": context,
        "full_schema": graph_wrapper.get_full_schema()
    })
    response = llm.invoke(prompt)
    layout = response.content
    print("Layout", layout)
    
    print('-'*10)
    print("\n2) Executing NetworkX code")
    
    if "python" not in layout:
        return None, "Error: You might not have generated Python code"
    layout_code =  re.sub(r"^```python\n|```$", "", layout, flags=re.MULTILINE).strip()
    
    print(layout_code)
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
                return None, "Error: unable to run custom layout code"
            attempt += 1

    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    REASON = local_vars["REASON"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)
    
    if str(FINAL_RESULT) in PRESET_LAYOUT_OPTION:
        return GraphVisualizationRequest(
            graph_wrapper,
            elements,
            FINAL_RESULT,
            node_styles,
            edge_styles
        ), f"Visualized with preset layout '{FINAL_RESULT}'\nReasoning: '{REASON}'"
    else:
        return GraphVisualizationRequest(
            graph_wrapper,
            elements,
            FINAL_RESULT,
            node_styles,
            edge_styles
        ), f"Visualized with custom layout\nReasoning: '{REASON}'"
