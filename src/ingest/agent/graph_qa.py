import re
from st_link_analysis import EdgeStyle, NodeStyle, st_link_analysis
import streamlit as st
from typing import Any
from langchain_openai import ChatOpenAI
import networkx as nx

from langchain_core.tools import tool
from langchain_community.chains.graph_qa.arangodb import ArangoGraphQAChain, ArangoGraph
from agent import env
from agent.graph_cache import GraphWrapper
from database import db as adb


arango_graph = ArangoGraph(adb)

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

# 4. Define the Text to AQL Tool
# Reference: https://python.langchain.com/docs/integrations/graphs/arangodb/
# Reference: https://python.langchain.com/api_reference/community/chains/langchain_community.chains.graph_qa.arangodb.ArangoGraphQAChain.html
# Note: It is encouraged to experiment and improve this section! This is just a placeholder:

@tool
def text_to_aql_to_text(graph_wrapper, query: str, ):
    """This tool is available to invoke the
    ArangoGraphQAChain object, which enables you to
    translate a Natural Language Query into AQL, execute
    the query, and translate the result back into Natural Language.
    """

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

    chain = ArangoGraphQAChain.from_llm(
    	llm=llm,
    	graph=arango_graph,
    	verbose=True,
        allow_dangerous_requests=True
    )
    
    result = chain.invoke(query)

    return str(result["result"])


# 5. Define the Text to NetworkX/cuGraph Tool
# Note: It is encouraged to experiment and improve this section! This is just a placeholder:

@tool
def text_to_nx_algorithm_to_text(query):
    """This tool is available to invoke a NetworkX Algorithm on
    the ArangoDB Graph. You are responsible for accepting the
    Natural Language Query, establishing which algorithm needs to
    be executed, executing the algorithm, and translating the results back
    to Natural Language, with respect to the original query.

    If the query (e.g traversals, shortest path, etc.) can be solved using the Arango Query Language, then do not use
    this tool.
    """

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")

    ######################
    print("1) Generating NetworkX code")

    text_to_nx = llm.invoke(f"""
    I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}

    I have the following graph analysis query: {query}.

    Generate the Python Code required to answer the query using the `G_adb` object.

    Be very precise on the NetworkX algorithm you select to answer this query. Think step by step.

    Only assume that networkx is installed, and other base python dependencies.

    Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.

    Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.

    Make sure that `FINAL_RESULT` stores a short & consice answer. Avoid setting this variable to a long sequence.

    Your code:
    """).content

    text_to_nx_cleaned = re.sub(r"^```python\n|```$", "", text_to_nx, flags=re.MULTILINE).strip()
    
    print('-'*10)
    print(text_to_nx_cleaned)
    print('-'*10)

    ######################

    print("\n2) Executing NetworkX code")
    global_vars = {"G_adb": G_adb, "nx": nx}
    local_vars = {}

    try:
        exec(text_to_nx_cleaned, global_vars, local_vars)
        text_to_nx_final = text_to_nx
    except Exception as e:
        print(f"EXEC ERROR: {e}")
        return f"EXEC ERROR: {e}"

        # TODO: Consider experimenting with a code corrector!
        attempt = 1
        MAX_ATTEMPTS = 3

        # while attempt <= MAX_ATTEMPTS
            # ...

    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)

    ######################

    print("3) Formulating final answer")

    nx_to_text = llm.invoke(f"""
        I have a NetworkX Graph called `G_adb`. It has the following schema: {arango_graph.schema}

        I have the following graph analysis query: {query}.

        I have executed the following python code to help me answer my query:

        ---
        {text_to_nx_final}
        ---

        The `FINAL_RESULT` variable is set to the following: {FINAL_RESULT}.

        Based on my original Query and FINAL_RESULT, generate a short and concise response to
        answer my query.
        
        Your response:
    """).content

    return nx_to_text