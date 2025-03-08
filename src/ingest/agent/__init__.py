from typing import Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from agent.graph_cache import GraphWrapper


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
