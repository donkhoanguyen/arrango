import streamlit as st
from typing import Annotated, Sequence, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END

import pandas as pd
from typing import (
    Annotated,
    Sequence,
    TypedDict,
    Optional
)

# Set up jinja
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader("./agent/prompt"))

from agent.graph_cache import GraphWrapper, choose_graph
from agent.utils import get_weather
from agent.graph_visualization import visualize_graph
from agent.graph_qa import extract_subgraph, text_to_aql_to_text, text_to_nx_algorithm_to_text
from agent.cpm import create_cpm_table, ask_cpm_question
from agent.hits import create_hits_table, ask_hits_question

# Set up tools
tools = [
    get_weather,
    choose_graph,
    visualize_graph,
    create_cpm_table,
    ask_cpm_question,
    create_hits_table,
    ask_hits_question,
    extract_subgraph,
    text_to_aql_to_text,
    text_to_nx_algorithm_to_text,
]
tools_by_name = {tool.name: tool for tool in tools}

# Set up OpenAI model
model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=st.secrets["OPENAI_API_KEY"])
model  = model.bind_tools(tools, parallel_tool_calls=False)
class AgentState(TypedDict):
    # List of messages so far
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # The dataframe we are working with
    df: Optional[pd.DataFrame]  # The resulting (CPM, hits?) dataframe

    # Cache of all graph already loaded
    graph_cache: dict[str, GraphWrapper]
    
    # Name of the graph that we would like to work with after
    chosen_graph_name: str
    
    # The original user query
    original_query: str

    # The original context of the component where this Agent was called upon
    original_context: str

    # TODO: For visualization of graph
    visualize_request: dict[str, str]

    # # topic: name of employee or name of task
    # topic: str

# Define our tool node
def tool_node(state: AgentState):
    """logic here"""
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        print("Current state graph name in tool :", state["chosen_graph_name"])
        # print("TOOL CALL", tool_call)
        tool_name = tool_call["name"]
        print("calling tool", tool_name)
        print("args:", tool_call["args"])
        if tool_name == "choose_graph":
            graph_name, reason = choose_graph.invoke(
                input= {
                    "graph_cache": state["graph_cache"],
                    "query": state["original_query"],
                    "context": state["original_context"],
                    "other_instruction": tool_call["args"].get("other_instruction", "")
                }
            )
            outputs.append(
                ToolMessage(
                    content=f"Graph '{graph_name}' has been chosen with reason '{reason}'",
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            state["messages"] = outputs
            state["chosen_graph_name"] = graph_name
            return state
        
        # elif tool_name == "search_emp_info":
        #     topic = state["topic"]
        #     tool_result = tools_by_name[tool_call["name"]].invoke({"topic": topic})
        #     state["topic"] = tool_result
        #     return state
        
        elif tool_name == "visualize_graph":
            graph_wrapper = state["graph_cache"].get(state["chosen_graph_name"], None)
            print("chosen graph name", state["chosen_graph_name"])
            print("chosen bitch", graph_wrapper)
            if not graph_wrapper:
                outputs.append(
                    ToolMessage(
                        content = "You have not chosen a graph yet, make sure to use choose_graph first!",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                graph_viz_request, message = visualize_graph.invoke(input={
                    "graph_wrapper": graph_wrapper,
                    "query": state["original_query"],
                    "context": state["original_context"],
                    "other_instruction": tool_call["args"].get("other_instruction", ""),
                })
                
                state["visualize_request"] = graph_viz_request
                outputs.append(
                    ToolMessage(
                        content=message,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
                
            state["messages"] = outputs
            return state
        
        elif tool_name == "create_cpm_table":
            graph_wrapper = state["graph_cache"].get(state["chosen_graph_name"], None)
            # No proceed if no graph chosen
            if not graph_wrapper:
                outputs.append(
                    ToolMessage(
                        content = "You have not chosen a graph yet, make sure to use choose_graph first!",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                tool_result = tools_by_name[tool_call["name"]].invoke({"G_adb": graph_wrapper.graph})
                outputs.append(
                    ToolMessage(
                        content="created cpm table and can now ask cpm questions on this table",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
                state["df"] = tool_result
            state["messages"] = outputs
            return state
        
        elif tool_name == "ask_cpm_question":
            cpm_df = state["df"]
            context = state["original_context"]
            tool_result = tools_by_name[tool_call["name"]].invoke({"df": cpm_df, 
                                                                   "question" :tool_call["args"],
                                                                   "context": context})
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )

            state["messages"] = outputs
            return state
        
        elif tool_name == "create_hits_table":
            graph_wrapper = state["graph_cache"].get(state["chosen_graph_name"], None)
            
            if not graph_wrapper:
                outputs.append(
                    ToolMessage(
                        content = "You have not chosen a graph yet, make sure to use choose_graph first!",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                tool_result = tools_by_name[tool_call["name"]].invoke({"G_adb": graph_wrapper.graph})
                outputs.append(
                    ToolMessage(
                        content="created hits table",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
                state["df"] = tool_result
            state["messages"] = outputs
            return state
        
        elif tool_name == "ask_hits_question":
            hits_df = state["df"]
            context = state["original_context"]
            tool_result = tools_by_name[tool_call["name"]].invoke({"df": hits_df, 
                                                                   "question" :tool_call["args"],
                                                                   "context": context})
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            state["messages"] = outputs
            return state
        elif tool_name == "extract_subgraph":
            graph_wrapper = state["graph_cache"].get(state["chosen_graph_name"], None)
            
            # No proceed if no graph chosen
            if not graph_wrapper:
                outputs.append(
                    ToolMessage(
                        content = "You have not chosen a graph yet, make sure to use choose_graph first!",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                # Start
                subgraph_wrapper, message = extract_subgraph.invoke(input={
                    "graph_wrapper": graph_wrapper,
                    "query": state["original_query"],
                    "context": state["original_context"],
                    "other_instruction": tool_call["args"].get("other_instruction", "")
                })
                if not subgraph_wrapper:
                    outputs.append(
                        ToolMessage(
                            content = message,
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                    )
                else:
                    print("Succesfully extracted", subgraph_wrapper)
                    state["graph_cache"][subgraph_wrapper.name] = subgraph_wrapper
                    outputs.append(
                        ToolMessage(
                            content=message,
                            name=tool_call["name"],
                            tool_call_id=tool_call["id"],
                        )
                    )
                    state["chosen_graph_name"] = subgraph_wrapper.name
                
            state["messages"] = outputs
            return state
        elif tool_name == "text_to_aql_to_text":
            result = text_to_aql_to_text.invoke(input={
                "query": state["original_query"],
                "context": state["original_context"],
                "other_instruction": tool_call["args"].get("other_instruction", "")
            })
            outputs.append(
                ToolMessage(
                    content=result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            ) 
            state["messages"] = outputs
            return state
        elif tool_name == "text_to_nx_algorithm_to_text":
            graph_wrapper = state["graph_cache"].get(state["chosen_graph_name"], None)
            
            # No proceed if no graph chosen
            if not graph_wrapper:
                outputs.append(
                    ToolMessage(
                        content = "You have not chosen a graph yet, make sure to use choose_graph first!",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
            else:
                # Start
                result = text_to_nx_algorithm_to_text.invoke(input={
                    "graph_wrapper": graph_wrapper,
                    "query": state["original_query"],
                    "context": state["original_context"],
                    "other_instruction": tool_call["args"].get("other_instruction", "")
                })
                outputs.append(
                    ToolMessage(
                        content=result,
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"],
                    )
                )
                
            state["messages"] = outputs
            return state
        # else:
        #     tool_result = tools_by_name[tool_name].invoke(tool_call["args"])
        #     outputs.append(
        #         ToolMessage(
        #             content = tool_result,
        #             name=tool_call["name"],
        #             tool_call_id=tool_call["id"],
        #         )
        #     )
        #     print(tool_call["id"])
        #     state["messages"] = outputs
        #     return state

agent_system_prompt_template = env.get_template("agent_system_prompt.jinja")
# Define the node that calls the model
def call_model(
        state: AgentState,
        config: RunnableConfig,
    ):

    graph_info = "None" if not state["chosen_graph_name"] else str(state["graph_cache"][state["chosen_graph_name"]])

    # Get the question 
    system_prompt = SystemMessage(agent_system_prompt_template.render({
        "original_query": state["original_query"],
        "original_context": state["original_context"],
        "graph_info": graph_info
    }))

    print(system_prompt)
    # Get response
    response = model.invoke([system_prompt] + state["messages"], config)
    
    # Persist state
    state["messages"] = [response]
    return state


# Define the conditional edge that determines whether to continue or not
def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"

def create_new_agent():
    # Define a new graph
    workflow = StateGraph(AgentState)

    # Define the two nodes we will cycle between
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    # Set the entrypoint as `agent`
    # This means that this node is the first one called
    workflow.set_entry_point("agent")

    # We now add a conditional edge
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )

    # We now add a normal edge from `tools` to `agent`.
    # This means that after `tools` is called, `agent` node is called next.
    workflow.add_edge("tools", "agent")

    # Now we can compile and visualize our graph
    graph = workflow.compile()
    
    return graph
