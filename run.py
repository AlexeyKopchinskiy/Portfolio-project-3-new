# Your code goes here.
# You can delete these comments, but do not change the name of this file
# Write your code to expect a terminal of 80 characters wide and 24 rows high

import os
import json
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

data = tasks.get_all_values()

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


# Example usage of the add_task function
# add_task(
#     task_name="Complete Python project",
#     deadline="2025-03-15",
#     priority="High",
#     category="Work",
#     project="102",
#     notes="Focus on Google Sheets integration"
# )

def main():
    """
    Main function to initialize the program and display a menu of options.
    """
    print("Welcome to the Task Manager!")

    while True:
        print("\nPlease select an option:")
        print("1 - Add a new task")
        print("2 - Review deadlines")
        print("3 - View tasks list")
        print("4 - Exit")

        # Get the user's choice
        user_choice = input("Enter the number of your choice: ").strip()

        if user_choice == "1":
            interactive_add_task()
        elif user_choice == "2":
            review_deadlines()  # Placeholder function for now
        elif user_choice == "3":
            view_tasks_list()  # Placeholder function for now
        elif user_choice == "4":
            print("Exiting the Task Manager. Have a great day!")
            break
        else:
            print("Invalid input. Please enter a number between 1 and 4.")

def interactive_add_task():
    """
    Collect task details interactively via the console and add a task.
    """
    print("Please enter the task details:")

    # Fetch category and project data
    categories_data = categories.get_all_values()[1:]  # Skip header row
    projects_data = projects.get_all_values()[1:]  # Skip header row

    # Prepare category and project options
    category_options = ", ".join([f"{row[0]}: {row[1]}" for row in categories_data])
    project_options = ", ".join([f"{row[0]}: {row[1]}" for row in projects_data])

    print(f"Available Categories: {category_options}")
    print(f"Available Projects: {project_options}")

    # Prompt user for task details
    task_name = input("Task Name: ")
    deadline = input("Deadline (YYYY-MM-DD): ")
    priority = input("Priority (High, Medium, Low): ")
    category = input(f"Category (Choose ID from: {category_options}): ")
    project = input(f"Project (Choose ID from: {project_options}): ")
    notes = input("Notes (Optional): ")

    # Call the add_task function with user-provided input
    add_task(
        task_name=task_name,
        deadline=deadline,
        priority=priority,
        category=category,
        project=project,
        notes=notes
    )
   
    print(f"Task '{task_name}' added successfully!")

# Placeholder functions for upcoming features
def review_deadlines():
    """
    Fetch tasks from the 'tasks' sheet and display them sorted by deadlines.
    """
    print("\nReviewing upcoming deadlines...")

    # Fetch all task data (excluding the header row)
    task_data = tasks.get_all_values()[1:]  # Skip header row

    # Filter tasks with deadlines and convert the deadline to datetime objects
    upcoming_tasks = []
    for row in task_data:
        if row[3]:  # Check if a deadline exists (index 3 in your task structure)
            deadline_date = datetime.strptime(row[3], "%Y-%m-%d")
            upcoming_tasks.append({
                "ID": row[0],  # Task ID
                "Name": row[1],  # Task Name
                "Deadline": deadline_date,
                "Priority": row[6],  # Priority
                "Status": row[5],  # Status
                "Notes": row[9]   # Notes
            })
    
    # Sort tasks by deadline
    sorted_tasks = sorted(upcoming_tasks, key=lambda x: x["Deadline"])

    # Display sorted tasks
    if sorted_tasks:
        print("\nUpcoming Deadlines:")
        for task in sorted_tasks:
            deadline_str = task["Deadline"].strftime("%Y-%m-%d")
            print(f"- ID: {task['ID']}, Name: {task['Name']}, Deadline: {deadline_str}, "
                  f"Priority: {task['Priority']}, Status: {task['Status']}, Notes: {task['Notes']}")
    else:
        print("No tasks with deadlines found.")

def view_tasks_list():
    print("Feature under construction: View tasks list.")

# Entry point for the program
main()