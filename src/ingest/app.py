import streamlit as st
# --- Page Layout ---
st.set_page_config(layout="wide")  # Set to full-screen mode

import networkx as nx
import fitz  # PyMuPDF
import tempfile
import os
import database as db
import graph as graph_utils

from component import *
from st_link_analysis import st_link_analysis

PROJECT_TO_TEAM_MAP = {
    "StreamSync Pipeline": "Business Intelligence",
    "DataForge ETL": "Data Engineering",
    "AetherFlow Orchestrator": "Data Science",
    "NeoGraph Linker": "Data Governance",
    "Company Overview": "*"
}

PROJECT_TO_TASKS_MAP = {
    "StreamSync Pipeline": "bi_team_task",
    "DataForge ETL": "de_team_task",
    "AetherFlow Orchestrator": "ds_team_task",
    "NeoGraph Linker": "dg_team_task",
    "Company Overview": "*"
}

PROJECT_TO_TASKS_MAP = {
    "StreamSync Pipeline": "bi_team_task",
    "DataForge ETL": "de_team_task",
    "AetherFlow Orchestrator": "ds_team_task",
    "NeoGraph Linker": "dg_team_task",
    "Company Overview": "*"
}

VIEW_BY_GRAPH_CHOICE = {
    "Employee Interaction": ["Default (by hierarchy)", "Grid", "✨ Magic View"],
    "Task Dependence": ["Default (by layers)", "Grid", "✨ Magic View"],
    "Task Assignment": ["Default", "✨ Magic View"],
}

PROJECT_LIST = ["StreamSync Pipeline", "DataForge ETL", "AetherFlow Orchestrator", "NeoGraph Linker", "Company Overview"]

GRAPH_LIST = ["Employee Interaction", "Task Dependence", "Task Assignment"]

# --- Initialize session state ---
if "project_choice" not in st.session_state:
    st.session_state.project_choice = PROJECT_LIST[0]

project_choice = st.session_state.project_choice

if "all_project_data" not in st.session_state:
    st.session_state.all_project_data = {}

if st.session_state.project_choice not in st.session_state.all_project_data:
    print("reloading again)")
    with st.spinner(f"Retrieving {project_choice}'s Task Assignment"):
        task_assignment = db.get_bi_team_task_assignment()
    with st.spinner(f"Retrieving {project_choice}'s Employee Interaction"):
        employee_interaction = db.get_employee_interact_graph()
    with st.spinner(f"Retriving {project_choice}'s Task Depenence"):
        task_dependence = db.get_task_dependence_graph()

    st.session_state.all_project_data[project_choice] = {
        "Task Assignment": {
            "graph": task_assignment,
            "render": db.retrieve_bi_team_task_assignment_graph
        },
        "Employee Interaction": {
            "graph": employee_interaction,
            "render": db.retrieve_employee_interaction_graph
        },
        "Task Dependence": {
            "graph": task_dependence,
            "render": db.retrieve_task_dependence_graph,
        },
        "collection/Tasks": db.get_all_tasks(),
        "collection/Employees": db.get_all_employees_by_team(PROJECT_TO_TEAM_MAP[project_choice])
    }

# Retrieving data
cur_project_data = st.session_state.all_project_data[project_choice]
emp_info_dict = cur_project_data["collection/Employees"]
task_info_dict = cur_project_data["collection/Tasks"]

if "documents_text" not in st.session_state:
    st.session_state.documents_text = []

if "main_graph_choice" not in st.session_state:
    st.session_state.main_graph_choice = "Task Dependence"

main_graph_choice = st.session_state.main_graph_choice

if "main_graph_view" not in st.session_state:
    st.session_state.main_graph_view = VIEW_BY_GRAPH_CHOICE[st.session_state.main_graph_choice][0]

main_graph_view = st.session_state.main_graph_view

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
    print("Generated!")

st.markdown(f"<h1 style='text-align: center;'>{project_choice}</h1>", unsafe_allow_html=True)
st.markdown(f"<h2 style='text-align: center;'>Project Overview Dashboard</h1>", unsafe_allow_html=True)

project_choice = st.selectbox("Current project:", PROJECT_LIST)
st.session_state.project_choice = project_choice

is_ready = True

# if not os.environ["OPENAI_API_KEY"] .startswith("sk-"):
#     st.warning("Please enter your OpenAI API key for GraphRAG Magic Ask!", icon="⚠")
#     is_ready = False

# if not uploaded_files:
#     st.warning("Upload your project-related documents here for processing into graph database.", icon="📄")
#     is_ready = False

if not is_ready:
    st.stop()

def render_graph(project_choice, graph_choice, graph_view):
    # Prepare graph and its render function
    graph_data = cur_project_data[graph_choice]
    graph = graph_data["graph"]
    render_function = graph_data["render"]


    # Start rendering
    st.markdown(f"### {graph_choice} Network")
    with st.spinner(f"Rendering {graph_choice} graph..."):
        # Prepare the elements and styles to render
        elements, node_styles, edge_styles = render_function(graph)

        graph_view_by_choice = VIEW_BY_GRAPH_CHOICE[graph_choice]
        # If is Magic View, then show default cose layouts and chatbot on the side
        if graph_view == graph_view_by_choice[-1]:
            st.warning("Magic View not implemented yet")
            graph_col, magic_col = st.columns([3, 1])
            with graph_col:
                layout_options = "cose"
                st_link_analysis(elements, layout_options, node_styles, edge_styles)
            with magic_col:
                chatbot = ChatInstance(f"{project_choice}/magic_view/{graph_choice}", "This is about a modifying how you visualize a node-edges graph. Offer what you can do to visualize this graph")
                chatbot.render()
            return

        # Determine what layout will the graph render based on different graph view choice and graph data
        layout_options = "cose"
        # Employee Interaction
        if graph_choice == GRAPH_LIST[0]:
            if graph_view == graph_view_by_choice[0]:
                layout_options = graph_utils.get_layout_for_seniority_layers(graph)
            elif graph_view == graph_view_by_choice[1]:
                layout_options = "grid"

        # Task Dependence
        elif graph_choice == GRAPH_LIST[1]:
            if graph_view == graph_view_by_choice[0]:
                layout_options = graph_utils.topo_sort_layered_layout(graph)
            elif graph_view == graph_view_by_choice[1]:
                layout_options = "grid"
        
        # Task Assignment
        elif graph_choice == GRAPH_LIST[2]:
            layout_options = "cose"
            pass
        
        # Finally, render it out to frontend
        st_link_analysis(elements, layout_options, node_styles, edge_styles)

        accordion_graph_chatbot(graph, f"{project_choice}/magic_ask/{graph_choice}")


graph_choose_col, graph_view_col = st.columns(2)

with graph_choose_col:
    main_graph_choice = st.selectbox("Choose a graph to view", ["Employee Interaction", "Task Dependence", "Task Assignment"])
    st.session_state.main_graph_choice = main_graph_choice

with graph_view_col:
    view_choices = VIEW_BY_GRAPH_CHOICE[main_graph_choice]
    main_graph_view = st.selectbox("Choose how you want to view", view_choices)
    st.session_state.main_graph_view = main_graph_view

render_graph(project_choice, main_graph_choice, main_graph_view)

# Project Overview Section
st.markdown("### Overview")

# Create a three-column layout
col1, col2, col3 = st.columns(3)

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