import streamlit as st
import networkx as nx
from pyvis.network import Network
import fitz  # PyMuPDF
import tempfile
import os

from langchain_openai.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

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

st.session_state["openai_model"] = "gpt-4o"

# Initialize ChatOpenAI with a default API key (or None)
llm = ChatOpenAI(
    model=st.session_state["openai_model"],
    streaming=True,
    temperature=0,
)

# Initialize ConversationBufferMemory
memory = ConversationBufferMemory(return_messages=True)

# Initialize ConversationChain
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=False
)

# --- Left Panel (Chatbot UI) ---
st.title("Interactive GraphRAG ETL")
st.write("Upload your project-related documents for processing and modify them here.")

if not os.environ["OPENAI_API_KEY"] .startswith("sk-"):
    st.warning("Please enter your OpenAI API key!", icon="⚠")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your query here"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = conversation.predict(input=prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Update the conversation memory
    conversation.memory.chat_memory.messages = [
        SystemMessage(content="You are a helpful assistant."),
        *[HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
            for m in st.session_state.messages]
    ]

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
