import streamlit as st
import networkx as nx
from pyvis.network import Network
import tempfile
import os

# --- Initialize session state ---
if "graph" not in st.session_state:
    st.session_state.graph = nx.Graph()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Page Layout ---
st.set_page_config(layout="wide")  # Set to full-screen mode

# Sidebar for Upload
st.sidebar.title("Upload Documents")
uploaded_files = st.sidebar.file_uploader("Upload project-related documents", accept_multiple_files=True)

if st.sidebar.button("Generate Graph"):
    st.session_state.graph = nx.erdos_renyi_graph(10, 0.3)  # Placeholder for processing logic

# Create two columns: Left (1/3) for chatbot, Right (2/3) for graph
left_col, right_col = st.columns([1, 2])

# --- Left Panel (Chatbot UI) ---
with left_col:
    st.title("Interactive GraphRAG ETL")
    st.write("Upload your project-related documents for process and modify them here.")

    # Chat History (display chat bubbles at top)
    chat_history_str = "\\n".join(st.session_state.chat_history)
    st.text_area("", chat_history_str, height=300, disabled=True)

    # User input for chatbot at the bottom
    user_input = st.text_input("You:", "")
    if st.button("Send"):
        if user_input:
            response = f"Processing: {user_input}"  # Placeholder chatbot response
            st.session_state.chat_history.append(f"You: {user_input}")
            st.session_state.chat_history.append(f"Bot: {response}")

# --- Right Panel (Graph Visualization) ---
with right_col:
    # st.title("Graph Visualization")

    # Save Pyvis network to an HTML file
    def draw_graph(graph):
        net = Network(height="700px", width="100%", notebook=False, bgcolor="#ffffff", font_color="black")
        net.from_nx(graph)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            net.save_graph(tmp_file.name)
            return tmp_file.name

    if st.session_state.graph.nodes:
        graph_html = draw_graph(st.session_state.graph)
        with open(graph_html, "r", encoding="utf-8") as file:
            st.components.v1.html(file.read(), height=700, scrolling=False)
        os.unlink(graph_html)  # Cleanup
    else:
        st.write("No graph to display. Upload files and generate a graph.")