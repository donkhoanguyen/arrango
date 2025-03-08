from typing import Annotated, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END

from agent.graph_cache import GraphWrapper
from agent.utils import get_weather

# Set up tools
tools = [get_weather]
tools_by_name = {tool.name: tool for tool in tools}

# Set up OpenAI model
model = ChatOpenAI(model="gpt-4o", temperature=0.7)
model  = model.bind_tools(tools)
class AgentState:
    # List of messages so far
    messages: Annotated[Sequence[BaseMessage], add_messages]

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

# Define our tool node
def tool_node(state: AgentState):
    """logic here"""
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        print('STATE:', state)
        # print("TOOL CALL", tool_call)
        tool_name = tool_call["name"]
        if tool_name == "choose_graph":
            tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            # print("CHOOSE GRAPH GOT OUTPUT:", tool_result)
            outputs.append(
                ToolMessage(
                    # content=json.dumps(tool_result),
                    content = tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            return {'G_adb': tool_result, "messages": outputs}
        # print("returned", tool_result)
        if tool_name == "create_cpm_table":
            G_adb = state["G_adb"]
            tool_result = tools_by_name[tool_call["name"]].invoke({"G_adb": G_adb})
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            return {'cpm_df': tool_result, "messages": outputs}
        if tool_name == "ask_cpm_question":
            cpm_df = state["cpm_df"]
            tool_result = tools_by_name[tool_call["name"]].invoke({"df": cpm_df, "question" :tool_call["args"]})
            outputs.append(
                ToolMessage(
                    content=tool_result,
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            state["messages"] = outputs
            return state

# Define the node that calls the model
def call_model(
        state: AgentState,
        config: RunnableConfig,
    ):
    print("new state", state)
    """logic here"""
    # Get the question 
    system_prompt = SystemMessage(
        "You are a helpful AI assistant that will be querying in our graph databases. \
        A typical workflow will include: \
            - Going into the database to select the right graph \
            - Perform the calculation / analysis required to generate desired output in either natural language or a dataframe \
            - If necessary, further analyze the output dataframe to formulate answers to the user's question \
        "
    )
    response = model.invoke([system_prompt] + state["messages"], config)
    # We return a list, because this will get added to the existing list
    state["messages"] = [response]
    return {"messages": [response], "question": "fuck you"}


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