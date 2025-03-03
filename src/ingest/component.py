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
    if st.button("More info", key=f"more_info/employee{employee['EmpID']}"):
        employee_modal(employee)
    

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
        <div style="
            background: #f5f5f5;
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
