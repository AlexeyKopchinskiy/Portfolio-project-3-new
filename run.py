# Your code goes here.
# You can delete these comments, but do not change the name of this file
# Write your code to expect a terminal of 80 characters wide and 24 rows high

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('Python Task Manager')

tasks = SHEET.worksheet('tasks')
projects = SHEET.worksheet('project')
categories = SHEET.worksheet('category')

print("Projects Data:")
print(projects.get_all_values())
print("Categories Data:")
print(categories.get_all_values())


data = tasks.get_all_values()

# print(data)

def add_task(task_name, deadline, priority, category, project, notes=""):
    """
    Add a new task to the 'tasks' tab.
    :param task_name: Name of the task
    :param deadline: Due date for the task (format: YYYY-MM-DD)
    :param priority: Priority level (e.g., High, Medium, Low)
    :param category: Category ID (must match the 'category' tab)
    :param project: Project ID (must match the 'project' tab)
    :param notes: Additional notes for the task (optional)
    """
    # Get the current date as the creation date
    create_date = datetime.now().strftime("%Y-%m-%d")
    
    # Auto-increment the task ID based on the number of rows
    new_id = len(tasks.get_all_values())

    # Prepare the new task as a list
    new_task = [
        new_id,         # Task ID
        task_name,      # Task name
        create_date,    # Creation date
        deadline,       # Deadline
        "",             # Complete date (empty by default)
        "Pending",      # Default status
        priority,       # Priority
        category,       # Category
        project,        # Project
        notes           # Notes
    ]

    # Append the new task to the tasks tab
    tasks.append_row(new_task)
    print(f"Task '{task_name}' added successfully!")
