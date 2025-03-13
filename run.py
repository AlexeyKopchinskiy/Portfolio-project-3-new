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

# Add task to the Google sheet
def interactive_add_task():
    """
    Collect task details interactively via the console and add a new task
    directly to the 'tasks' sheet.
    """
    print("Please enter the task details:")

    # Fetch category and project data for user-friendly prompts
    categories_data = categories.get_all_values()[1:]  # Skip header row
    projects_data = projects.get_all_values()[1:]  # Skip header row

    # Prepare category and project options
    category_options = ", ".join([f"{row[0]}: {row[1]}" for row in categories_data])
    project_options = ", ".join([f"{row[0]}: {row[1]}" for row in projects_data])

    print(f"Available Categories: {category_options}")
    print(f"Available Projects: {project_options}")

    # Prompt user for task details
    task_name = input("Task Name: ")
    deadline = input("Deadline (YYYY-MM-DD or DD-MM-YYYY): ")
    priority = input("Priority (High, Medium, Low): ")
    category = input(f"Category (Choose ID from: {category_options}): ")
    project = input(f"Project (Choose ID from: {project_options}): ")
    notes = input("Notes (Optional): ")

    # Validate and format the deadline
    try:
        deadline = datetime.strptime(deadline, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        try:
            deadline = datetime.strptime(deadline, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Task creation aborted.")
            return

    # Auto-increment the task ID based on the number of rows
    new_id = len(tasks.get_all_values())

    # Get the current date as the creation date
    create_date = datetime.now().strftime("%Y-%m-%d")

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

    # Append the new task directly to the tasks tab
    tasks.append_row(new_task)
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
            try:
                # Try parsing the date in the expected format
                deadline_date = datetime.strptime(row[3], "%Y-%m-%d")
            except ValueError:
                try:
                    # Try parsing the date in the alternate format (day-month-year)
                    deadline_date = datetime.strptime(row[3], "%d-%m-%Y")
                except ValueError:
                    # Skip invalid date formats
                    print(f"Invalid date format for task '{row[1]}'. Skipping...")
                    continue

            # Append the valid task
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
        print("No tasks with valid deadlines found.")

# View task list
def view_tasks_list():
    """
    Display all tasks from the 'tasks' sheet in a user-friendly format.
    """
    print("\nFetching tasks list...")

    # Fetch all task data (excluding the header row)
    task_data = tasks.get_all_values()[1:]  # Skip header row

    if not task_data:
        print("No tasks found in the sheet.")
        return

    # Iterate through tasks and format their output
    print("\nTasks List:")
    for row in task_data:
        # Parse the deadline and complete date to handle various formats
        try:
            deadline = datetime.strptime(row[3], "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            try:
                deadline = datetime.strptime(row[3], "%d-%m-%Y").strftime("%d-%m-%Y")
            except ValueError:
                deadline = "Invalid Format"

        try:
            complete_date = datetime.strptime(row[4], "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            try:
                complete_date = datetime.strptime(row[4], "%d-%m-%Y").strftime("%d-%m-%Y")
            except ValueError:
                complete_date = "Invalid Format"

        # Print task details
        print(f"- ID: {row[0]}, Name: {row[1]}, Created: {row[2]}, Deadline: {deadline}, "
              f"Complete Date: {complete_date}, Status: {row[5]}, Priority: {row[6]}, "
              f"Category: {row[7]}, Project: {row[8]}, Notes: {row[9]}")

# Update task
def update_task():
    """
    Update an existing task in the 'tasks' sheet.
    """
    print("\nUpdate Task Details")

     # Fetch all tasks (excluding the header row)
    task_data = tasks.get_all_values()
    if len(task_data) <= 1:  # Check if there are no tasks
        print("No tasks found to update.")
        return

    # Display all tasks
    print("\nAvailable Tasks:")
    for row in task_data[1:]:
        print(f"- ID: {row[0]}, Name: {row[1]}, Status: {row[5]}, Deadline: {row[3]}")
    
    # Ask user for the task ID to update
    task_id = input("\nEnter the ID of the task you want to update: ").strip()

    # Find the task row based on the ID
    task_row = None
    for index, row in enumerate(task_data[1:], start=2):  # Start from row 2 in the sheet
        if row[0] == task_id:
            task_row = index
            break

    if not task_row:
        print("Task ID not found.")
        return
    
    # Ask which field to update
    print("\nWhat would you like to update?")
    print("1 - Task Name")
    print("2 - Status")
    print("3 - Deadline")
    print("4 - Priority")
    print("5 - Notes")
    choice = input("Enter the number of your choice: ").strip()

    if choice == "1":
        new_task_name = input("Enter new task name: ").strip()
        tasks.update_cell(task_row, 2, new_task_name)  # Column 2 is 'Task Name'
        print("Task name updated successfully!")
    
    elif choice == "2":
        new_status = input("Enter new status (Pending/In Progress/Complete): ").strip()
        tasks.update_cell(task_row, 6, new_status)  # Column 6 is 'Status'
        print("Task status updated successfully!")
    
    elif choice == "3":
        new_deadline = input("Enter new deadline (YYYY-MM-DD or DD-MM-YYYY): ").strip()
        try:
            # Validate and standardize the date format
            new_deadline = datetime.strptime(new_deadline, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            try:
                new_deadline = datetime.strptime(new_deadline, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Update aborted.")
                return
        tasks.update_cell(task_row, 4, new_deadline)  # Column 4 is 'Deadline'
        print("Task deadline updated successfully!")

    elif choice == "4":
        new_priority = input("Enter new priority (High/Medium/Low): ").strip()
        tasks.update_cell(task_row, 7, new_priority)  # Column 7 is 'Priority'
        print("Task priority updated successfully!")

    elif choice == "5":
        new_notes = input("Enter new notes: ").strip()
        tasks.update_cell(task_row, 10, new_notes)  # Column 10 is 'Notes'
        print("Task notes updated successfully!")

    else:
        print("Invalid choice. Update aborted.")

# Delete task
def delete_task():
    """
    Move a task from the 'tasks' sheet to the 'deleted' sheet based on task ID.
    """
    print("\nDelete (Archive) a Task")

    # Fetch all task data (excluding the header row)
    task_data = tasks.get_all_values()
    if len(task_data) <= 1:  # Check if there are no tasks
        print("No tasks found to delete.")
        return
    
    # Display all tasks
    print("\nAvailable Tasks:")
    for row in task_data[1:]:
        print(f"- ID: {row[0]}, Name: {row[1]}, Status: {row[5]}, Deadline: {row[3]}")
    
    # Ask user for the task ID to delete
    task_id = input("\nEnter the ID of the task you want to delete: ").strip()

    # Find the task row based on the ID
    task_row = None
    for index, row in enumerate(task_data[1:], start=2):  # Start from row 2 in the sheet
        if row[0] == task_id:
            task_row = index
            break

    if not task_row:
        print("Task ID not found.")
        return
    
    # Fetch the task details
    task_details = tasks.row_values(task_row)

    # Move the task to the 'deleted' sheet
    deleted_sheet = SHEET.worksheet('deleted')
    deleted_sheet.append_row(task_details)

    # Delete the task from the 'tasks' sheet
    tasks.delete_rows(task_row)
    print(f"Task '{task_details[1]}' (ID: {task_id}) has been successfully archived in the 'deleted' tab.")

# Mark tasks as completed
def mark_task_completed():
    """
    Mark a task as 'Completed' and optionally move it to the 'completed' sheet.
    """
    print("\nMark Task as Completed")

    # Fetch all tasks (excluding the header row)
    task_data = tasks.get_all_values()
    if len(task_data) <= 1:  # Check if there are no tasks
        print("No tasks found to mark as completed.")
        return

    # Display all tasks
    print("\nAvailable Tasks:")
    for row in task_data[1:]:
        print(f"- ID: {row[0]}, Name: {row[1]}, Status: {row[5]}, Deadline: {row[3]}")
    
     # Ask user for the task ID to mark as completed
    task_id = input("\nEnter the ID of the task you want to mark as completed: ").strip()

    # Find the task row based on the ID
    task_row = None
    for index, row in enumerate(task_data[1:], start=2):  # Start from row 2 in the sheet
        if row[0] == task_id:
            task_row = index
            break

    if not task_row:
        print("Task ID not found.")
        return
    
    # Update the task's status to 'Completed' and add the completion date
    complete_date = datetime.now().strftime("%Y-%m-%d")
    tasks.update_cell(task_row, 5, complete_date)  # Column 5 is 'Complete Date'
    tasks.update_cell(task_row, 6, "Completed")   # Column 6 is 'Status'
    print(f"Task (ID: {task_id}) has been marked as 'Completed'.")

    # Ask if the user wants to move the task to the 'completed' sheet
    move_task = input("Do you want to move this task to the 'completed' tab? (yes/no): ").strip().lower()
    if move_task == "yes":
        # Fetch the task details
        task_details = tasks.row_values(task_row)

        # Move the task to the 'completed' sheet
        completed_sheet = SHEET.worksheet('completed')
        completed_sheet.append_row(task_details)

        # Delete the task from the 'tasks' sheet
        tasks.delete_rows(task_row)
        print(f"Task '{task_details[1]}' (ID: {task_id}) has been moved to the 'completed' tab.")
    else:
        print("Task remains in the 'tasks' sheet as 'Completed'.")

# Show tasks from selected projects
def view_tasks_by_project():
    """
    Display tasks that belong to a specific project.
    """
    print("\nView Tasks by Project")

    # Fetch all projects (excluding the header row)
    project_data = projects.get_all_values()[1:]  # Skip header row

    if not project_data:
        print("No projects found.")
        return

    # Display the list of projects
    print("\nAvailable Projects:")
    for row in project_data:
        print(f"- ID: {row[0]}, Name: {row[1]}")

    # Ask the user to select a project by ID
    project_id = input("\nEnter the ID of the project to view its tasks: ").strip()

    # Fetch all task data (excluding the header row)
    task_data = tasks.get_all_values()[1:]  # Skip header row

    # Filter tasks belonging to the selected project
    filtered_tasks = [task for task in task_data if task[8] == project_id]



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
        print("4 - Update a task")
        print("5 - Delete (archive) a task")
        print("6 - Mark a task as completed")
        print("7 - Exit")

        # Get the user's choice
        user_choice = input("Enter the number of your choice: ").strip()

        if user_choice == "1":
            interactive_add_task()
        elif user_choice == "2":
            review_deadlines()
        elif user_choice == "3":
            view_tasks_list()
        elif user_choice == "4":
            update_task()
        elif user_choice == "5":
            delete_task()
        elif user_choice == "6":
            mark_task_completed()
        elif user_choice == "7":
            print("Exiting the Task Manager. Have a great day!")
            break
        else:
            print("Invalid input. Please enter a number between 1 and 7.")


# Entry point for the program
main()