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
    col1, col2, _= st.columns(3)

    with col1:
        if st.button("ℹ️ More info", key=f"more_info/employee{employee['EmpID']}"):
            employee_modal(employee)
    with col2:
        if st.button('✨ Magic Ask', key=f"magic_ask/employee{employee['EmpID']}"):
            magic_ask_employee(employee)
       
    st.markdown("---")

def get_status_color(status):
    """Returns a color for the status tag."""
    status_colors = {
        "Planned": "#d3d3d3",  # Gray
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
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        ">
            <p style="margin: 0; font-size: 20px; font-weight: bold;">
                {task.get("Description", "Unknown")}
            </p>
            <div style="background-color: {status_color};
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                display: inline-block;
                margin-right: 10px;">
                {task.get("Status", "Planned")}
            </div>
            <br> </br> 
            <p style="color: #555;">Task ID: {task.get("TaskID", "No description available.")}</p>
            <p><b>Assigned Employees:</b> {', '.join(task.get("AssignedEmployees", [])) or 'None'}</p>
            <p><b>Advisors:</b> {', '.join(task.get("Advisors", [])) or 'None'}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    
    col1, col2, _ = st.columns(3)

    with col1:
        if st.button("ℹ️ More info", key=f"more_info/task{task['TaskID']}"):
            task_modal(task)
    with col2:
        if st.button('✨ Magic Ask', key=f"magic_ask/task{task['TaskID']}"):
            magic_ask_task(task)
    
    st.markdown("---")

@st.dialog("Magic Ask Employee")
def magic_ask_employee(employee):
    st.chat_input(f"What do you want to ask about {employee['FirstName']}?")
    # TODO: Implement CPM and HITS Promotion Analysis here

@st.dialog("Magic Ask Task")
def magic_ask_task(task):
    st.chat_input(f"What do you want to ask about Task {task['TaskID']}?")
    # TODO: Implement CPM and HITS Promotion Analysis here

@st.dialog("Employee Information")
def employee_modal(employee):
    # Creating a modal-like layout for employee information
    st.markdown(f"## Employee: {employee['FirstName']} {employee['LastName']}")
    st.markdown(f"### Employee ID: {employee['EmpID']}")
    
    # Employee Details Section
    st.markdown("### Employee Details")
    st.markdown(f"**First Name**: {employee['FirstName']}")
    st.markdown(f"**Last Name**: {employee['LastName']}")
    st.markdown(f"**Email**: {employee['Email']}")
    st.markdown(f"**Role**: {employee['Role']}")
    st.markdown(f"**Department**: {employee['Department']}")
    st.markdown(f"**Team**: {employee['Team']}")
    st.markdown(f"**Seniority Level**: {employee['Seniority']}")
    
    # Salary and Hire Date Section
    st.markdown("### Salary and Hire Date")
    st.markdown(f"**Salary**: {employee['Salary']}")
    st.markdown(f"**Hire Date**: {employee['HireDate']}")
    
    # Manager Section
    if employee['ManagerID']:
        st.markdown("### Manager Information")
        st.markdown(f"**Manager ID**: {employee['ManagerID']}")
    else:
        st.markdown("### Manager Information")
        st.markdown("This employee doesn't have a manager listed.")
    
    # Optional: Adding a divider for separation
    st.markdown("---")
    
    # Additional Notes Section (Optional)
    st.markdown("### Notes")
    st.markdown("You can add additional information or notes about the employee here.")
    st.markdown("For example, performance reviews, special achievements, or other remarks.")

@st.dialog("Task Information")
def task_modal(task):
    """Modal dialog for displaying task details."""
    
    # Task Title
    st.markdown(f"## Task: {task['TaskID']}")
    st.markdown(f"### {task['Description']}")

    # Task Details
    st.markdown("### Task Details")
    st.markdown(f"**Task ID**: {task['TaskID']}")
    st.markdown(f"**Description**: {task['Description']}")
    st.markdown(f"**Story Points**: {task.get('StoryPoints', 'N/A')}")
    
    # Status with color tag
    status_color = {
        "Not Started": "#d3d3d3",
        "In Progress": "#f39c12",
        "Completed": "#2ecc71",
        "Blocked": "#e74c3c"
    }.get(task.get("Status", "Not Started"), "#bdc3c7")

    st.markdown(
        f'<div style="background-color: {status_color}; color: white; padding: 5px 10px; '
        'border-radius: 5px; font-size: 12px; font-weight: bold; display: inline-block;">'
        f"{task.get('Status', 'Not Started')}</div>",
        unsafe_allow_html=True
    )

    # Assigned Employees & Advisors
    st.markdown("### Assigned Employees")
    assigned_employees = ", ".join(task.get("AssignedEmployees", [])) or "None"
    st.markdown(f"**Employees**: {assigned_employees}")

    st.markdown("### Advisors")
    advisors = ", ".join(task.get("Advisors", [])) or "None"
    st.markdown(f"**Advisors**: {advisors}")

    # Task Timing
    st.markdown("### Task Timeline")
    st.markdown(f"**Start Time**: {task.get('StartTime', 'Unknown')}")
    st.markdown(f"**Estimated Finish Time**: {task.get('EstimatedFinishTime', 'Unknown')}")
    st.markdown(f"**Actual Finish Time**: {task.get('ActualFinishTime', 'Not Finished')}")

    # Preceding Tasks
    if "PrecedingTasks" in task and task["PrecedingTasks"]:
        preceding_tasks = ", ".join(task["PrecedingTasks"])
        st.markdown("### Preceding Tasks")
        st.markdown(f"{preceding_tasks}")
    else:
        st.markdown("### Preceding Tasks")
        st.markdown("No preceding tasks.")

    # Divider
    st.markdown("---")
    
    # Notes (Optional)
    st.markdown("### Notes")
    st.markdown("Add any relevant details or comments about this task.")

def accordion_graph_chatbot(G):
    with st.expander("✨ Ask about this graph!"):
        st.chat_input("Hello")
