import re
from st_link_analysis import EdgeStyle, NodeStyle, st_link_analysis
import streamlit as st
from typing import Any
from langchain_openai import ChatOpenAI
import networkx as nx

from langchain_core.tools import tool
from agent import env
from agent.graph_cache import GraphWrapper

PRESET_LAYOUT_OPTION = set(["cose", "random", "grid", "circle", "concentric", "breadthfirst", "fcose", "cola"])

extract_subgraph_template = env.get_template("extract_subgraph_prompt.jinja")
@tool
def extract_subgraph(
        graph_wrapper: Any,
        query: str,
        context: str,
        other_instruction: str
    ):
    """
    This tool extracts a subgraph from a given NetworkX graph based on a natural language query.
    
    The tool dynamically generates and executes NetworkX code to retrieve relevant nodes and edges. 
    Additional context and further instructions help refine the extraction process.
    
    Args:
        graph_wrapper: A wrapper containing the graph, its schema, and its description.
        query: The original query from the user.
        context: The original context for why the user asked this query.
        other_instruction: Further instructions derived from other tool interactions.
        
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
        "graph_name": graph_wrapper.name,
        "full_schema": graph_wrapper.get_full_schema(),
        "graph_description": graph_wrapper.description,
        "query": query,
        "context": context,
        "other_instruction": other_instruction,
    })
    print(prompt)
    response = llm.invoke(prompt)
    layout = response.content

    print('-'*10)
    print("\n2) Executing NetworkX code")
    
    if "python" not in layout:
        return None, "Error: You might not have generated Python code"
    layout_code =  re.sub(r"^```python\n|```$", "", layout, flags=re.MULTILINE).strip()
    
    print(layout_code)
    global_vars = {"G_main": G.copy(), "nx": nx}
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
                return None, "Error: unable to run extract subgraph code, no subgraph was created"
            attempt += 1

    print('-'*10)
    GRAPH_NAME = local_vars["GRAPH_NAME"]
    GRAPH_SCHEMA = local_vars["GRAPH_SCHEMA"]
    GRAPH_DESCRIPTION = local_vars["GRAPH_DESCRIPTION"]
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    FINAL_RESULT.name = GRAPH_NAME
    REASON = local_vars["REASON"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)
    
    subgraph_wrapper = GraphWrapper(
        None,
        FINAL_RESULT,
        GRAPH_NAME,
        GRAPH_SCHEMA,
        GRAPH_DESCRIPTION
    )

    return subgraph_wrapper, f"Succesfully extracted subgraph {subgraph_wrapper}\nReason: {REASON}\nNOTE: this will override the current chosen_graph_name with the new graph {subgraph_wrapper.name}"
