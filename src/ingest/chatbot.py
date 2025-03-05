import streamlit as st
from openai import OpenAI
# from streamlit_float import float_css_helper, float_parent

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

DEFAULT_CHAT_AVATAR_MAP = {
    "user": "❓",
    "assistant": "💁",
}

class ChatInstance:
    def __init__(self, chatbot_id: str, context: str):
        if chatbot_id not in st.session_state:
            st.session_state[chatbot_id] = [
                {
                    "role": "system",
                    "content": f"You are a helpful chatbot in a Project Dashboard of a human company. The user's context is this '{context}'. First, warmly welcome the user and explain quickly about what you can do, including explaining 2 or 3 type and example questions you are equpiped best to answer with the given context.",
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
                    response = st.write_stream(stream)
                self.append_message({"role": "assistant", "content": response})

            # Start accepting chat
        st.chat_input("What do you want to do today?", key=f"{self.chatbot_id}/prev_user_msg", on_submit=self._callback_append_user_msg)

    def get_response_stream(self):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in self.get_messages()
            ],
            stream=True,
        )
        return stream

    def chat(self, query):
        self.append_message({"role": "user", "content": query})

