import os
import streamlit as st

os.environ["LANGSMITH_TRACING"] = st.secrets["LANGSMITH_TRACING"]
os.environ["LANGSMITH_ENDPOINT"] = st.secrets["LANGSMITH_ENDPOINT"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
os.environ["LANGSMITH_PROJECT"] = st.secrets["LANGSMITH_PROJECT"]

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_core.messages.ai import AIMessageChunk
from typing import Literal
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=st.secrets["OPENAI_API_KEY"])


# Tool 1: Generate image metadata with @tool decorator
@tool
def generate_image_metadata(image_url: str):
    """Mock function to return image metadata."""
    metadata = {
        "url": image_url,
        "width": 1920,
        "height": 1080,
        "format": "JPEG",
        "size_kb": 350  # Image size in KB
    }
    return metadata  # Returns a dictionary

# Tool 2: Analyze image metadata with @tool decorator
@tool
def analyze_image_metadata(metadata: dict):
    """Check if image meets certain criteria."""
    if metadata["width"] >= 1280 and metadata["height"] >= 720 and metadata["size_kb"] <= 500:
        return {"status": "Valid", "message": "Image meets resolution and size requirements."}
    else:
        return {"status": "Invalid", "message": "Image does not meet the required specs."}


@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")


tools = [get_weather, generate_image_metadata, analyze_image_metadata]
agent = create_react_agent(model, tools=tools)

DEFAULT_CHAT_AVATAR_MAP = {
    "user": "❓",
    "assistant": "💁",
}

def process_stream(stream):
    for chunk in stream:
        message = chunk[0]
        if isinstance(message, ToolMessage):
            with st.expander(f"Used tool [{message.name}]"):
                st.markdown("Tool Response:")
                st.markdown(f"```\n{message.content}\n```")
            yield ""
        
        if isinstance(message, AIMessageChunk):
            yield message.content

class ChatInstance:
    def __init__(self, chatbot_id: str, context: str):
        if chatbot_id not in st.session_state:
            st.session_state[chatbot_id] = [
                {
                    "role": "system",
                    "content": f"You are a helpful chatbot in a Project Dashboard of a human company. The user's context is this '{context}'. First, warmly welcome the user and explain quickly about what you can do, including explaining 2 or 3 type and example questions you are equpiped best to answer with the given context. Do it in under 100 words, and make sure the questions are in markdown list.",
                }
            ]
        self.chatbot_id = chatbot_id
        self.context = context

    def get_messages(self):
        return st.session_state[self.chatbot_id]

    def append_message(self, message):
        st.session_state[self.chatbot_id].append(message)

    def _callback_append_user_msg(self):
        user_msg = st.session_state[f"{self.chatbot_id}/prev_user_msg"]
        self.append_message({"role": "user", "content": user_msg})

    def render(self):
        messages = self.get_messages()

        with st.container(height=500):
            # Display chat messages from history on app rerun
            for message in messages:
                # Skip system prompt
                if message["role"] == "system":
                    continue
                with st.chat_message(message["role"], avatar=DEFAULT_CHAT_AVATAR_MAP[message["role"]]):
                    st.markdown(message["content"])
            
            # If is new chatbot, then open with an welcome
            if len(messages) == 1 or messages[-1]["role"] == "user":
                with st.chat_message("assistant", avatar=DEFAULT_CHAT_AVATAR_MAP["assistant"]):
                    stream = self.get_response_stream()
                    response = st.write_stream(process_stream(stream))
                self.append_message({"role": "assistant", "content": response})

            # Start accepting chat
        st.chat_input("What do you want to do today?", key=f"{self.chatbot_id}/prev_user_msg", on_submit=self._callback_append_user_msg)

    def get_response_stream(self):
        stream = agent.stream(
            {
                "messages": self.get_messages(),
            },
            stream_mode="messages"
        )
        # print_stream(stream)
        return stream

    def chat(self, query):
        self.append_message({"role": "user", "content": query})
