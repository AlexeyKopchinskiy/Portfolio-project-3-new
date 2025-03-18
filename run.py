"""
run.py

This module is the sole component of the Task Manager application, handling all functionality 
within a single file using Object-Oriented Programming (OOP). It integrates task, category, 
and project management features while maintaining clear and modular design principles.

Features:
- Fully self-contained application for managing tasks, categories, and projects.
- Encapsulates all logic within a single module using classes and methods.
- Loads, updates, and manages tasks with data persistence through Google Sheets.
- Provides a user interface for efficient task management operations.

Usage:
    Run this script to start the Task Manager application:
    $ python run.py

Modules and Dependencies:
- Google Sheets API: Used to connect to and interact with task, category, and project data.
- datetime: Facilitates deadline validation and date-related functionality.

Classes and Functions:
- TaskManager: Central class that encapsulates all task management logic.
- Task: Represents individual tasks and their attributes (e.g., name, deadline, priority).
- load_tasks(), add_task(), update_task(): Key methods for handling task operations.

Author:
- Alexey Kopchinskiy

Date:
- 18-03-2025
"""

from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

from datetime import datetime

import gspread


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

# Utility function for retrying API calls with exponential backoff


def retry_with_backoff(func, *args, retries=5, delay=1):
    """
    Retry a function with exponential backoff in case of APIError (e.g., 429 quota errors).

    Args:
        func (callable): The function to retry.
        *args: Arguments for the function.
        retries (int): Maximum number of retries.
        delay (int): Initial delay in seconds between retries.

    Returns:
        The result of the function call if successful.

    Raises:
        Exception: If all retries fail, the original exception is re-raised.
    """

    import time
    for attempt in range(retries):
        try:
            return func(*args)
        except APIError as e:
            if "429" in str(e):
                print(
                    f"Quota exceeded. Retrying in {delay * (2 ** attempt)} seconds...")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise  # Re-raise non-429 errors
    raise Exception("Exceeded maximum retries.")


class Task:
    """
    Represents an individual task with related attributes and methods.
    """

    def __init__(self,
                 task_id,
                 name,
                 deadline,
                 priority,
                 status="Pending",
                 notes="",
                 category=None,
                 project=None,
                 create_date=None):
        self.task_id = task_id
        self.name = name
        self.deadline = deadline
        self.priority = priority
        self.status = status
        self.notes = notes
        self.category = category
        self.project = project
        self.complete_date = None
        self.create_date = create_date

    def mark_as_completed(self):
        """Marks the task as completed and sets the completion date."""
        self.status = "Completed"
        self.complete_date = datetime.now().strftime("%Y-%m-%d")

    def update(self, **kwargs):
        """Dynamically updates attributes of the task."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __str__(self):
        """String representation of a task."""
        return (f"Task(ID: {self.task_id}, Name: {self.name}, Deadline: {self.deadline}, "
                f"Priority: {self.priority}, Status: {self.status}, Notes: {self.notes})")


class TaskManager:
    """
    Manages tasks and their interactions with the Task class and Google Sheets.
    """

    def __init__(self, tasks_sheet, projects_sheet, categories_sheet):
        self.tasks_sheet = tasks_sheet
        self.projects_sheet = projects_sheet
        self.categories_sheet = categories_sheet
        self.tasks = self.load_tasks()

    # Helper methods for data validation
    def validate_task_name(self, name):
        """
        Validates the task name to ensure it is not empty and does not exceed 50 characters.
        Args: name (str): The name of the task to validate.
        Returns: str: An error message if the task name is invalid, 
            or None if the validation succeeds.
        """
        if not name or len(name) > 50:
            return "Task name must be non-empty and 50 characters or less."
        return None

    def validate_deadline(self, deadline):
        """
        Validates the task deadline to ensure it is in the correct date format (YYYY-MM-DD)
        and not set in the past.
        Args: deadline (str): The deadline date as a string in the format YYYY-MM-DD.
        Returns: str: An error message if the deadline is invalid, 
            or None if the validation succeeds.
        """
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            if deadline_date < datetime.now():
                return "Deadline cannot be in the past."
        except ValueError:
            return "Invalid deadline format. Please use YYYY-MM-DD."
        return None

    def validate_priority(self, priority):
        """
        Validates the task priority to ensure it is one of the allowed values:
        'High', 'Medium', or 'Low'.
        Args: priority (str): The priority level of the task.
        Returns: str: An error message if the priority is invalid, 
            or None if the validation succeeds.
        """
        valid_priorities = ["High", "Medium", "Low"]
        if priority not in valid_priorities:
            return "Invalid priority. Please choose from High, Medium, or Low."
        return None

    def validate_category_id(self, category_id):
        """
        Validates the category ID to ensure it exists within the valid categories
        retrieved from the categories sheet.
        Args: category_id (str): The ID of the category to validate.
        Returns: str: An error message if the category ID is invalid, 
            or None if the validation succeeds.
        """
        category_ids = [row[0] for row in retry_with_backoff(self.categories_sheet.get_all_values)[
            1:]]  # Skip header row
        if category_id not in category_ids:
            return "Invalid category ID. Please choose from the available categories."
        return None

    def validate_project_id(self,
                            project_id,
                            name=None,
                            deadline=None,
                            priority=None,
                            category_id=None):
        """
        Validates various aspects of a task, including project ID, task name, deadline, priority, 
        and category ID.
        Args:
            project_id (str): The project ID to validate.
            name (str, optional): The name of the task to validate. Defaults to None.
            deadline (str, optional): The deadline for the task in the format YYYY-MM-DD. 
                Defaults to None.
            priority (str, optional): The priority level of the task ('High', 'Medium', 'Low'). 
                Defaults to None.
            category_id (str, optional): The category ID to validate. Defaults to None.
        Returns:
            str: An error message if any validation fails, or None if all validations succeed.
        """

        # Fetch valid project IDs and category IDs
        project_ids = [row[0] for row in retry_with_backoff(self.projects_sheet.get_all_values)[
            1:]]  # Skip header row
        category_ids = [row[0] for row in retry_with_backoff(self.categories_sheet.get_all_values)[
            1:]]  # Skip header row

        # Validate project ID
        if project_id not in project_ids:
            return "Invalid project ID. Please choose from the available projects."

        # Validate name if provided
        if name is not None:
            if not name.strip() or len(name) > 50:
                return "Task name must be non-empty and 50 characters or less."

        # Validate deadline if provided
        if deadline is not None:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                if deadline_date < datetime.now():
                    return "Deadline cannot be in the past."
            except ValueError:
                return "Invalid deadline format. Please use YYYY-MM-DD."

        # Validate priority if provided
        if priority is not None:
            valid_priorities = ["High", "Medium", "Low"]
            if priority not in valid_priorities:
                return "Invalid priority. Please choose from High, Medium, or Low."

        # Validate category ID if provided
        if category_id is not None:
            if category_id not in category_ids:
                return "Invalid category ID."

        # If all validations pass
        return None

    def get_project_name(self, project_id):
        """
        Fetches the project name corresponding to a given project ID.
        Args: project_id (str): The ID of the project.
        Returns: str: The name of the project, or 'Unknown Project' if the ID is not found.
        """
        project_data = retry_with_backoff(self.projects_sheet.get_all_values)
        project_dict = {row[0]: row[1]
                        for row in project_data[1:]}  # Skip header row
        return project_dict.get(project_id, "Unknown Project")


    def get_category_name(self, category_id):
        """
        Fetches the category name corresponding to a given category ID.
        Args: category_id (str): The ID of the category.
        Returns: str: The name of the category, or 'Unknown Category' if the ID is not found.
        """
        category_data = retry_with_backoff(self.categories_sheet.get_all_values)[
            1:]  # Skip header
        # Create a dictionary of ID: Name
        category_dict = {row[0]: row[1] for row in category_data}
        return category_dict.get(category_id, "Unknown Category")

    def load_tasks(self):
        """
        Load tasks from the Google Sheets into Task objects.
        """
        task_data = retry_with_backoff(self.tasks_sheet.get_all_values)[
            1:]  # Skip header row
        loaded_tasks = []

        for row in task_data:
            loaded_tasks.append(Task(
                task_id=row[0],
                name=row[1],
                deadline=row[3],
                priority=row[6],
                status=row[5],
                notes=row[9],
                category={"id": row[7], "name": self.get_category_name(
                    row[7])},  # Convert to dictionary
                project={"id": row[8], "name": self.get_project_name(
                    row[8])}     # Convert to dictionary
            ))

        return loaded_tasks


    def generate_unique_task_id(self):
        """
        Generate the next sequential task ID based on the highest existing task ID.
        """
        existing_ids = [int(task.task_id)
                        for task in self.tasks if task.task_id.isdigit()]
        # If there are no existing IDs, start with 1
        next_id = max(existing_ids, default=0) + 1
        return str(next_id)


    def add_task(self,
                 name,
                 deadline,
                 priority,
                 category_id,
                 project_id,
                 notes="",
                 create_date=None):
        """
        Create a new task and add it to the task list.

        Args:
            name (str): Name of the task.
            deadline (str): Deadline of the task in YYYY-MM-DD format.
            priority (str): Task priority ('High', 'Medium', 'Low').
            category_id (str): Task category ID.
            project_id (str): Task project ID.
            notes (str): Optional notes for the task. Default is an empty string.
            create_date (str, optional): The date the task is created in YYYY-MM-DD format. 
                Defaults to today's date.

        Returns:
            None
        """
        # Use the current date if create_date is not provided
        if create_date is None:
            create_date = datetime.now().strftime("%Y-%m-%d")

        # Fetch category and project names
        category_name = self.get_category_name(category_id)
        project_name = self.get_project_name(project_id)

        # Generate a unique task ID
        new_task_id = self.generate_unique_task_id()

        # Create the new task object
        new_task = Task(
            task_id=new_task_id,
            name=name,
            deadline=deadline,
            priority=priority,
            status="Pending",  # Default status
            notes=notes,
            create_date=create_date,
            category={"id": category_id, "name": category_name},
            project={"id": project_id, "name": project_name}
        )

        # Add the new task to the task list
        self.tasks.append(new_task)

        # Sync with Google Sheets or other storage
        self.tasks_sheet.append_row([
            new_task.task_id,
            new_task.name,
            new_task.create_date,
            new_task.deadline,
            "",
            new_task.status,
            new_task.priority,
            new_task.category["name"],
            new_task.project["name"],
            new_task.notes
        ])
        print(f"Task '{name}' added successfully with ID {new_task_id}, "
              f"Category '{category_name}', Project '{project_name}', \
                and Create Date '{create_date}'.")

    def create_task_from_input(self):
        """
        Create a new task by collecting user input, with options 
        for selecting project and category names.
        """
        # Prompt for task name
        while True:
            name = input("Enter task name: ").strip()
            error = self.validate_task_name(name)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Prompt for task deadline
        while True:
            deadline = input("Enter task deadline (YYYY-MM-DD): ").strip()
            error = self.validate_deadline(deadline)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Prompt for task priority
        while True:
            priority = input(
                "Enter task priority (High, Medium, Low): ").strip().capitalize()
            error = self.validate_priority(priority)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Display category options and prompt for selection
        print("Available categories:")
        category_data = retry_with_backoff(self.categories_sheet.get_all_values)[
            1:]  # Skip header row
        for row in category_data:
            print(f"ID: {row[0]}, Name: {row[1]}")
        while True:
            category_id = input("Enter category ID: ").strip()
            error = self.validate_category_id(category_id)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Display project options and prompt for selection
        print("Available projects:")
        project_date = retry_with_backoff(self.projects_sheet.get_all_values)[
            1:]  # Skip header row
        for row in project_date:
            print(f"ID: {row[0]}, Name: {row[1]}")
        while True:
            project_id = input("Enter project ID: ").strip()
            error = self.validate_project_id(project_id)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Prompt for notes
        notes = input("Enter additional notes (optional): ").strip()

        # Automatically add the current date as the create date
        create_date = datetime.now().strftime("%Y-%m-%d")

        # Add the task
        self.add_task(name, deadline, priority, category_id,
                      project_id, notes, create_date)

    def view_tasks(self):
        """
        Display all tasks in a table-like format with field names as the header.
        Excludes notes and category fields, and adds ': ' after the project name if present.
        """
        if not self.tasks:
            print("No tasks found.")
            return

        # Define the header row for the table
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]

        # Print the header row
        print(
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        # Print each task as a row in the table
        for task in self.tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")

    def review_deadlines(self):
        """
        Display tasks sorted by their deadlines in a table-like format.
        """
        if not self.tasks:
            print("No tasks found.")
            return

        # Sort tasks by deadline (convert to datetime for proper sorting)
        sorted_tasks = sorted(
            self.tasks,
            key=lambda task: datetime.strptime(task.deadline, "%Y-%m-%d")
        )

        # Define the header row
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]

        # Print the header row
        print(
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        # Print each task
        for task in sorted_tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")


    def update_task(self):
        """
        Update an existing task by modifying its attributes, with a retry mechanism
        for invalid inputs. Changes are saved to both the in-memory list and Google Sheets.
        """
        if not self.tasks:
            print("No tasks available to update.")
            return

        # Display tasks in a table-like format
        print("\n--- Update a Task ---")
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]
        print(
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        for task in self.tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")

        # Get Task ID from the user
        while True:
            task_id = input(
                "Enter the ID of the task you want to update: ").strip()
            task = next((t for t in self.tasks if str(
                t.task_id) == task_id), None)
            if not task:
                print("Task ID not found. Please try again.")
            else:
                break

        # Show update options
        print("\nWhat would you like to update?")
        print("1 - Task Name")
        print("2 - Deadline")
        print("3 - Priority")
        print("4 - Notes")
        print("5 - Status")

        # Main update loop
        while True:
            loaded_choice = input("Enter the number of your choice: ").strip()

            if loaded_choice == "1":  # Update Task Name
                while True:
                    new_name = input("Enter the new task name: ").strip()
                    error = self.validate_task_name(new_name)
                    if error:
                        print(f"Error: {error}")
                    else:
                        task.name = new_name
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 2, new_name)
                        print("Task name updated successfully!")
                        break

            elif loaded_choice == "2":  # Update Deadline
                while True:
                    new_deadline = input(
                        "Enter the new deadline (YYYY-MM-DD): ").strip()
                    error = self.validate_deadline(new_deadline)
                    if error:
                        print(f"Error: {error}")
                    else:
                        task.deadline = new_deadline
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 4, new_deadline)
                        print("Task deadline updated successfully!")
                        break

            elif loaded_choice == "3":  # Update Priority
                while True:
                    new_priority = input(
                        "Enter the new priority (High, Medium, Low): ").strip().capitalize()
                    error = self.validate_priority(new_priority)
                    if error:
                        print(f"Error: {error}")
                    else:
                        task.priority = new_priority
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 7, new_priority)
                        print("Task priority updated successfully!")
                        break

            elif loaded_choice == "4":  # Update Notes
                while True:
                    new_notes = input("Enter the new notes: ").strip()
                    if len(new_notes) > 250:
                        print(
                            "Warning: Notes exceeded 250 characters and will be truncated.")
                        new_notes = new_notes[:250]
                    task.notes = new_notes
                    self.tasks_sheet.update_cell(
                        int(task.task_id) + 1, 10, new_notes)
                    print("Task notes updated successfully!")
                    break

            elif loaded_choice == "5":  # Update Status
                while True:
                    new_status = input(
                        "Enter the new status (Pending, In Progress, Completed): ").strip()
                    if new_status not in ["Pending", "In Progress", "Completed"]:
                        print(
                            "Invalid status. Please choose from Pending, In Progress, or Completed.")
                    else:
                        task.status = new_status
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 6, new_status)
                        print("Task status updated successfully!")
                        break

            else:
                print("Invalid choice. Please choose a valid option.")
                continue  # Prompt user again for a valid choice

            # Exit the update loop after successful editing
            break


    def delete_task(self):
        """
        Archive a task by moving it to the 'Deleted' tab in Google Sheets
        and removing it from the 'Tasks' tab and in-memory list.
        """
        if not self.tasks:
            print("No tasks available to delete.")
            return

        # Display tasks to help the user choose
        print("\n--- Delete (Archive) a Task ---")
        print("Available Tasks:")
        for task in self.tasks:
            print(
                f"ID: {task.task_id}, Name: {task.name}, Status: {task.status}")

        # Get Task ID from the user
        task_id = input(
            "Enter the ID of the task you want to delete: ").strip()
        task = next((t for t in self.tasks if str(
            t.task_id) == task_id), None)

        if not task:
            print("Task ID not found. Please try again.")
            return

        # Move the task to the "Deleted" tab
        deleted_tab = SHEET.worksheet("deleted")
        deleted_tab.append_row([
            task.task_id,  # Task ID
            task.name,     # Task Name
            datetime.now().strftime("%Y-%m-%d"),  # Deletion Date
            task.deadline,  # Deadline
            task.complete_date if task.complete_date else "",  # Complete Date
            task.status,   # Status
            task.priority,  # Priority
            task.category,  # Category ID
            task.project,  # Project ID
            task.notes     # Notes
        ])

        # Find the row in the "Tasks" tab
        task_rows = retry_with_backoff(self.tasks_sheet.get_all_values)
        for i, row in enumerate(task_rows):
            if row[0] == task.task_id:  # Match the Task ID
                self.tasks_sheet.delete_rows(i + 1)  # Row index is 1-based
                print(
                    f"Task '{task.name}' has been removed from the 'Tasks' tab.")
                break

        # Remove the task from the in-memory list
        self.tasks.remove(task)

        print(
            f"Task '{task.name}' has been archived and moved to the 'Deleted' tab.")

    def mark_task_completed(self):
        """
        Mark a task as completed by updating the status and completion date.
        """
        if not self.tasks:
            print("No tasks available to mark as completed.")
            return

        # Display tasks to help the user choose
        print("\n--- Mark a Task as Completed ---")
        print("Available Tasks:")
        for task in self.tasks:
            if task.status != "Completed":  # Only show incomplete tasks
                print(
                    f"ID: {task.task_id}, Name: {task.name}, Status: {task.status}")

        # Get Task ID from the user
        task_id = input(
            "Enter the ID of the task you want to mark as completed: ").strip()
        task = next((t for t in self.tasks if str(
            t.task_id) == task_id), None)

        if not task:
            print("Task ID not found. Please try again.")
            return

        if task.status == "Completed":
            print(f"Task '{task.name}' is already marked as completed.")
            return

        # Update the task's status and completion date
        task.mark_as_completed()

        # Update the Google Sheet
        task_row = int(task.task_id) + 1  # Account for header row
        self.tasks_sheet.update_cell(
            task_row, 6, "Completed")  # Update Status column
        # Update Complete Date column
        self.tasks_sheet.update_cell(task_row, 5, task.complete_date)

        print(
            f"Task '{task.name}' has been marked as completed successfully!")

    def view_tasks_by_project(self):
        """
        Display tasks filtered by a specific project ID in a table-like format.
        """
        if not self.tasks:
            print("No tasks available to view.")
            return

        # Display available projects
        print("\n--- View Tasks by Project ---")
        print("Available Projects:")
        project_ids = [row[0] for row in retry_with_backoff(self.projects_sheet.get_all_values)[
            1:]]  # Skip header
        # Skip header
        for row in retry_with_backoff(self.projects_sheet.get_all_values)[1:]:
            print(f"ID: {row[0]}, Name: {row[1]}")

        # Get the project ID from the user
        project_id = input("Enter the Project ID to view tasks for: ").strip()
        if project_id not in project_ids:
            print("Invalid Project ID. Please try again.")
            return

        # Filter tasks by project ID
        filtered_tasks = [
            task for task in self.tasks if task.project["id"] == project_id
        ]

        if not filtered_tasks:
            print(f"No tasks found for Project ID {project_id}.")
            return

        # Define the header row
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]

        # Print the header row
        print(
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        # Print each task
        for task in filtered_tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")



# Initialize the TaskManager
manager = TaskManager(tasks, projects, categories)

while True:
    print("\nPlease select an option:")
    print("1 - Add a new task")
    print("2 - Review deadlines")
    print("3 - View tasks list")
    print("4 - Update a task")
    print("5 - Delete (archive) a task")
    print("6 - Mark a task as completed")
    print("7 - View tasks by project")
    print("8 - Exit")

    choice = input("Enter your choice: ").strip()
    if choice == "1":
        manager.create_task_from_input()
    elif choice == "2":
        manager.review_deadlines()
    elif choice == "3":
        manager.view_tasks()
    elif choice == "4":
        manager.update_task()
    elif choice == "5":
        manager.delete_task()
    elif choice == "6":
        manager.mark_task_completed()
    elif choice == "7":
        manager.view_tasks_by_project()
    elif choice == "8":
        print("Exiting Task Manager. Goodbye!")
        break
    else:
        print("Option not yet implemented. Stay tuned!")
