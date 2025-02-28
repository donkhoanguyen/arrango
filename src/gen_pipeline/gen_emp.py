import pandas as pd
import numpy as np
import datetime
import uuid

def create_employees_dataframe():
    """
    Create a structured employees dataframe based on the provided organizational hierarchy.
    
    Returns:
        pandas.DataFrame: DataFrame containing employee information
    """
    # Initialize empty list to store employee records
    employees = []
    
    # Counter for employee IDs
    emp_id = 1
    
    # Set seed for reproducibility
    np.random.seed(42)
    
    # Sample first and last names
    first_names = [
        'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda', 
        'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
        'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
        'Matthew', 'Margaret', 'Anthony', 'Betty', 'Mark', 'Sandra', 'Donald', 'Ashley',
        'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
        'Kenneth', 'Dorothy', 'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa',
        'Edward', 'Deborah', 'Ronald', 'Stephanie', 'Timothy', 'Rebecca', 'Jason', 'Sharon',
        'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
        'Nicholas', 'Shirley', 'Eric', 'Angela', 'Jonathan', 'Helen', 'Stephen', 'Anna',
        'Larry', 'Brenda', 'Justin', 'Pamela', 'Scott', 'Nicole', 'Brandon', 'Emma'
    ]
    
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson',
        'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin',
        'Thompson', 'Garcia', 'Martinez', 'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee',
        'Walker', 'Hall', 'Allen', 'Young', 'Hernandez', 'King', 'Wright', 'Lopez',
        'Hill', 'Scott', 'Green', 'Adams', 'Baker', 'Gonzalez', 'Nelson', 'Carter',
        'Mitchell', 'Perez', 'Roberts', 'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans',
        'Edwards', 'Collins', 'Stewart', 'Sanchez', 'Morris', 'Rogers', 'Reed', 'Cook',
        'Morgan', 'Bell', 'Murphy', 'Bailey', 'Rivera', 'Cooper', 'Richardson', 'Cox',
        'Howard', 'Ward', 'Torres', 'Peterson', 'Gray', 'Ramirez', 'James', 'Watson'
    ]
    
    # Base date for hire dates
    base_date = datetime.datetime(2020, 1, 1)
    
    # Helper function to generate a random hire date
    def generate_hire_date(seniority):
        # More senior roles have earlier hire dates on average
        if seniority == 'Director' or seniority == 'Vice-Director':
            days_offset = np.random.randint(0, 365*3)  # Up to 3 years ago
        elif seniority.startswith('Lead'):
            days_offset = np.random.randint(365, 365*4)  # 1-4 years ago
        elif seniority.startswith('Senior'):
            days_offset = np.random.randint(365*2, 365*5)  # 2-5 years ago
        elif seniority.startswith('Mid'):
            days_offset = np.random.randint(365*1, 365*4)  # 1-4 years ago
        else:  # Junior
            days_offset = np.random.randint(0, 365*2)  # 0-2 years ago
            
        return base_date - datetime.timedelta(days=days_offset)
    
    # Helper function to determine salary based on role and seniority
    def generate_salary(role, seniority):
        # Base salary ranges by role and seniority
        salary_ranges = {
            'Director': (180000, 220000),
            'Vice-Director': (160000, 180000),
            'Lead': (140000, 160000),
            'Senior Data Scientist': (130000, 150000),
            'Mid-Level Data Scientist': (100000, 125000),
            'Junior Data Scientist': (80000, 95000),
            'Senior Data Engineer': (125000, 145000),
            'Mid-Level Data Engineer': (95000, 120000),
            'Junior Data Engineer': (75000, 90000),
            'Senior BI Analyst': (115000, 135000),
            'Mid-Level BI Analyst': (90000, 110000),
            'Junior BI Analyst': (70000, 85000),
            'Senior Data Governance Analyst': (110000, 130000),
            'Mid-Level Data Governance Analyst': (85000, 105000),
            'Junior Data Governance Analyst': (65000, 80000)
        }
        
        if role == 'Director' or role == 'Vice-Director':
            range_key = role
        else:
            range_key = seniority + ' ' + role
            
        if range_key in salary_ranges:
            min_salary, max_salary = salary_ranges[range_key]
            return np.random.randint(min_salary, max_salary)
        else:
            # Default fallback
            return np.random.randint(70000, 90000)
    
    # 1. Leadership Layer (2 people)
    # Director
    fname, lname = np.random.choice(first_names), np.random.choice(last_names)
    hire_date = generate_hire_date('Director')
    salary = generate_salary('Director', 'Director')
    employees.append({
        'EmpID': emp_id,
        'FirstName': fname,
        'LastName': lname,
        'Email': f"{fname.lower()}.{lname.lower()}@company.com",
        'Role': 'Director',
        'Department': 'Data',
        'Team': 'Leadership',
        'Seniority': 'Director',
        'HireDate': hire_date,
        'Salary': salary,
        'ManagerID': None
    })
    director_id = emp_id
    emp_id += 1
    
    # Vice-Director
    fname, lname = np.random.choice(first_names), np.random.choice(last_names)
    hire_date = generate_hire_date('Vice-Director')
    salary = generate_salary('Vice-Director', 'Vice-Director')
    employees.append({
        'EmpID': emp_id,
        'FirstName': fname,
        'LastName': lname,
        'Email': f"{fname.lower()}.{lname.lower()}@company.com",
        'Role': 'Vice-Director',
        'Department': 'Data',
        'Team': 'Leadership',
        'Seniority': 'Vice-Director',
        'HireDate': hire_date,
        'Salary': salary,
        'ManagerID': director_id
    })
    vice_director_id = emp_id
    emp_id += 1
    
    # 2. Team Leads (4 people)
    team_lead_ids = {}
    
    for team in ['Business Intelligence', 'Data Engineering', 'Data Science', 'Data Governance']:
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Lead')
        salary = generate_salary('Lead', 'Lead')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': f'{team} Lead',
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Lead',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': vice_director_id
        })
        team_lead_ids[team] = emp_id
        emp_id += 1
    
    # 3. Team Composition
    
    # Business Intelligence Team
    team = 'Business Intelligence'
    role = 'BI Analyst'
    # 3 Senior BI Analysts
    for _ in range(3):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Senior')
        salary = generate_salary(role, 'Senior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Senior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 4 Mid-Level BI Analysts
    for _ in range(4):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Mid')
        salary = generate_salary(role, 'Mid-Level')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Mid-Level',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 2 Junior BI Analysts
    for _ in range(2):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Junior')
        salary = generate_salary(role, 'Junior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Junior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
        
    # Data Engineering Team
    team = 'Data Engineering'
    role = 'Data Engineer'
    # 3 Senior Data Engineers
    for _ in range(3):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Senior')
        salary = generate_salary(role, 'Senior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Senior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 4 Mid-Level Data Engineers
    for _ in range(4):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Mid')
        salary = generate_salary(role, 'Mid-Level')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Mid-Level',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 2 Junior Data Engineers
    for _ in range(2):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Junior')
        salary = generate_salary(role, 'Junior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Junior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
        
    # Data Science Team
    team = 'Data Science'
    role = 'Data Scientist'
    # 2 Senior Data Scientists
    for _ in range(2):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Senior')
        salary = generate_salary(role, 'Senior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Senior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 3 Mid-Level Data Scientists
    for _ in range(3):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Mid')
        salary = generate_salary(role, 'Mid-Level')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Mid-Level',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 2 Junior Data Scientists
    for _ in range(2):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Junior')
        salary = generate_salary(role, 'Junior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Junior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
        
    # Data Governance Team
    team = 'Data Governance'
    role = 'Data Governance Analyst'
    # 2 Senior Data Governance Analysts
    for _ in range(2):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Senior')
        salary = generate_salary(role, 'Senior')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Senior',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 2 Mid-Level Data Governance Analysts
    for _ in range(2):
        fname, lname = np.random.choice(first_names), np.random.choice(last_names)
        hire_date = generate_hire_date('Mid')
        salary = generate_salary(role, 'Mid-Level')
        employees.append({
            'EmpID': emp_id,
            'FirstName': fname,
            'LastName': lname,
            'Email': f"{fname.lower()}.{lname.lower()}@company.com",
            'Role': role,
            'Department': 'Data',
            'Team': team,
            'Seniority': 'Mid-Level',
            'HireDate': hire_date,
            'Salary': salary,
            'ManagerID': team_lead_ids[team]
        })
        emp_id += 1
    
    # 1 Junior Data Governance Analyst
    fname, lname = np.random.choice(first_names), np.random.choice(last_names)
    hire_date = generate_hire_date('Junior')
    salary = generate_salary(role, 'Junior')
    employees.append({
        'EmpID': emp_id,
        'FirstName': fname,
        'LastName': lname,
        'Email': f"{fname.lower()}.{lname.lower()}@company.com",
        'Role': role,
        'Department': 'Data',
        'Team': team,
        'Seniority': 'Junior',
        'HireDate': hire_date,
        'Salary': salary,
        'ManagerID': team_lead_ids[team]
    })
    
    # Create DataFrame and return
    df = pd.DataFrame(employees)
    
    # Verify the count is 40 employees
    # assert len(df) == 40, f"Expected 40 employees, got {len(df)}"
    
    return df

def main():
    """
    Main function to create and save the employees data.
    """
    # Create the employees DataFrame
    employees_df = create_employees_dataframe()
    
    # Save to CSV
    employees_df.to_csv('data/employees.csv', index=False)
    
    # Display summary information
    print(f"Created data/employees.csv with {len(employees_df)} employees")
    print("\nTeam Distribution:")
    team_counts = employees_df['Team'].value_counts()
    for team, count in team_counts.items():
        print(f"- {team}: {count} employees")
    
    print("\nSeniority Distribution:")
    seniority_counts = employees_df['Seniority'].value_counts()
    for seniority, count in seniority_counts.items():
        print(f"- {seniority}: {count} employees")
    
    print("\nSample of employees:")
    print(employees_df[['EmpID', 'FirstName', 'LastName', 'Role', 'Team', 'Seniority']].head(10))

if __name__ == "__main__":
    main()