import os
import streamlit as st
import networkx as nx
import pandas as pd
import nx_arangodb as nxadb
import re

from agent import create_new_agent

os.environ["LANGSMITH_TRACING"] = st.secrets["LANGSMITH_TRACING"]
os.environ["LANGSMITH_ENDPOINT"] = st.secrets["LANGSMITH_ENDPOINT"]
os.environ["LANGSMITH_API_KEY"] = st.secrets["LANGSMITH_API_KEY"]
os.environ["LANGSMITH_PROJECT"] = st.secrets["LANGSMITH_PROJECT"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from langchain_core.messages.ai import AIMessageChunk
from typing import Literal
from langgraph.prebuilt import create_react_agent
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
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")

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
def ask_hits_question(question, df, model_name="gpt-4o"):
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


tools = [get_weather, generate_image_metadata, analyze_image_metadata, 
         choose_graph, create_cpm_table, ask_cpm_question,
         ask_hits_question, create_hits_table]
agent = create_react_agent(model, tools=tools)

DEFAULT_CHAT_AVATAR_MAP = {
    "user": "❓",
    "assistant": "💁",
}



class ChatInstance:
    def __init__(self, chatbot_id: str, context: str):
        if "GRAPH_CACHE" not in st.session_state:
            raise ValueError("Graph cache is not loaded yet, cannot start chatbot")

        self.GRAPH_CACHE = st.session_state.GRAPH_CACHE
        if chatbot_id not in st.session_state:
            st.session_state[chatbot_id] = [
                {
                    "role": "system",
                    "content": f"You are a helpful chatbot in a Project Dashboard of a human company. The user's context is this '{context}'. First, warmly welcome the user and explain quickly about what you can do, including explaining 2 or 3 type and example questions you are equpiped best to answer with the given context. Do it in under 100 words, and make sure the questions are in markdown list.",
                }
            ]
        self.chatbot_id = chatbot_id
        self.context = context
        self.agent = create_new_agent()

    def get_messages(self):
        return st.session_state[self.chatbot_id]

    def append_message(self, message):
        st.session_state[self.chatbot_id].append(message)

    def _callback_append_user_msg(self):
        user_msg = st.session_state[f"{self.chatbot_id}/prev_user_msg"]
        self.append_message({"role": "user", "content": user_msg})

    def process_stream(self, stream):
        for message, metadata in stream:
            if isinstance(message, ToolMessage):
                with st.expander(f"Used tool [{message.name}]"):
                    st.markdown("Tool Response:")
                    st.markdown(f"```\n{message.content}\n```")
                    # self.append_message({"role": "tool", "name": message.name, "content": message.content})
                yield "\n [using tool]\n"
            
            if isinstance(message, AIMessageChunk):
                if metadata["langgraph_node"] == "tools":
                    yield ""
                else:
                    yield message.content

    def render(self):
        messages = self.get_messages()

        with st.container(height=500):
            # Display chat messages from history on app rerun
            for message in messages:
                # Skip system prompt
                if message["role"] == "system" or message["role"] == "tool":
                    continue
                with st.chat_message(message["role"], avatar=DEFAULT_CHAT_AVATAR_MAP[message["role"]]):
                    st.markdown(message["content"])
            
            # If is new chatbot, then open with an welcome
            if len(messages) == 1 or messages[-1]["role"] == "user":
                with st.chat_message("assistant", avatar=DEFAULT_CHAT_AVATAR_MAP["assistant"]):
                    stream = self.get_response_stream()
                    response = st.write_stream(self.process_stream(stream))
                self.append_message({"role": "assistant", "content": response})

            # Start accepting chat
        st.chat_input("What do you want to do today?", key=f"{self.chatbot_id}/prev_user_msg", on_submit=self._callback_append_user_msg)
    def get_response_stream(self):
        messages = self.get_messages()
        stream = self.agent.stream(
            {
                "messages": self.get_messages(),
                "graph_cache": self.GRAPH_CACHE,
                "chosen_graph_name": None,
                "original_query": messages[-1]["content"],
                "original_context": self.context
            },
            stream_mode="messages"
        )
        # print_stream(stream)
        return stream

    def chat(self, query):
        self.append_message({"role": "user", "content": query})
