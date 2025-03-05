import streamlit as st
# --- Page Layout ---
st.set_page_config(layout="wide")  # Set to full-screen mode

import networkx as nx
import fitz  # PyMuPDF
import tempfile
import os
import database as db
import graph

from component import *
from st_link_analysis import st_link_analysis

VIEW_BY_GRAPH_CHOICE = {
    "Employee Interaction": ["Default (by hierarchy)", "Grid", "✨ Magic View"],
    "Task Dependence": ["Default (by layers)", "Grid", "✨ Magic View"]
}



# --- Initialize session state ---
if "graph" not in st.session_state:
    st.session_state.graph = nx.Graph()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "documents_text" not in st.session_state:
    st.session_state.documents_text = []

if "emp_info_dict" not in st.session_state:
    with st.spinner("Retrieving employee information..."):
        st.session_state.emp_info_dict = db.get_all_employees()

if "task_info_dict" not in st.session_state:
    with st.spinner("Retrieving tasks information..."):
        st.session_state.task_info_dict = db.get_all_tasks()

if "emp_interact_graph" not in st.session_state:
    with st.spinner("Retrieving employee interaction graph..."):
        st.session_state.emp_interact_graph = db.get_employee_interact_graph()

if "task_depend_graph" not in st.session_state:
    with st.spinner("Retrieving task dependence graph..."):
        st.session_state.task_depend_graph = db.get_task_dependence_graph()

if "main_graph_choice" not in st.session_state:
    st.session_state.main_graph_choice = "Task Dependence"

if "main_graph_view" not in st.session_state:
    st.session_state.main_graph_view = VIEW_BY_GRAPH_CHOICE[st.session_state.main_graph_choice][0]

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

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
#     st.warning("Please enter your OpenAI API key for GraphRAG Magic Ask!", icon="⚠")
#     is_ready = False

# if not uploaded_files:
#     st.warning("Upload your project-related documents here for processing into graph database.", icon="📄")
#     is_ready = False

if not is_ready:
    st.stop()

def render_employee_interaction_graph():
    emp_interact_graph = st.session_state.emp_interact_graph
    elements, node_styles, edge_styles = db.retrieve_employee_interaction_graph(
        emp_interact_graph,
        st.session_state.emp_info_dict 
    )

    # Render the component
    st.markdown("### Employee Interaction Network")

    with st.spinner("Calculating employee view..."):
        # Retrieve graph choices
        graph_view = st.session_state.main_graph_view
        graph_choice = st.session_state.main_graph_choice
        graph_view_by_choice = VIEW_BY_GRAPH_CHOICE[graph_choice]
        
        if graph_view == graph_view_by_choice[-1]:
            st.warning("Magic View not implemented yet")
            graph_col, magic_col = st.columns([3, 1])
            with graph_col:
                layout_options = "cose"
                st_link_analysis(elements, layout_options, node_styles, edge_styles)
            with magic_col:
                chatbot = ChatInstance("magic_view/emp_interact_graph", "This is about a modifying how you visualize a node-edges graph. Offer what you can do to visualize this graph")
                chatbot.render()
        
        # Switch graph_view then render accordingly
        elif graph_view == graph_view_by_choice[0]:
            layout_options = graph.get_layout_for_seniority_layers(emp_interact_graph)
            st_link_analysis(elements, layout_options, node_styles, edge_styles)
        elif graph_view == graph_view_by_choice[1]:
            layout_options = "grid"
            st_link_analysis(elements, layout_options, node_styles, edge_styles)

    accordion_graph_chatbot(emp_interact_graph, "magic_ask/emp_interact_graph")

def render_task_dependence_graph():
    
    task_depend_graph = st.session_state.task_depend_graph
    elements, node_styles, edge_styles = db.retrieve_task_dependence_graph(
        task_depend_graph,
        st.session_state.task_info_dict
    )
        
    # Render the component
    st.markdown("### Task Dependence Network")
    with st.spinner("Calculating task view..."):
        # Retrieve graph choices
        graph_view = st.session_state.main_graph_view
        graph_choice = st.session_state.main_graph_choice
        graph_view_by_choice = VIEW_BY_GRAPH_CHOICE[graph_choice]
        
        # Switch graph_view then render accordingly
        if graph_view == graph_view_by_choice[0]:
            layout_options = graph.topo_sort_layered_layout(st.session_state.task_depend_graph)
        elif graph_view == graph_view_by_choice[1]:
            layout_options = "grid"
        elif graph_view == graph_view_by_choice[-1]:
            # TODO: Implement magic view here
            st.warning("Magic View not implemented yet")
            layout_options = "cose"

        # TODO: Might be a good place to do graphrag here
        st_link_analysis(elements, layout_options, node_styles, edge_styles)
    
    accordion_graph_chatbot(task_depend_graph, "magic_ask/task_depend_graph")
graph_choose_col, graph_view_col = st.columns(2)

with graph_choose_col:
    st.session_state.main_graph_choice = st.selectbox("Choose a graph to view", ["Employee Interaction", "Task Dependence"])

with graph_view_col:
    view_choices = VIEW_BY_GRAPH_CHOICE[st.session_state.main_graph_choice]
    st.session_state.main_graph_view = st.selectbox("Choose how you want to view", view_choices)

if st.session_state.main_graph_choice == "Employee Interaction":
    with st.spinner("Retrieving your employees..."):
        render_employee_interaction_graph()
elif st.session_state.main_graph_choice == "Task Dependence":
    with st.spinner("Retrieving your tasks..."):
        render_task_dependence_graph()


# Project Overview Section
st.markdown("### Overview")


# Create a three-column layout
col1, col2, col3 = st.columns(3)

emp_info_dict = st.session_state.emp_info_dict
task_info_dict = st.session_state.task_info_dict

# First column: Summary tile + Information
with col1:
    st.selectbox("employee_stat", ["Current Employees", "Active Employees"], label_visibility="collapsed")
    summary_tile("Current Employees", len(emp_info_dict), "Total number of employees in this project.", "#FF7F3E")

# Second column: Summary tile + Information
with col2:
    st.selectbox("task_stat", ["Remaining Tasks", "Active Tasks", "Total Story Points", "Remaining Story Points"], label_visibility="collapsed")
    summary_tile("Remaining Tasks", len(task_info_dict), "Remaining number of tasks.", "#4CAF50")

# Third column: Summary tile + Information
with col3:
    st.selectbox("project_stat", ["Project Deadline", "Project Monetary Value"], label_visibility="collapsed")
    summary_tile("Project Deadline", "03/06/2025", "Date where the project has to deliver.", "#2196F3")

st.markdown("---")

emp_col, task_col = st.columns(2)

with emp_col:

    st.markdown(f"### Active Employees ({len(emp_info_dict)})")

    # Create a scrollable container
    container = st.container(height=800)
    with container:
        # Create a div with a scrollable class
        for empID in emp_info_dict:
            employee_tile(emp_info_dict[empID])

with task_col:
    st.markdown(f"### Active Tasks({len(emp_info_dict)})")

    # Create a scrollable container
    container = st.container(height=800)
    with container:
        # Create a div with a scrollable class
        for taskID in task_info_dict:
            task_tile(task_info_dict[taskID])