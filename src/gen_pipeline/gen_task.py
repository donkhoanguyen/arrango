import pandas as pd
import numpy as np
import datetime
import uuid
import os
import openai
from openai import OpenAI
import json
from dotenv import load_dotenv

# Load environment variables (for OpenAI API key)
load_dotenv()

class TaskDatabaseGenerator:
    def __init__(self, employees_file='data/employees.csv'):
        """
        Initialize the Task Database Generator system.
        
        Args:
            employees_file: Path to existing employees CSV file.
        """
        # Load existing employees data
        if os.path.exists(employees_file):
            self.employees_df = pd.read_csv(employees_file)
            print(f"Loaded {len(self.employees_df)} employees from file.")
        else:
            raise FileNotFoundError(f"Employees file {employees_file} not found. Please provide a valid file path.")
            
        # Initialize tasks dataframe
        self.tasks_df = pd.DataFrame(columns=[
            'TaskID', 
            'Description', 
            'AssignedEmployees', 
            'Advisors', 
            'PrecedingTasks', 
            'StoryPoints', 
            'StartTime', 
            'EstimatedFinishTime',
            'Status',
            'ActualFinishTime'
        ])
        
        # Load tasks data if file exists
        if os.path.exists('data/tasks.csv'):
            self.tasks_df = pd.read_csv('data/tasks.csv')
            print(f"Loaded {len(self.tasks_df)} existing tasks from file.")
    
    def generate_task_id(self):
        """Generate a unique TaskID."""
        return f"TSK-{uuid.uuid4().hex[:8].upper()}"
    
    def add_task(self, description, assigned_employees, advisors, preceding_tasks, 
                 story_points, start_time, estimated_finish_time, status='Planned', actual_finish_time=None):
        """
        Add a new task to the system.
        
        Args:
            description: String description of the task
            assigned_employees: List of EmpIDs assigned to the task
            advisors: List of EmpIDs serving as advisors/verifiers
            preceding_tasks: List of TaskIDs that must be completed before this task
            story_points: Integer representing complexity/effort
            start_time: Timestamp when the task begins
            estimated_finish_time: Timestamp when the task is expected to be completed
            status: Current status of the task (default: 'Planned')
            actual_finish_time: Timestamp when the task was actually completed (if applicable)
        """
        # Validate employees exist
        for emp_id in assigned_employees + advisors:
            if emp_id not in self.employees_df['EmpID'].values:
                raise ValueError(f"Employee ID {emp_id} does not exist")
                
        # Validate preceding tasks exist
        for task_id in preceding_tasks:
            if task_id and task_id not in self.tasks_df['TaskID'].values:
                raise ValueError(f"Task ID {task_id} does not exist")
        
        # Generate a new TaskID
        task_id = self.generate_task_id()
        
        # Format for storage
        assigned_employees_str = ','.join(map(str, assigned_employees))
        advisors_str = ','.join(map(str, advisors))
        preceding_tasks_str = ','.join(map(str, preceding_tasks))
        
        # Create a new task
        new_task = {
            'TaskID': task_id,
            'Description': description,
            'AssignedEmployees': assigned_employees_str,
            'Advisors': advisors_str,
            'PrecedingTasks': preceding_tasks_str,
            'StoryPoints': story_points,
            'StartTime': start_time,
            'EstimatedFinishTime': estimated_finish_time,
            'Status': status,
            'ActualFinishTime': actual_finish_time
        }
        
        # Add to the tasks dataframe
        self.tasks_df = pd.concat([self.tasks_df, pd.DataFrame([new_task])], ignore_index=True)
        
        # Save updated tasks to file
        self.tasks_df.to_csv('data/tasks.csv', index=False)
        
        return task_id
    
    def generate_tasks_with_openai(self, num_tasks=30, project_type="software_development"):
        """
        Generate realistic tasks using OpenAI API based on project type.
        
        Args:
            num_tasks: Number of tasks to generate
            project_type: Type of project (software_development, infrastructure, data_migration, etc.)
        """
        try:
            # Check if API key is set
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it before continuing.")
            
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            # Get employee IDs for random assignment
            employee_ids = self.employees_df['EmpID'].tolist()
            
            # Create project context based on project type
            if project_type == "software_development":
                context = "software development project with tasks including planning, design, development, testing, and deployment"
            elif project_type == "infrastructure":
                context = "infrastructure setup project with tasks including server provisioning, network configuration, security setup, and monitoring"
            elif project_type == "data_migration":
                context = "data migration project with tasks including data analysis, schema design, ETL development, validation, and cutover"
            else:
                context = f"{project_type} project with appropriate tasks for this domain"
            
            print(f"Generating {num_tasks} tasks for a {context}...")
            
            # Use OpenAI to generate project tasks
            prompt = f"""
            Generate {num_tasks} realistic DevOps and software development tasks for a {context}.
            For each task, provide:
            1. A detailed task description
            2. Story points (1-13, with higher numbers for more complex tasks)
            3. A suggested duration in days (1-14)
            
            Format your response as a JSON array with objects containing these fields:
            [
                {{
                    "description": "Detailed task description",
                    "story_points": integer between 1-13,
                    "duration_days": integer between 1-14
                }},
                ...
            ]
            """
            
            # Initialize the client (do this once)
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Replace the old response creation with:
            response = client.chat.completions.create(
                model="gpt-4",  # or your preferred model
                messages=[
                    {"role": "system", "content": "You are a project management assistant creating realistic task data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Parse the generated tasks
            try:
                tasks = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError:
                # Fallback parsing in case OpenAI doesn't return proper JSON
                content = response.choices[0].message.content
                # Find the JSON part - typically between ```json and ```
                json_start = content.find('[')
                json_end = content.rfind(']') + 1
                if json_start >= 0 and json_end > json_start:
                    tasks = json.loads(content[json_start:json_end])
                else:
                    raise ValueError("Could not parse JSON from API response")
            
            # Set project start date to today
            project_start = pd.Timestamp(datetime.datetime.now().date())
            current_date = project_start
            
            # Create task dependencies (preceding tasks)
            created_task_ids = []
            
            # First pass: Create tasks without dependencies
            for i, task_data in enumerate(tasks):
                # Determine task timing
                duration_days = task_data.get('duration_days', np.random.randint(1, 14))
                start_time = current_date + pd.Timedelta(days=np.random.randint(0, 5))  # Randomize start times a bit
                estimated_finish_time = start_time + pd.Timedelta(days=duration_days)
                
                # Select random employees for assignment (1-3 employees per task)
                num_assigned = np.random.randint(1, 4)
                assigned_employees = np.random.choice(employee_ids, num_assigned, replace=False).tolist()
                
                # Select random employees as advisors (1-2 employees)
                num_advisors = np.random.randint(1, 3)
                # Make sure advisors are different from assigned employees
                available_advisors = [e for e in employee_ids if e not in assigned_employees]
                advisors = np.random.choice(available_advisors, min(num_advisors, len(available_advisors)), replace=False).tolist()
                
                # For initial tasks, no preceding tasks
                preceding_tasks = []
                
                # Create the task
                task_id = self.add_task(
                    description=task_data['description'],
                    assigned_employees=assigned_employees,
                    advisors=advisors,
                    preceding_tasks=preceding_tasks,
                    story_points=task_data.get('story_points', np.random.randint(1, 13)),
                    start_time=start_time,
                    estimated_finish_time=estimated_finish_time
                )
                
                created_task_ids.append(task_id)
                
                # Increment date for variety
                if i % 3 == 0:  # Every few tasks, advance the date
                    current_date += pd.Timedelta(days=np.random.randint(1, 3))
            
            # Second pass: Add dependencies to some tasks
            for i in range(len(created_task_ids)):
                if i >= 5:  # Skip the first few tasks to avoid circular dependencies
                    # 70% chance of having preceding tasks
                    if np.random.random() < 0.7:
                        # Select 1-2 random preceding tasks from tasks created earlier
                        num_preceding = np.random.randint(1, 5)
                        possible_preceding = created_task_ids[:i]  # Only consider earlier tasks
                        preceding_tasks = np.random.choice(possible_preceding, 
                                                          min(num_preceding, len(possible_preceding)), 
                                                          replace=False).tolist()
                        
                        # Update the task with preceding tasks
                        task_idx = self.tasks_df[self.tasks_df['TaskID'] == created_task_ids[i]].index[0]
                        self.tasks_df.at[task_idx, 'PrecedingTasks'] = ','.join(preceding_tasks)
            
            # Save the updated dataframe
            self.tasks_df.to_csv('data/tasks.csv', index=False)
            
            print(f"Generated {len(created_task_ids)} tasks and saved to data/tasks.csv")
            
        except Exception as e:
            print(f"Error generating tasks with OpenAI: {str(e)}")
    
    def display_employees(self, limit=10):
        """Display sample of employees in the system."""
        return self.employees_df.head(limit)[['EmpID', 'FirstName', 'LastName', 'Role', 'Department']]
    
    def display_tasks(self, limit=10):
        """Display sample of tasks in the system."""
        return self.tasks_df.head(limit)


# Demo: Generate task database using the existing employees file
def generate_task_database():
    # Initialize the database generator with existing employees file
    generator = TaskDatabaseGenerator()
    
    # Display sample of employees for reference
    print("\nSample of employees from existing file:")
    print(generator.display_employees())
    
    # Generate tasks using OpenAI API
    project_types = ["software_development", "infrastructure", "data_migration"]
    selected_type = project_types[0]  # Default to software development
    
    # Prompt for project type selection
    print("\nAvailable project types:")
    for i, ptype in enumerate(project_types):
        print(f"{i+1}. {ptype.replace('_', ' ').title()}")
    
    try:
        choice = int(input("\nSelect project type (1-3) or press Enter for default: ") or "1")
        if 1 <= choice <= len(project_types):
            selected_type = project_types[choice-1]
    except ValueError:
        print("Invalid input, using default project type.")
    
    # Prompt for number of tasks
    try:
        num_tasks = int(input("\nHow many tasks to generate? (default: 30) ") or "30")
    except ValueError:
        num_tasks = 30
        print("Invalid input, using default 30 tasks.")
    
    # Generate tasks
    generator.generate_tasks_with_openai(num_tasks=num_tasks, project_type=selected_type)
    
    # Display sample of generated tasks
    print("\nSample of generated tasks:")
    print(generator.display_tasks())
    
    print(f"\nTask generation complete. All {num_tasks} tasks have been saved to data/tasks.csv")


# Manual task entry function
def manual_task_entry():
    generator = TaskDatabaseGenerator()
    
    print("\nManual Task Entry")
    print("-----------------")
    
    # Display employees for reference
    print("\nEmployee List:")
    print(generator.display_employees(limit=40))  # Show all employees
    
    # Get task information
    description = input("Task Description: ")
    
    # Get assigned employees
    assigned_input = input("Assigned Employee IDs (comma-separated): ")
    assigned_employees = [int(emp_id.strip()) for emp_id in assigned_input.split(",") if emp_id.strip()]
    
    # Get advisors
    advisors_input = input("Advisor Employee IDs (comma-separated): ")
    advisors = [int(emp_id.strip()) for emp_id in advisors_input.split(",") if emp_id.strip()]
    
    # Display existing tasks
    if len(generator.tasks_df) > 0:
        print("\nExisting Tasks:")
        print(generator.tasks_df[['TaskID', 'Description']])
        
        # Get preceding tasks
        preceding_input = input("Preceding Task IDs (comma-separated, or leave blank): ")
        preceding_tasks = [task_id.strip() for task_id in preceding_input.split(",") if task_id.strip()]
    else:
        preceding_tasks = []
    
    # Get story points
    story_points = int(input("Story Points (1-13): ") or "5")
    
    # Get dates - default to current date for start, estimated finish 7 days later
    default_start = datetime.datetime.now().strftime("%Y-%m-%d")
    default_end = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    start_date = input(f"Start Date (YYYY-MM-DD, default: {default_start}): ") or default_start
    end_date = input(f"Estimated Finish Date (YYYY-MM-DD, default: {default_end}): ") or default_end
    
    # Create task
    task_id = generator.add_task(
        description=description,
        assigned_employees=assigned_employees,
        advisors=advisors,
        preceding_tasks=preceding_tasks,
        story_points=story_points,
        start_time=pd.Timestamp(start_date),
        estimated_finish_time=pd.Timestamp(end_date)
    )
    
    print(f"\nTask created successfully! Task ID: {task_id}")
    
    
# Main entry point
if __name__ == "__main__":
    print("DevOps Task Database Creator")
    print("============================")
    print("1. Generate Task Database with OpenAI API")
    print("2. Manual Task Entry")
    
    choice = input("\nEnter your choice (1 or 2): ")
    
    if choice == "1":
        generate_task_database()
    elif choice == "2":
        manual_task_entry()
    else:
        print("Invalid choice. Exiting.")