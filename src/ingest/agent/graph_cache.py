import json
import streamlit as st
from typing import Any
from langchain_openai import ChatOpenAI
import nx_arangodb as nxadb

from langchain_core.tools import tool
from arango.database import StandardDatabase
from agent import env


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
    
    def get_full_schema(self):
        full_schema = {"nodes": {}, "edges": {}}
        
        for node in self.schema["nodes"]:
            full_schema["nodes"][node] = NODE_SCHEMA[node]
        
        for edge in self.schema["edges"]:
            full_schema["edges"][edge] = NODE_SCHEMA[edge]

        return full_schema


choose_graph_template = env.get_template("choose_graph_prompt.jinja")
@tool
def choose_graph(graph_cache: dict[str, Any], query: str, context: str):
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
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])
    llm = llm.bind(response_format={"type": "json_object"})
    
    graph_list = [str(graph_cache[graph_name]) for graph_name in graph_cache] 
      
    prompt = choose_graph_template.render({
        "query": query,
        "context": context,
        "NODE_SCHEMA": NODE_SCHEMA,
        "EDGE_SCHEMA": EDGE_SCHEMA,
        "graph_list": graph_list,
    })
    
    response = llm.invoke(prompt)
    response_json = json.loads(response.content)
    
    return response_json["name"], response_json["reason"] 
    