import os
import nx_arangodb as nxadb

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
            "AssignedEmployees": task.get("AssignedEmployees", []),
            "Advisors": task.get("Advisors", []),
            "PrecedingTasks": task.get("PrecedingTasks", []),
            "StoryPoints": task.get("StoryPoints"),
            "StartTime": task.get("StartTime"),
            "EstimatedFinishTime": task.get("EstimatedFinishTime"),
            "Status": task.get("Status"),
            "ActualFinishTime": task.get("ActualFinishTime")
        }
        task_dict[f"task/{task['_key']}"] = task_info
    
    return task_dict

def get_employee_interact_graph():
    return nxadb.Graph(name="employee_interaction")

        
SENIORITY_LABEL_MAP = {
    "Lead": "Lead",
    "Senior": "SeniorEmployee",
    "Mid-Level": "MidLevelEmployee",
    "Junior": "JuniorEmployee"
}

def retrieve_employee_interaction_graph(emp_interact_graph, emp_info_dict):

    employee_information = get_all_employees()
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
                **employee_information[employee_node]
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
                "label": "Interact",
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
