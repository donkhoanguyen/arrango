import streamlit as st
import networkx as nx
import pandas as pd
import re

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from arango import ArangoClient
from langchain_openai import ChatOpenAI
from networkx.utils import backends


db = ArangoClient(hosts="https://b61c3b83bfe6.arangodb.cloud:8529") \
    .db(username="root", 
        password="RHr0KzkRUVlp61IisH8G", 
        name="DAC_devops_log",
        verify=True)

model = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=st.secrets["OPENAI_API_KEY"])


@tool    
def create_cpm_table(G_adb):
    """
    Create a dataframe from the Critical Path Method (CPM) analysis of our graph.

    Args:
        G_adb: The ArangoDB graph object

    Returns:
        A pandas DataFrame with the CPM analysis results
    """

    for node in G_adb.nodes():
        story_points = G_adb.nodes[node].get("StoryPoints", "1")  # Default to 1 if missing
        G_adb.nodes[node]["duration"] = int(story_points)  # Ensure integer conversion

    # Step 1: Compute earliest start (ES) and finish (EF)
    es = {}  # Earliest Start
    ef = {}  # Earliest Finish

    with backends.override_backend("nx"):
        for node in nx.topological_sort(G_adb):
            es[node] = max((ef.get(pred, 0) for pred in G_adb.predecessors(node)), default=0)
            ef[node] = es[node] + G_adb.nodes[node]["duration"]

    # Step 2: Compute latest finish (LF) and start (LS)
    lf = {}  # Latest Finish
    ls = {}  # Latest Start

    # Start from the last node in the topological order
    project_duration = max(ef.values())  # Total project duration
    for node in reversed(list(nx.topological_sort(G_adb))):
        lf[node] = min((ls.get(succ, project_duration) for succ in G_adb.successors(node)), default=project_duration)
        ls[node] = lf[node] - G_adb.nodes[node]["duration"]

    # Step 3: Compute slack time
    slack = {node: ls[node] - es[node] for node in G_adb.nodes()}

    slack_score = pd.DataFrame(list(slack.items()), columns=['TaskID', 'slack_time'])
    slack_score['TaskID'] = slack_score['TaskID'].str.replace('task/', '')
    slack_score = slack_score.sort_values(by='slack_time', ascending=False)
    # slack_score.head(10)
    es_score = pd.DataFrame(list(es.items()), columns=['TaskID', 'earliest_start'])
    es_score['TaskID'] = es_score['TaskID'].str.replace('task/', '')
    es_score = es_score.sort_values(by='earliest_start', ascending=False)
    # es_score.head(10)
    ls_score = pd.DataFrame(list(ls.items()), columns=['TaskID', 'latest_start'])
    ls_score['TaskID'] = ls_score['TaskID'].str.replace('task/', '')
    ls_score = ls_score.sort_values(by='latest_start', ascending=False)
    # ls_score.head(10)

    merged_df = es_score.merge(slack_score, on='TaskID', how='outer')\
                           .merge(ls_score, on='TaskID', how='outer')

    merged_df = merged_df.sort_values(by=['latest_start', 'slack_time'], ascending=[True, True])

    return merged_df

@tool
def ask_cpm_question(question, df, model_name="gpt-4o"):
    """
    Provide information about tasks using critical path method.

    If asked questions about what tasks to do next,  determine the order in which tasks should be executed using the Critical Path Method (CPM). 
    Tasks should be sorted by latest start (ascending) to ensure that tasks with the tightest deadlines are completed first. 
    If two tasks have the same latest start, prioritize the one with the lower slack time to avoid delaying critical tasks.
    Normally give the top 5 tasks to do next.
    
    Args:
        question: string containing the question about the dataframe
        model_name: Optional OpenAI model to use (default: gpt-4)
    
    Returns:
        Answer from ChatGPT about the dataframe
    """
    llm = ChatOpenAI(temperature=0, model_name=model_name, api_key=st.secrets["OPENAI_API_KEY"])
    
    # Get dataframe info
    df_info = df.info(buf=None, max_cols=None, memory_usage=None, show_counts=None)
    df_head = df.head()
    df_describe = df.describe()

    print("1) Generating python code")
    # Construct prompt
    text_to_python = llm.invoke(f"""
    I have a pandas dataframe with the following information:
    
    DataFrame Info:
    {df_info}
    
    First few rows:
    {df_head}
    
    Summary statistics:
    {df_describe}
    
    Question: {question}
    
    Generate the Python Code required to answer the query using the `df` object.
    I already have this dataframe and DO NOT RE-INITIALIZE any dataframe. I will give you one and you will use my dataframe.
    Be very precise and think step by step.

    Always set the last variable as `FINAL_RESULT`, which represents the answer to the original query.

    Only provide python code that I can directly execute via `exec()`. Do not provide any instructions.

    Make sure that `FINAL_RESULT` stores a short & consice answer. Avoid setting this variable to a long sequence.

    Your code:
    """).content

    text_to_python_cleaned = re.sub(r"^```python\n|```$", "", text_to_python, flags=re.MULTILINE).strip()
    
    print('-'*10)
    print(text_to_python_cleaned)
    print('-'*10)

    print("\n2) Executing python code")
    global_vars = {"df": df}
    local_vars = {}

    try:
        exec(text_to_python_cleaned, global_vars, local_vars)
        text_to_python_final = text_to_python
    except Exception as e:
        print(f"EXEC ERROR: {e}")
        return f"EXEC ERROR: {e}"

    print('-'*10)
    FINAL_RESULT = local_vars["FINAL_RESULT"]
    print(f"FINAL_RESULT: {FINAL_RESULT}")
    print('-'*10)

    print("3) Formulating final answer")

    python_to_text = llm.invoke(f"""
    I have a pandas dataframe with the following information: 
                                
    DataFrame Info:
    {df_info}
    
    First few rows:
    {df_head}
    
    Summary statistics:
    {df_describe}

    I have executed the following Python code to answer the query:
    ---
        {text_to_python_final}
    ---

    The `FINAL_RESULT` variable is set to the following: {FINAL_RESULT}.

    Based on my original Query and FINAL_RESULT, generate a short and concise response to
    answer my query.
          
    """).content
    
    return python_to_text