import streamlit as st

from agent.graph_visualization import GraphVisualizationRequest
# --- Page Layout ---
st.set_page_config(layout="wide")  # Set to full-screen mode

import networkx as nx
import fitz  # PyMuPDF
import tempfile
import os
import database as db
import graph as graph_utils
from database import db as adb
from agent.graph_cache import GraphWrapper

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
    "StreamSync Pipeline": "bi_tasks",
    "DataForge ETL": "de_tasks",
    "AetherFlow Orchestrator": "ds_tasks",
    "NeoGraph Linker": "dg_tasks",
    "Company Overview": "*"
}

GRAPH_TYPE = ["Employee Interaction", "Task Dependence", "Task Assignment"]

VIEW_BY_GRAPH_CHOICE = {
    "Employee Interaction": ["Default (by hierarchy)", "Grid", "✨ Magic View"],
    "Task Dependence": ["Default (by layers)", "Grid", "✨ Magic View"],
    "Task Assignment": ["Default", "✨ Magic View"],
}

PROJECT_LIST = ["StreamSync Pipeline", "DataForge ETL", "AetherFlow Orchestrator", "NeoGraph Linker", "Company Overview"]

GRAPH_LIST = ["Employee Interaction", "Task Dependence", "Task Assignment"]

# --- Initialize session state ---
# Load project choice
if "project_choice" not in st.session_state:
    st.session_state.project_choice = PROJECT_LIST[0]
project_choice = st.session_state.project_choice

# Load graph cache for Agents
if "GRAPH_CACHE" not in st.session_state:
    GRAPH_CACHE = {}

    # Preload name, schema, and description for task dependence graph
    for project in PROJECT_TO_TASKS_MAP:
        tasks_col = PROJECT_TO_TASKS_MAP[project]

        if tasks_col == "*":
            continue
        tasks_dependence_graph_name = f"{tasks_col}_dependence_graph"
        schema = {
            "nodes": ["task"],
            "edges": ["depends on"],
            "tasks_col": tasks_col,
        }
        description = f"This is the graph of task dependence for the project {project}"
        
        GRAPH_CACHE[tasks_dependence_graph_name] = GraphWrapper(adb, None, tasks_dependence_graph_name,schema, description)

    # Preload employee interaction graph
    for project in PROJECT_TO_TEAM_MAP:
        team = PROJECT_TO_TEAM_MAP[project]
        schema = {
            "nodes": ["employee"],
            "edges": ["interacts with"],
        }
        description = "The graph of extended interaction and help between employees of the company"
        if team == "*":
            GRAPH_CACHE["employee_interaction"] = GraphWrapper(adb, None, "employee_interaction", schema, description)
        else:
            GRAPH_CACHE[f"{team}_employee_interaction"] = GraphWrapper(adb, None, f"{team}_employee_interaction", schema, description)
    
    # Preload task assignment graph
    schema = {
        "nodes": ["task", "employee"],
        "edges": ["assigned to", "advised"]
    }
    description = "The graph of task assignment between tasks and employees"
    GRAPH_CACHE["bi_team_task_assignment"] = GraphWrapper(adb, None, "bi_team_task_assignment", schema, description)

    st.session_state.GRAPH_CACHE = GRAPH_CACHE

GRAPH_CACHE: dict[str, GraphWrapper] = st.session_state.GRAPH_CACHE

# Load entire project data
if "all_project_data" not in st.session_state:
    st.session_state.all_project_data = {}

# Preload all graphs related to this project
if project_choice not in st.session_state.all_project_data:
    team = PROJECT_TO_TEAM_MAP[project_choice]
    team_tasks = PROJECT_TO_TASKS_MAP[project_choice]

    # Retrieve collections
    emp_col = None
    with st.spinner(f"Retrieving {project_choice}'s List of Employees"):
        emp_col = db.get_all_employees_by_team(team)

    tasks_col = None
    with st.spinner(f"Retrieving {project_choice}'s List of Tasks"):
        tasks_col = db.get_all_tasks(team_tasks)

    # Retrieve graphs
    task_assignment = None
    if team != "*":
        with st.spinner(f"Retrieving {project_choice}'s Task Assignment"):
            task_assignment = db.get_task_assignment(team_tasks)
            GRAPH_CACHE["bi_team_task_assignment"].graph = task_assignment
        
    employee_interaction = None
    with st.spinner(f"Retrieving {project_choice}'s Employee Interaction"):
        employee_interaction = db.get_employee_interact_graph(team)
        if team == "*":
            GRAPH_CACHE[f"employee_interaction"].graph = employee_interaction
        else:
            GRAPH_CACHE[f"{team}_employee_interaction"].graph = employee_interaction

    task_dependence = None
    if team != "*":
        with st.spinner(f"Retrieving {project_choice}'s Task Depenence"):
            task_dependence = db.get_task_dependence_graph(team_tasks)
            GRAPH_CACHE[f"{team_tasks}_dependence_graph"].graph = task_dependence
    
    # Set data
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
        "collection/Tasks": tasks_col,
        "collection/Employees": emp_col,
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

# st.sidebar.title("Upload Documents")
# uploaded_files = st.sidebar.file_uploader("Upload project-related documents (PDF only)",
#                                           accept_multiple_files=True, type=["pdf"])

# # --- Function to extract text from PDFs ---
# def extract_text_from_pdfs(files):
#     extracted_texts = []
#     for file in files:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
#             temp_pdf.write(file.read())
#             temp_pdf_path = temp_pdf.name

#         doc = fitz.open(temp_pdf_path)
#         text = "\\n".join([page.get_text("text") for page in doc])
#         extracted_texts.append(text)

#         os.remove(temp_pdf_path)  # Cleanup temporary file
#     return extracted_texts

# # Process uploaded PDFs when "Generate Graph" is clicked
# if st.sidebar.button("Generate Graph"):
#     print("Generated!")

if project_choice != "Company Overview":
    st.markdown(f"<h1 style='text-align: center;'>Project: {project_choice}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>Project Insights Dashboard</h1>", unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align: center;'>{project_choice}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center;'>Company Insights Dashboard</h1>", unsafe_allow_html=True)

project_choice = st.selectbox("Current project:", PROJECT_LIST)

if project_choice != st.session_state.project_choice:
    st.session_state.project_choice = project_choice
    st.rerun()

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
    # Do not support tasks-related graph for Company Overview
    st.markdown(f"### {graph_choice} Network")
    if project_choice == list(PROJECT_TO_TEAM_MAP.keys())[-1] and graph_choice != GRAPH_LIST[0]:
        st.warning(f"{graph_choice} visualization not supported for {project_choice} yet", icon="⚠")
        return
    # Prepare graph and its render function
    graph_data = cur_project_data[graph_choice]
    graph = graph_data["graph"]
    render_function = graph_data["render"]

    # Initialize specific request_visualize function
    viz_request_id = f"{project_choice}/magic_view/{graph_choice}/viz_request"
    def request_visualize(visualize_request: GraphVisualizationRequest):
        # Just to be sure
        if visualize_request == None:
            raise ValueError("Can't visualize a null visualization request")
        st.session_state[viz_request_id]= visualize_request
        st.rerun()

    # Start rendering
    with st.spinner(f"Rendering {graph_choice} graph..."):

        graph_view_by_choice = VIEW_BY_GRAPH_CHOICE[graph_choice]

        # If is Magic View, then show visualization request if any
        # Otherwise, default cose layouts
        # Also there is chatbot on the side
        if graph_view == graph_view_by_choice[-1]:
            graph_col, magic_col = st.columns([3, 1])
            with graph_col:
                if viz_request_id in st.session_state:
                    st.markdown("#### ✨ Custom Magic View layout")
                    st.session_state[viz_request_id].render()
                else:
                    st.markdown("#### Default layout")
                    elements, node_styles, edge_styles = render_function(graph)
                    layout_options = "grid"
                    st_link_analysis(elements, layout_options, node_styles, edge_styles)
            with magic_col:
                magic_view_chatbot(GRAPH_CACHE[graph.name], f"{project_choice}/magic_view/{graph_choice}", request_visualize)

            return graph.name

        # Prepare the elements and styles to render
        elements, node_styles, edge_styles = render_function(graph)

        # Determine what layout will the graph render based on different graph view choice and graph data
        layout_options = "cose"
        # Employee Interaction
        if graph_choice == GRAPH_LIST[0]:
            if graph_view == graph_view_by_choice[0]:
                if project_choice != "Company Overview":
                    layout_options = graph_utils.get_layout_for_seniority_layers(f"{PROJECT_TO_TEAM_MAP[project_choice]}_employee_interaction")
                else:
                    layout_options = graph_utils.get_layout_for_seniority_layers("employee_interaction")
                    print(layout_options)
            elif graph_view == graph_view_by_choice[1]:
                layout_options = "grid"

        # Task Dependence
        elif graph_choice == GRAPH_LIST[1]:
            if graph_view == graph_view_by_choice[0]:
                layout_options = "grid"
                # layout_options = graph_utils.topo_sort_layered_layout(graph.name)
            elif graph_view == graph_view_by_choice[1]:
                layout_options = "grid"
        
        # Task Assignment
        elif graph_choice == GRAPH_LIST[2]:
            layout_options = "cose"
        
        # Finally, render it out to frontend
        st_link_analysis(elements, layout_options, node_styles, edge_styles)
        return graph.name


graph_choose_col, graph_view_col = st.columns(2)

with graph_choose_col:
    main_graph_choice = st.selectbox("Choose a graph to view", GRAPH_TYPE, index=GRAPH_TYPE.index(main_graph_choice))
    st.session_state.main_graph_choice = main_graph_choice

with graph_view_col:
    view_choices = VIEW_BY_GRAPH_CHOICE[main_graph_choice]
    main_graph_view = st.selectbox("Choose how you want to view", view_choices)
    st.session_state.main_graph_view = main_graph_view

current_graph_name = render_graph(project_choice, main_graph_choice, main_graph_view)

if current_graph_name != None:
    accordion_graph_chatbot(GRAPH_CACHE[current_graph_name], f"{project_choice}/magic_ask/{main_graph_choice}")

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
    st.selectbox("task_stat", ["Total Tasks", "Active Tasks", "Total Story Points", "Remaining Story Points"], label_visibility="collapsed")
    summary_tile("Total Tasks", len(task_info_dict), "Total number of tasks.", "#4CAF50")

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
    st.markdown(f"### Active Tasks({len(task_info_dict)})")

    # Create a scrollable container
    container = st.container(height=800)
    with container:
        # Create a div with a scrollable class
        for taskID in task_info_dict:
            task_tile(task_info_dict[taskID])