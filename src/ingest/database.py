import nx_arangodb as nxadb
import streamlit as st

from st_link_analysis import NodeStyle, EdgeStyle
from arango import ArangoClient

client = ArangoClient(hosts=st.secrets["DATABASE_HOST"])
db = client.db(
    st.secrets["DATABASE_NAME"],
    username=st.secrets["DATABASE_USERNAME"],
    password=st.secrets["DATABASE_PASSWORD"]
)

TASKS_TO_PROJECT_MAP = {
    "bi_tasks": "StreamSync Pipeline",
    "de_tasks": "DataForge ETL",
    "ds_tasks": "AetherFlow Orchestrator",
    "dg_tasks": "NeoGraph Linker",
    "*": "Company Overview"
}

# Function to get all employee information as a dictionary with EmpID as the key
def get_all_employees_by_team(team_name):
    # Access the employee vertex collection
    # employee_collection = db.collection('employee')  # Ensure this is the correct collection name
    print("searching for team", team_name)
    if team_name != "*":
        employee_query = f"""
        FOR e IN employee
            FILTER e.Team == '{team_name}'
            RETURN e
        """
    else:
        employee_query = f"""
        FOR e IN employee
            RETURN e
        """
    # Fetch all employees from the collection
    employees = db.aql.execute(employee_query)  # Fetches all documents in the collection
    
    # Create a dictionary to store employee info with EmpID as the key
    employee_dict = {}
    
    for employee in employees:
        # Build employee info dictionary
        employee_info = {
            "EmpID": employee["_key"],
            "FirstName": employee.get("FirstName"),
            "LastName": employee.get("LastName"),
            "Email": employee.get("Email"),
            "Role": employee.get("Role"),
            "Department": employee.get("Department"),
            "Team": employee.get("Team"),
            "Seniority": employee.get("Seniority"),
            "HireDate": employee.get("HireDate"),
            "Salary": employee.get("Salary"),
            "ManagerID": employee.get("ManagerID")
        }
        # Use EmpID as the key
        employee_dict[f"employee/{employee['_key']}"] = employee_info
    
    return employee_dict

# Function to get all task information as a dictionary with as TaskID the key
def get_all_tasks(tasks_col):
    if tasks_col == "*":
        collections = db.aql.execute("FOR c IN COLLECTIONS() FILTER c.name LIKE '%_tasks' RETURN c.name")
        # Retrieve and flatten documents into one list
        tasks = [
            {**doc, "_collection": collection}  # Add collection name as metadata if needed
            for collection in collections
            for doc in db.collection(collection).all()
        ]
    else:
        task_collection = db.collection(tasks_col)  # Ensure this is the correct collection name
        tasks = task_collection.all()  # Fetches all documents in the collection
    
    # Create a dictionary to store employee info with EmpID as the key
    task_dict = {}
    
    for task in tasks:
        # Build employee info dictionary
        task_info = {
            "TaskID": task["_key"],
            "Description": task.get("Description"),
            "AssignedEmployees": task.get("AssignedEmployees", "").split(","),
            "Advisors": task.get("Advisors", "").split(","),
            "PrecedingTasks": task.get("PrecedingTasks"), 
            "StoryPoints": task.get("StoryPoints"),
            "StartTime": task.get("StartTime"),
            "EstimatedFinishTime": task.get("EstimatedFinishTime"),
            "Status": task.get("Status"),
            "ActualFinishTime": task.get("ActualFinishTime"),
            "Project": TASKS_TO_PROJECT_MAP[tasks_col if tasks_col != "*" else task["_collection"]]
        }
        task_dict[f"task/{task['_key']}"] = task_info
    
    return task_dict

def get_employee_interact_graph(team):
    full_graph = nxadb.Graph(name="employee_interaction")
    # TODO: temporary  
    return full_graph
    if team == "*":
        return full_graph
    
    filtered_nodes = {n for n, data in full_graph.nodes(data=True) if data["Team"] == team}
    team_graph = full_graph.copy().subgraph(filtered_nodes)
    team_graph.name = f"{team}_employee_interaction"
    return team_graph

def get_task_dependence_graph(tasks_col):
    return nxadb.DiGraph(name=f"{tasks_col}_dependence_graph")

def get_task_assignment(tasks_col):
    return nxadb.MultiDiGraph(name=f"bi_team_task_assignment")
    # return nxadb.MultiDiGraph(name=f"{tasks_col}_task_assignment")


def retrieve_employee_interaction_graph(emp_interact_graph):
    nodes = []
    edges = []
    for employee_node, employee_info in emp_interact_graph.nodes(data=True):
        seniority = employee_info["Seniority"] 

        nodes.append({
            "data": {
                "id": employee_node, 
                "label": seniority,
                "name": f"{employee_info['FirstName']} {employee_info['LastName']}",
                **employee_info
            }
        })
    # Style node & edge groups
    node_styles = [
        NodeStyle("Director", "#FF5722", "name", "person"),           # Coral
        NodeStyle("Vice-Director", "#E91E63", "name", "person"),      # Pink
        NodeStyle("Lead", "#FF7F3E", "name", "person"),           # Orange
        NodeStyle("Senior", "#4CAF50", "name", "person"), # Green
        NodeStyle("Mid-Level", "#2196F3", "name", "person"), # Blue
        NodeStyle("Junior", "#FFC107", "name", "person"), # Amber
        NodeStyle("Employee", "#9C27B0", "name", "person"),       # Purple
    ]
    for emp_from, emp_to in emp_interact_graph.edges:
        if (
            emp_from == "employee/0"
            or emp_to == "employee/0"
        ):
            continue
        edges.append({
            "data": {
                "id": f"{emp_from}->{emp_to}",
                "label": "Interacts",
                "source": emp_from,
                "target": emp_to,
            }
        })
    
    edge_styles = [
        EdgeStyle("Interact", caption='label', directed=True),
    ]
    elements = {
        "nodes": nodes,
        "edges": edges,
    }

    return elements, node_styles, edge_styles

def retrieve_task_dependence_graph(task_interact_graph):
    nodes = []
    edges = []
    
    for task_node, task_info in task_interact_graph.nodes(data=True):
        nodes.append({
            "data": {
                "id": task_node, 
                "label": task_info["Status"],
                "name": task_info["TaskID"],
                **task_info
            }
        })
    # Style node & edge groups
    node_styles = [
        NodeStyle("Planned", "#d3d3d3", "name", "person"),           # Orange
        NodeStyle("In Progress", "#f39c12", "name", "person"), # Green
        NodeStyle("Completed", "#2ecc71", "name", "person"), # Blue
        NodeStyle("Blocked", "#e74c3c", "name", "person"), # Amber
    ]
    for task_from, task_to in task_interact_graph.edges:
        edges.append({
            "data": {
                "id": f"{task_from}->{task_to}",
                "label": "Depends On",
                "source": task_from,
                "target": task_to,
            }
        })
    
    edge_styles = [
        EdgeStyle("Depends On", caption='label', directed=True),
    ]
    elements = {
        "nodes": nodes,
        "edges": edges,
    }

    return elements, node_styles, edge_styles

def retrieve_bi_team_task_assignment_graph(task_graph):
    nodes = []
    edges = []

    # Mapping task statuses to labels and colors
    TASK_STATUS_LABEL_MAP = {
        "Planned": "PlannedTask",
        "In Progress": "InProgressTask",
        "Completed": "CompletedTask",
        "Blocked": "BlockedTask",
    }
    TASK_COLOR_MAP = {
        "PlannedTask": "#d3d3d3",
        "InProgressTask": "#f39c12",
        "CompletedTask": "#2ecc71",
        "BlockedTask": "#e74c3c",
    }
    
    # Employee seniority color mapping
    EMPLOYEE_COLOR_MAP = {
        "Lead": "#FF7F3E",
        "Senior": "#4CAF50",
        "Mid-Level": "#2196F3",
        "Junior": "#FFC107",
    }

    for node, data in task_graph.nodes(data=True):
        if node[:4] == "task":
            if data["Status"] == "Planned":
                continue
            task_label = TASK_STATUS_LABEL_MAP.get(data["Status"], "PlannedTask")
            nodes.append({
                "data": {
                    "id": node, 
                    "label": task_label,
                    "name": data["TaskID"],
                    **data
                }
            })
        else:
            # Only render for BI team
            if data["Team"] != "Business Intelligence":
                continue
            seniority = data["Seniority"]
            nodes.append({
                "data": {
                    "id": node,
                    "label": seniority,
                    "name": f"{data['FirstName']} {data['LastName']}",
                    **data
                }
            })

    # Style mappings for nodes
    node_styles = [
        NodeStyle(label, TASK_COLOR_MAP[label], "name", "task") for label in TASK_STATUS_LABEL_MAP.values()
    ] + [
        NodeStyle(seniority, EMPLOYEE_COLOR_MAP[seniority], "name", "person") for seniority in EMPLOYEE_COLOR_MAP
    ]
    # Add edges
    for emp_from, task_to, data in task_graph.edges(data=True):
        edges.append({
            "data": {
                "id": f"{emp_from}->{task_to}",
                "label": data["relationship"],
                "source": emp_from,
                "target": task_to,
            }
        })

    # Style mappings for edges
    edge_styles = [
        EdgeStyle("assigned", color="#E57373", caption='label', directed=True),
        EdgeStyle("advised", color="#64B5F6", caption='label', directed=True),
    ]

    elements = {
        "nodes": nodes,
        "edges": edges,
    }

    return elements, node_styles, edge_styles
