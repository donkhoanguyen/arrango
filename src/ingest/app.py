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

# --- Sidebar for File Upload & Controls ---
st.sidebar.title("Upload Documents")
uploaded_files = st.sidebar.file_uploader("Upload project-related documents", accept_multiple_files=True)

if st.sidebar.button("Generate Graph"):
    st.session_state.graph = nx.erdos_renyi_graph(10, 0.3)  # Placeholder for processing logic

# --- Chatbot Interface ---
st.title("Graph-Based Chatbot")
st.subheader("Ask the chatbot to modify your graph")

# Chatbot interaction
user_input = st.text_input("You:", "")
if st.button("Send"):
    if user_input:
        response = f"Processing: {user_input}"  # Placeholder chatbot response
        st.session_state.chat_history.append(f"You: {user_input}")
        st.session_state.chat_history.append(f"Bot: {response}")

st.write("### Chat History")
st.write("\n".join(st.session_state.chat_history))

# --- Display Graph using Pyvis ---
st.subheader("Graph Visualization")

# Save Pyvis network to an HTML file
def draw_graph(graph):
    net = Network(height="500px", width="100%", notebook=False)
    net.from_nx(graph)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
        net.save_graph(tmp_file.name)
        return tmp_file.name

if st.session_state.graph.nodes:
    graph_html = draw_graph(st.session_state.graph)
    with open(graph_html, "r", encoding="utf-8") as file:
        st.components.v1.html(file.read(), height=500)
else:
    st.write("No graph to display. Upload files and generate a graph.")

# Cleanup temp file
if "graph_html" in locals():
    os.unlink(graph_html)
