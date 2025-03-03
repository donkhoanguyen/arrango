import streamlit as st
import networkx as nx
from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
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

# Sidebar for Upload and API Key
os.environ["OPENAI_API_KEY"] = st.sidebar.text_input("OpenAI API Key", type="password")

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


# Methods for Chatbot UI
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown("<h1 style='text-align: center;'>Project Overview Dashboard</h1>", unsafe_allow_html=True)

is_ready = True

# if not os.environ["OPENAI_API_KEY"] .startswith("sk-"):
#     st.warning("Please enter your OpenAI API key for interactive GraphRAG modification!", icon="⚠")
#     is_ready = False

# if not uploaded_files:
#     st.warning("Upload your project-related documents here for processing into graph database.", icon="📄")
#     is_ready = False

if not is_ready:
    st.stop()

def employee_interaction_graph():
    # Sample Data
    elements = {
        "nodes": [
            {"data": {"id": 1, "label": "PERSON", "name": "Streamlit"}},
            {"data": {"id": 2, "label": "PERSON", "name": "Hello"}},
            {"data": {"id": 3, "label": "PERSON", "name": "World"}},
            {"data": {"id": 4, "label": "POST", "content": "x"}},
            {"data": {"id": 5, "label": "POST", "content": "y"}},
        ],
        "edges": [
            {"data": {"id": 6, "label": "FOLLOWS", "source": 1, "target": 2}},
            {"data": {"id": 7, "label": "FOLLOWS", "source": 2, "target": 3}},
            {"data": {"id": 8, "label": "POSTED", "source": 3, "target": 4}},
            {"data": {"id": 9, "label": "POSTED", "source": 1, "target": 5}},
            {"data": {"id": 10, "label": "QUOTES", "source": 5, "target": 4}},
        ],
    }

    # Style node & edge groups
    node_styles = [
        NodeStyle("PERSON", "#FF7F3E", "name", "person"),
        NodeStyle("POST", "#2A629A", "content", "description"),
    ]

    edge_styles = [
        EdgeStyle("FOLLOWS", caption='label', directed=True),
        EdgeStyle("POSTED", caption='label', directed=True),
        EdgeStyle("QUOTES", caption='label', directed=True),
    ]

    # Render the component
    st.markdown("### Employee Interaction Network")
    st_link_analysis(elements, "cose", node_styles, edge_styles)

selected_graph_view = os.environ["SELECTED_GRAPH_VIEW"] if "SELECTED_GRAPH_VIEW" in os.environ else "Employee Interaction"

if selected_graph_view == "Employee Interaction":
    employee_interaction_graph()
elif selected_graph_view == "Project Overview":
    st.write("Insert graph here")


os.environ["SELECTED_GRAPH_VIEW"]= st.selectbox("Choose a Graph View", ["Employee Interaction", "Project Overview"])
