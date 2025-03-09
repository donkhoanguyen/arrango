import os
import streamlit as st
import networkx as nx
import pandas as pd
import nx_arangodb as nxadb
import re

from agent import create_new_agent

os.environ["LANGSMITH_TRACING"] = st.secrets["LANGSMITH_TRACING"]
os.environ["LANGSMITH_ENDPOINT"] = st.secrets["LANGSMITH_ENDPOINT"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
os.environ["LANGSMITH_PROJECT"] = st.secrets["LANGSMITH_PROJECT"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

from langchain_openai import ChatOpenAI
from langchain_core.messages.ai import AIMessageChunk
from typing import Literal
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from arango import ArangoClient
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, ToolMessage 

DEFAULT_CHAT_AVATAR_MAP = {
    "human": "❓",
    "ai": "💁",
}

class ChatInstance:
    def __init__(self, chatbot_id: str, context: str, request_visualize=None):
        if "GRAPH_CACHE" not in st.session_state:
            raise ValueError("Graph cache is not loaded yet, cannot start chatbot")

        self.GRAPH_CACHE = st.session_state.GRAPH_CACHE
        if chatbot_id not in st.session_state:
            st.session_state[chatbot_id] = [
                SystemMessage(
                    content=f"You are a helpful chatbot in a Project Dashboard of a human company. The user's context is this '{context}'. First, warmly welcome the user and explain quickly about what you can do, including explaining 2 or 3 type and example questions you are equpiped best to answer with the given context. Do it in under 100 words, and make sure the questions are in markdown list.",
                )
            ]
        self.chatbot_id = chatbot_id
        self.context = context
        self.agent = create_new_agent()
        self.current_state = None
        self.request_visualize = request_visualize
        self.chosen_graph_name = None

    def get_messages(self) -> list[BaseMessage]:
        return st.session_state[self.chatbot_id]

    def append_message(self, message):
        st.session_state[self.chatbot_id].append(message)
    
    def update_messages(self, messages: list[BaseMessage]):
        st.session_state[self.chatbot_id] = messages 
    
    def _callback_append_user_msg(self):
        user_msg = st.session_state[f"{self.chatbot_id}/prev_user_msg"]
        self.append_message(HumanMessage(content=user_msg))

    def process_stream(self, stream):
        for type, chunk in stream:
            if type == "messages":
                message, metadata = chunk
                if isinstance(message, ToolMessage):
                    self._render_tool_message(message)
                    yield ""
                
                if isinstance(message, AIMessageChunk):
                    if metadata["langgraph_node"] == "tools":
                        yield ""
                    else:
                        yield message.content
            elif type =="values":
                self.current_state = chunk

    def _render_tool_message(self, message: ToolMessage):
        with st.expander(f"Used tool [{message.name}]"):
            st.markdown("Tool Response:")
            st.markdown(f"```\n{message.content}\n```")

    def render(self):
        messages = self.get_messages()

        with st.container(height=500):
            # Display chat messages from history on app rerun
            for message in messages:
                print(message)
                print(message.type)
                # Skip system prompt
                if message.type == "system" or message.content == "":
                    continue

                # Render tool differently
                if message.type == "tool":
                    self._render_tool_message(message)
                    continue

                # Render user and AI message with chat tile
                with st.chat_message(message.type, avatar=DEFAULT_CHAT_AVATAR_MAP[message.type]):
                    st.markdown(message.content)
            
            # If is new chatbot, then open with an welcome
            if len(messages) == 1 or messages[-1].type == "human":
                with st.chat_message("ai", avatar=DEFAULT_CHAT_AVATAR_MAP["ai"]):
                    stream = self.get_response_stream()
                    st.write_stream(self.process_stream(stream))

                # Check final state after running
                final_state = self.current_state
                
                # Update message
                self.update_messages(final_state["messages"])
                self.chosen_graph_name = final_state["chosen_graph_name"]
                
                # If there is visualize request, then we request visualize :)
                if "visualize_request" in final_state and final_state["visualize_request"]:
                    if self.request_visualize:
                        self.request_visualize(final_state["visualize_request"])
                    else:
                        st.error("You requested a network visualization but there is no support in this chatbot to visualize here.")

            # Start accepting chat
        st.chat_input("What do you want to do today?", key=f"{self.chatbot_id}/prev_user_msg", on_submit=self._callback_append_user_msg)

    def get_response_stream(self):
        messages = self.get_messages()
        stream = self.agent.stream(
            {
                "messages": self.get_messages(),
                "graph_cache": self.GRAPH_CACHE,
                "chosen_graph_name": self.chosen_graph_name,
                "original_query": messages[-1].content,
                "original_context": self.context,
                "visualize_request": None
            },
            stream_mode=["messages", "values"]
        )
        # print_stream(stream)
        return stream
