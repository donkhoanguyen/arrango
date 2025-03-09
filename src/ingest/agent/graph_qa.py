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
        other_instruction: Further instructions derived from other tool interactions or from message history.
        
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

text_to_aql_answer_template = env.get_template("text_to_aql_answer_prompt.jinja")
@tool
def text_to_aql_to_text(
        query: str,
        context: str,
        other_instruction: str
    ):
    """
    This tool processes a natural language query on an ArangoDB graph using the ArangoGraphQAChain.

    The tool translates the query into AQL, executes it, and converts the result back into natural language.

    Args:
        query: The original query from the user.
        context: The context for why the user asked this query.
        other_instruction: Additional instructions derived from tool interactions or message history.

    Returns:
        A natural language response that answers the original query based on the executed AQL result.
    """

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])

    chain = ArangoGraphQAChain.from_llm(
    	llm=llm,
    	graph=arango_graph,
    	verbose=True,
        allow_dangerous_requests=True
    )
    
    answer_prompt = text_to_aql_answer_template.render({
        "query": query,
        "context": context,
        "other_instruction": other_instruction,
    })
    result = chain.invoke(answer_prompt)

    return str(result["result"])


# 5. Define the Text to NetworkX/cuGraph Tool
# Note: It is encouraged to experiment and improve this section! This is just a placeholder:
text_to_nx_code_template = env.get_template("text_to_nx_code_prompt.jinja")
text_to_nx_answer_template = env.get_template("text_to_nx_answer_prompt.jinja")
@tool
def text_to_nx_algorithm_to_text(
        graph_wrapper: Any,
        query: str,
        context: str,
        other_instruction: str,
    ):
    """
    This tool invokes a NetworkX algorithm on an ArangoDB graph based on a natural language query.

    You have to make sure you already CHOSE a graph before calling this tool. You should use this tool in conjunction with other tools, because this only extract subgraphs, not answer questions about it.

    The tool determines the appropriate NetworkX algorithm, executes it, and translates the results back into natural language. 
    If the query can be efficiently solved using Arango Query Language (AQL), this tool should not be used.

    Args:
        graph_wrapper: A wrapper containing the graph, its schema, and its description.
        query: The original natural language query from the user.
        context: The broader context for why the query was made.
        other_instruction: Additional instructions derived from tool interactions or message history.

    Returns:
        A response in natural language summarizing the algorithm's output, formatted to align with the original query.
    """

    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])

    ######################
    print("1) Generating NetworkX code")

    code_prompt = text_to_nx_code_template.render({
        "full_schema": graph_wrapper.get_full_schema(),
        "query": query,
        "context": context,
        "other_instruction": other_instruction
    })

    text_to_nx = llm.invoke(code_prompt).content

    text_to_nx_cleaned = re.sub(r"^```(python|python3)\n|```$", "", text_to_nx, flags=re.MULTILINE).strip()
    
    print('-'*10)
    print(text_to_nx_cleaned)
    print('-'*10)

    ######################

    print("\n2) Executing NetworkX code")
    global_vars = {"G": graph_wrapper.graph, "nx": nx}
    local_vars = {}

    MAX_ATTEMPTS = 3
    attempt = 1
    while attempt <= MAX_ATTEMPTS:
        print(f"Attempt #{attempt}: Running for effect...")
        try:
            exec(text_to_nx_cleaned, global_vars, local_vars)
            break
        except Exception as e:
            print(f"EXEC ERROR: {e}")
            if attempt == MAX_ATTEMPTS:
                return None, "Error: unable to run NetworkX to analyze graph, cannot answer query about graph"
            attempt += 1

    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)

    ######################

    print("3) Formulating final answer")

    answer_prompt = text_to_nx_answer_template.render({
        "full_schema": graph_wrapper.get_full_schema(),
        "query": query,
        "other_instruction":  other_instruction,
        "executed_code": text_to_nx,
        "FINAL_RESULT": FINAL_RESULT
    })

    nx_to_text = llm.invoke(answer_prompt).content

    return nx_to_text
