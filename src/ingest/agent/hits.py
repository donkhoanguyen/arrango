import streamlit as st
import networkx as nx
import pandas as pd
import nx_arangodb as nxadb
import re

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from arango import ArangoClient
from langchain_openai import ChatOpenAI
from langchain_community.graphs import ArangoGraph


db = ArangoClient(hosts="https://b61c3b83bfe6.arangodb.cloud:8529") \
    .db(username="root", 
        password="RHr0KzkRUVlp61IisH8G", 
        name="DAC_devops_log",
        verify=True)

model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=st.secrets["OPENAI_API_KEY"])



@tool
def choose_graph(question):
    """
    Given the user's question + our graph database schema + our logic, choose the right graph to query from.

    Args:
        question: The user's question
        schema: The schema of our graph database
        
    Returns:
        The name of the graph to query from.
    """    
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o", api_key=st.secrets["OPENAI_API_KEY"])    

    db = ArangoClient(hosts="https://b61c3b83bfe6.arangodb.cloud:8529") \
    .db(username="root", 
        password="RHr0KzkRUVlp61IisH8G", 
        name="DAC_devops_log",
        verify=True)
    
    arango_graph = ArangoGraph(db)

    graph_name = llm.invoke(f"""
    I have a graph database with the following information:
    
    Graph Schema:
    {arango_graph.schema}
    
    User question:
    {question}

    Given the user's question and our graph database schema, determine the right graph to query from.

    Give me nothing but the name of the graph. Do not provide any additional information.

    Your code:
    """).content

    G_adb = nxadb.DiGraph(name=graph_name)

    return G_adb

@tool
def create_hits_table(G_adb):
    """
    Create a pandas DataFrame from the HITS analysis of our graph.

    Args:
        G_adb: The ArangoDB graph object

    Returns:
        A pandas DataFrame with the HITS analysis results
    """
    G_adb = nxadb.DiGraph(name="emp_interaction1")
    hubs, authorities = nx.hits(G_adb)

    print("got hub and authority")

    # Create a DataFrame from hubs and authorities
    hits_df = pd.DataFrame({
        'EmpID': list(hubs.keys()),
        'Hub_Score': list(hubs.values()),
        'Authority_Score': list(authorities.values())
    })

    print(hits_df.head(10))

    # Clean the Node column by removing 'employee/'
    hits_df['EmpID'] = hits_df['EmpID'].str.replace('employee/', '')

    # Sort by Hub Score in descending order
    hits_df = hits_df.sort_values('Hub_Score', ascending=False)

    # Reset the index
    hits_df = hits_df.reset_index(drop=True)

    return hits_df

@tool
def ask_hits_question(question, df, context = None, model_name="gpt-4o"):
    """
    Provide information about employees using Hyperlink-Induced Topic Search (HITS) to derive insight into: which employee should be on managerial track
    and which one should be on technical track.

    The Hub Score represents how likely they are to become managers.
    The authority score represents how likely they are to remain in technical roles.
    If asked about tendency of a specific employee, return that employee Hub and Authority score from their EmpID.
    Else, answer to the best of your ability.
    
    Args:
        question: string containing the question about the dataframe
        df: pandas DataFrame with the HITS analysis results
        model_name: Optional OpenAI model to use (default: gpt-4)
    
    Returns:
        Answer from ChatGPT about the dataframe
    """
    llm = ChatOpenAI(temperature=0, model_name=model_name, api_key=st.secrets["OPENAI_API_KEY"])
    
    # # Get dataframe info
    # df_info = df.info(buf=None, max_cols=None, memory_usage=None, show_counts=None)
    # df_head = df.head()
    # df_describe = df.describe()

    # print("1) Generating python code")
    # # Construct prompt
    # text_to_python = llm.invoke(f"""
    # I have a pandas dataframe with the following information:
    
    # DataFrame Info:
    # {df_info}
    
    # First few rows:
    # {df_head}
    
    # Summary statistics:
    # {df_describe}
    
    # Question: {question}
    
    # Generate the Python Code required to answer the query using the `df` object.

    # I already have this dataframe and DO NOT RE-INITIALIZE any dataframe. I will give you one and you will use my dataframe.

    # I also have additional context: {context}. Look for here EmpID in this, then combine with the result dataframe to answer my question.
    # Be very precise and think step by step.

    # Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.

    # Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.

    # Make sure that `FINAL_RESULT` stores a short & consice answer. Avoid setting this variable to a long sequence.

    # Your code:
    # """).content

    # text_to_python_cleaned = re.sub(r"^```python\n|```$", "", text_to_python, flags=re.MULTILINE).strip()
    
    # print('-'*10)
    # print(text_to_python_cleaned)
    # print('-'*10)

    # print("\n2) Executing python code")
    # global_vars = {"df": df}
    # local_vars = {}

    # try:
    #     exec(text_to_python_cleaned, global_vars, local_vars)
    #     text_to_python_final = text_to_python
    # except Exception as e:
    #     print(f"EXEC ERROR: {e}")
    #     return f"EXEC ERROR: {e}"
    

    # print('-'*10)
    # FINAL_RESULT = local_vars["FINAL_RESULT"]
    # print(f"FINAL_RESULT: {FINAL_RESULT}")
    # print('-'*10)

    # print("3) Formulating final answer")

    python_to_text = llm.invoke(f"""
    I originally asked this question: {question}. Now I receive an answer:
    {df}

    I also have additional context: {context}.

    Hubs score should be an indicator of managerial prospect and authority score should be
    and indicator of technical track prospect.

    Based on my original question, FINAL_RESULT, and topic, generate a short and concise response to
    answer my query.
          
    """).content
    
    return python_to_text


# @tool
# def search_emp_info(topic: str):
#     """
#     Search for information about an employee in a pandas DataFrame.

#     Args:
#         question: The question to be answered.
#         topic: The full name of the employee (First Name + Last Name).

#     Returns:
#         A dictionary containing all information about the employee.
#     """
#     # Load your DataFrame (assuming it's stored in a CSV file for this example)
#     df = pd.read_csv('../../data/employees.csv')
    
#     # Combine First Name and Last Name to create a full name column
#     df['FullName'] = df['FirstName'] + ' ' + df['LastName']
    
#     # Search for the employee by full name
#     employee_info = df[df['FullName'] == topic]
    
#     if employee_info.empty:
#         return {"error": "Employee not found"}
    
#     # Convert the employee information to a dictionary
#     employee_dict = employee_info.to_dict(orient='records')[0]
    
#     return employee_dict
