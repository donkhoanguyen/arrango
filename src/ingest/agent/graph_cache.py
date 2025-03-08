import json
from langchain_openai import ChatOpenAI
import nx_arangodb as nxadb

from langchain_core.tools import tool
from arango.database import StandardDatabase

NODE_SCHEMA = {
    "employee": {
        "_id": "employee/<_key>",
        "_key": "<int> The ID of the employee in this company",
        "FirstName": "<string> The first name of this employee",
        "LastName": "<string> The last name of this employee",
        "Email": "<email> The email of this employee",
        "Role": "<string> The role or job title of this employee",
        "Department": "<string> The department in which the employee works",
        "Team": "<string> The specific team within the department",
        "Seniority": "<string> The seniority level of this employee",
        "HireDate": "<date> The date this employee was hired in YYYY-MM-DD format"
    },
    "task": {
        "_id": f"<name of the tasks collection, specified as tasks_col>/<TaskID>",
        "TaskID": "<string> the ID of this task",
        "Description": "<string> short description of this task",
        "StoryPoints": "<int> The count of this story points",
        "Status": "<'Planned'|'In Progress'|'Blocked'|'Completed'> the status of this task",
    }
}

EDGE_SCHEMA = {
    "interacts with": {
        "_from": "employee's <_id>",
        "_to": "employee's <_id>",
        "description": "The _to employee has had extended help with _from employee to make the _from employee achieve some tasks"
    },
    "depends on": {
        "_from": "<task _id>",
        "_to": "<task _id>",
        "description": "The _from task depends on the 'Completed' Status of all its _to neighbor to get started"
    },
    "assigned to": {
        "_from": "employee's <_id>",
        "_to": "task's <_id>",
        "relationship": "assigned",
        "description": "The employee assigned to a task will be the one who is expected to COMPLETE and DELIVER it. Here, mostly junior and midlevels are assigned"
    },
    "advised": {
        "_from": "employee's <_id>",
        "_to": "task's <_id>",
        "relationship": "advised",
        "description": "The employee advised a task will be the one who is expected to QUALITY CONTROL and MAKE SURE the assigned meets expectation. Here, mostly seniors and lead are advising a task"
    }
}

class GraphWrapper:
    def __init__(self, db: StandardDatabase, graph: nxadb.DiGraph, name: str, schema: dict[str, str], description: str):
        self.db = db
        self.graph = graph
        self.name = name
        self.schema = schema
        self.description = description
    
    def __repr__(self):
        return f"NetworkX DiGraph with name '{self.name}', schema: {self.schema}, and overall description: {self.description}"

    def load_graph(self):
        if self.graph is not None:
            print(f"Graph with name {self.graph} is already loaded!")
            return
        
        self.graph = nxadb.DiGraph(name=self.name, db=self.db)

@tool
def choose_graph(graph_cache: dict[str, GraphWrapper], query: str, context: str):
    """
    Given the user's query and original context on why this is asked, choose the
    most appropriate graph to load for subsequent queries from a list of graphs
    along with their schema and description.

    Args:
        graph_cache: The cache for preloaded graphs, will be provided in the current state
        query: The original query of the user
        context: The schema of our graph database
        
    Returns:
        The name of the graph to query from and a brief reason why we chose this one.
    """
    # Initialize llm
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o")
    
    graph_list = [str(graph_cache[graph_name]) for graph_name in graph_cache] 
      
    prompt = f"""
        You are a master database system manager. You are responsible for choosing
        the appropriate graphs with a client's query and the original context on
        what specifics might the client be asking.
        Query: {query}
        Original Context: {context} 
        
        Your graph database system has the following types of nodes: {NODE_SCHEMA}
        and the following types of edges: {EDGE_SCHEMA}.
        
        You have these following graph databases along with their schema and their brief
        description: {graph_list}
        
        With the above information, first give a brief reason why you would choose this,
        and then the chosen graph name. You MUST return in only JSON format, as follows:
        {"{"} 
        "reason": "brief reason why you would choose this graph",
        "name": "the name of the chosen graph name"
        {"}"} 
    """
    print(prompt) 
    response = llm.invoke(prompt)
    
    response_json = json.loads(response)
    
    return response_json["name"], response_json["reason"] 
    