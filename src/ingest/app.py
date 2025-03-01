import streamlit as st
import networkx as nx
from pyvis.network import Network
import fitz  # PyMuPDF
import tempfile
import os

# --- Initialize session state ---
if "graph" not in st.session_state:
    st.session_state.graph = nx.Graph()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "documents_text" not in st.session_state:
    st.session_state.documents_text = []

# --- Page Layout ---
st.set_page_config(layout="wide")  # Set to full-screen mode

# Sidebar for Upload
st.sidebar.title("Upload Documents")
uploaded_files = st.sidebar.file_uploader("Upload project-related documents (PDF only)", 
                                          accept_multiple_files=True, type=["pdf"])

# --- Function to extract text from PDFs ---
def extract_text_from_pdfs(files):
    extracted_texts = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(file.read())
            temp_pdf_path = temp_pdf.name

        doc = fitz.open(temp_pdf_path)
        text = "\\n".join([page.get_text("text") for page in doc])
        extracted_texts.append(text)

        os.remove(temp_pdf_path)  # Cleanup temporary file
    return extracted_texts

# Process uploaded PDFs when "Generate Graph" is clicked
if st.sidebar.button("Generate Graph"):
    if uploaded_files:
        st.session_state.documents_text = extract_text_from_pdfs(uploaded_files)
        st.session_state.graph = nx.erdos_renyi_graph(10, 0.3)  # Placeholder for processing logic
        st.sidebar.success("Graph generated successfully!")
    else:
        st.sidebar.warning("Please upload at least one PDF file.")

# Create two columns: Left (1/3) for chatbot, Right (2/3) for graph
left_col, right_col = st.columns([1, 2])

# --- Left Panel (Chatbot UI) ---
with left_col:
    st.title("Interactive GraphRAG ETL")
    st.write("Upload your project-related documents for processing and modify them here.")

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

# Debug: Show extracted text from PDFs
if st.sidebar.checkbox("Show Extracted Text"):
    for idx, text in enumerate(st.session_state.documents_text):
        st.sidebar.write(f"### Document {idx + 1} Content:")
        st.sidebar.text_area("", text, height=200, disabled=True)
