import os
import random
import nx_arangodb as nxadb
import networkx as nx

from st_link_analysis import st_link_analysis, NodeStyle, EdgeStyle
from arango import ArangoClient

os.environ["DATABASE_HOST"] = "https://b61c3b83bfe6.arangodb.cloud:8529"
os.environ["DATABASE_USERNAME"] = "root"
os.environ["DATABASE_PASSWORD"] = "RHr0KzkRUVlp61IisH8G"
os.environ["DATABASE_NAME"] = "DAC_devops_log"

client = ArangoClient(hosts=os.environ["DATABASE_HOST"])
db = client.db(
    os.environ["DATABASE_NAME"],
    username=os.environ["DATABASE_USERNAME"],
    password=os.environ["DATABASE_PASSWORD"]
)

# Function to get all employee information as a dictionary with EmpID as the key
def get_all_employees():
    # Access the employee vertex collection
    employee_collection = db.collection('employee')  # Ensure this is the correct collection name
    
    # Fetch all employees from the collection
    employees = employee_collection.all()  # Fetches all documents in the collection
    
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
def get_all_tasks():
    task_collection = db.collection('task')  # Ensure this is the correct collection name
    
    # Fetch all employees from the collection
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
            # "Status": task.get("Status"),
            "Status": random.choice(list(TASK_STATUS_LABEL_MAP.keys())),
            "ActualFinishTime": task.get("ActualFinishTime")
        }
        task_dict[f"task/{task['_key']}"] = task_info
    
    return task_dict

def get_employee_interact_graph():
    return nxadb.Graph(name="employee_interaction")

def get_task_dependence_graph():
    return nxadb.DiGraph(name="tasks_sprint1")


        
SENIORITY_LABEL_MAP = {
    "Lead": "Lead",
    "Senior": "SeniorEmployee",
    "Mid-Level": "MidLevelEmployee",
    "Junior": "JuniorEmployee"
}

TASK_STATUS_LABEL_MAP = {
    "Planned": "PlannedTask",
    "In Progress": "InProgressTask",
    "Complete": "CompleteTask",
    "Blocked": "BlockedTask"
}

def retrieve_employee_interaction_graph(emp_interact_graph, emp_info_dict):
    nodes = []
    edges = []
    
    for employee_node in emp_interact_graph.nodes:
        employee_info = emp_info_dict[employee_node]
        seniority = employee_info["Seniority"] 


        nodes.append({
            "data": {
                "id": employee_node, 
                "label": SENIORITY_LABEL_MAP.get(seniority, "Employee"),
                "name": f"{employee_info['FirstName']} {employee_info['LastName']}",
                **emp_info_dict[employee_node]
            }
        })
    # Style node & edge groups
    node_styles = [
        NodeStyle("Lead", "#FF7F3E", "name", "person"),           # Orange
        NodeStyle("SeniorEmployee", "#4CAF50", "name", "person"), # Green
        NodeStyle("MidLevelEmployee", "#2196F3", "name", "person"), # Blue
        NodeStyle("JuniorEmployee", "#FFC107", "name", "person"), # Amber
        NodeStyle("Employee", "#9C27B0", "name", "person"),       # Purple
    ]
    for emp_from, emp_to in emp_interact_graph.edges:
        if (emp_from == "employee/0" or emp_to == "employee/0"):
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

def retrieve_task_dependence_graph(task_interact_graph, task_info_dict):
    nodes = []
    edges = []
    
    if nx.is_directed_acyclic_graph(task_interact_graph):
        print("Yup")
    else:
        print("FUck")
    topological_order = list(nx.topological_sort(task_interact_graph))
    print("Topological Sort:", topological_order)

    for task_node in task_interact_graph.nodes:
        task_info = task_info_dict[task_node]

        nodes.append({
            "data": {
                "id": task_node, 
                "label": TASK_STATUS_LABEL_MAP.get(task_info["Status"], "Planned"),
                "name": task_info["TaskID"],
                **task_info_dict[task_node]
            }
        })
    # Style node & edge groups
    node_styles = [
        NodeStyle("PlannedTask", "#d3d3d3", "name", "person"),           # Orange
        NodeStyle("InProgressTask", "#f39c12", "name", "person"), # Green
        NodeStyle("CompleteTask", "#2ecc71", "name", "person"), # Blue
        NodeStyle("BlockedTask", "#e74c3c", "name", "person"), # Amber
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