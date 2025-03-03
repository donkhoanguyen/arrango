import json
import streamlit as st
import networkx as nx
import fitz  # PyMuPDF
import tempfile
import os
import database as db

from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle

# --- Page Layout ---
st.set_page_config(layout="wide")  # Set to full-screen mode


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

# if "emp_interac" not in st.session_state:
#     st.session_state.emp_interact_graph = db.get_employee_interact_graph()

if "main_graph_view" not in st.session_state:
    st.session_state.main_graph_view = "Employee Interaction"

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
    elements, node_styles, edge_styles = db.retrieve_employee_interaction_graph(
        st.session_state.emp_interact_graph,
        st.session_state.emp_info_dict 
    )
    # Render the component
    st.markdown("### Employee Interaction Network")

    # TODO: Might be a good place to do graphrag here
    st_link_analysis(elements, "grid", node_styles, edge_styles)

if st.session_state.main_graph_view == "Employee Interaction":
    with st.spinner("Retrieving your graph..."):
        employee_interaction_graph()
elif st.session_state.main_graph_view == "Project Overview":
    st.write("Insert graph here")

st.session_state.main_graph_view = st.selectbox("Choose a graph view", ["Employee Interaction", "Project Overview"])

# Project Overview Section
st.markdown("### Overview")


# Create a three-column layout
col1, col2, col3 = st.columns(3)

import streamlit as st


def summary_tile(title, number, description, color):
    st.markdown(
        f"""
        <div style="background-color: {color}; padding: 20px; border-radius: 10px; height: 225px; text-align: center;">
            <h4 style="margin: 0; color: white;">{title}</h4>
            <h1 style="margin: 0; color: white;">{number}</h1>
            <p style="color: white;">{description}</p>
        </div>
        """, unsafe_allow_html=True) 

# Create a three-column layout
col1, col2, col3 = st.columns(3)

emp_info_dict = st.session_state.emp_info_dict
task_info_dict = st.session_state.task_info_dict

# Function to create a styled employee tile
def employee_tile(employee):
    # Tile styling (white background with a slight shadow and rounded corners)
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
            <p style="margin: 0; font-size: 28px; font-weight: bold; color: #333;">{employee['FirstName']} {employee['LastName']}</p>
            <p style="margin: 5px 0; font-size: 16px; color: #777;"><strong>Employee ID:</strong> {employee['EmpID']}</p>
            <p style="margin: 5px 0; font-size: 20px; font-weight: bold; color: #333;">
                {employee['Department']} | {employee['Role']}
            </p>
        </div>
        """, unsafe_allow_html=True)

def get_status_color(status):
    """Returns a color for the status tag."""
    status_colors = {
        "Not Started": "#d3d3d3",  # Gray
        "In Progress": "#f39c12",  # Orange
        "Completed": "#2ecc71",    # Green
        "Blocked": "#e74c3c",      # Red
    }
    return status_colors.get(status, "#bdc3c7") 

def task_tile(task):
    """Displays a task tile with key details."""
    status_color = get_status_color(task.get("Status", "Not Started"))

    st.markdown(
        f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        ">
            <h4 style="margin: 0;">Task: {task.get("TaskID", "Unknown")}</h4>
            <p style="color: #555;">{task.get("Description", "No description available.")}</p>

            <div style="display: flex; align-items: center;">
                <div style="background-color: {status_color};
                            color: white;
                            padding: 5px 10px;
                            border-radius: 5px;
                            font-size: 12px;
                            font-weight: bold;
                            display: inline-block;
                            margin-right: 10px;">
                    {task.get("Status", "Not Started")}
                </div>
            </div>

            <p><b>Assigned Employees:</b> {', '.join(task.get("AssignedEmployees", [])) or 'None'}</p>
            <p><b>Advisors:</b> {', '.join(task.get("Advisors", [])) or 'None'}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# @st.dialog("Employee Information")
# def vote(emp_info):
#     st.markdown(f"### {}")
#     st.write(f"Why is {item} your favorite?")
#     reason = st.text_input("Because...")
#     if st.button("Submit"):
#         st.session_state.vote = {"item": item, "reason": reason}
#         st.rerun()

# First column: Summary tile + Information
with col1:
    st.selectbox("employee_stat", ["Current Employees", "Active Employees"], label_visibility="collapsed")
    summary_tile("Current Employees", len(emp_info_dict), "Total number of employees in this project.", "#FF7F3E")

    st.markdown("---")
    st.markdown(f"### Active Employees ({len(emp_info_dict)})")

    # Create a scrollable container
    container = st.container(height=400)
    with container:
        # Add the scrollable box styling using custom HTML/CSS
        st.markdown("""
        <style>
            .scrollable-box {
                max-height: 400px;
                overflow-y: auto;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid #e0e0e0;
            }
        </style>
        """, unsafe_allow_html=True)

        # Create a div with a scrollable class
        for empID in emp_info_dict:
            employee_tile(emp_info_dict[empID])


# Second column: Summary tile + Information
with col2:
    st.selectbox("task_stat", ["Remaining Tasks", "Active Tasks", "Total Story Points", "Remaining Story Points"], label_visibility="collapsed")
    summary_tile("Remaining Tasks", "20", "Remaining number of tasks.", "#4CAF50")

    st.markdown("---")
    st.markdown(f"### Active Tasks({len(emp_info_dict)})")

    # Create a scrollable container
    container = st.container(height=400)
    with container:
        # Add the scrollable box styling using custom HTML/CSS
        st.markdown("""
        <style>
            .scrollable-box {
                max-height: 400px;
                overflow-y: auto;
                padding: 10px;
                border-radius: 10px;
                border: 2px solid #e0e0e0;
            }
        </style>
        """, unsafe_allow_html=True)

        # Create a div with a scrollable class
        for empID in emp_info_dict:
            employee_tile(emp_info_dict[empID])

# Third column: Summary tile + Information
with col3:
    st.selectbox("project_stat", ["Project Deadline", "Project Monetary Value"], label_visibility="collapsed")
    summary_tile("Project Deadline", "03/06/2025", "Date where the project has to deliver.", "#2196F3")

