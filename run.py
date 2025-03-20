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

import time
from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError
import gspread

# Import colorama for console colorization
from colorama import Fore, Back, Style

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

CONSOLE_WIDTH = 100  # Force fixed width for Heroku console

# Utility function for retrying API calls with exponential backoff

class RetryLimitExceededError(Exception):
    """
        Custom exception for when retry attempts exceed the maximum limit.
        Raised when the retry limit for an API call is exceeded.
    """

def retry_with_backoff(func, *args, retries=5, delay=1):
    """
    Retry a function with exponential backoff in case of APIError (e.g., 429 quota errors).
    Args:
        func (callable): The function to retry.
        *args: Arguments for the function.
        retries (int): Maximum number of retries.
        delay (int): Initial delay in seconds between retries.
    Returns: The result of the function call if successful.
    Raises: RetryLimitExceededError: If all retries fail.
            APIError: If the error encountered is not related to rate-limiting.
    """
    if not callable(func):
        raise TypeError(f"The provided function {func} is not callable.")

    for attempt in range(retries):
        try:
            return func(*args)
        except APIError as e:
            if "429" in str(e):  # Rate-limiting error
                print(
                    f"Quota exceeded. Retrying in {delay * (2 ** attempt)} seconds...")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
            else:
                raise  # Re-raise non-rate-limiting API errors
    # Raise a custom exception if retries are exhausted
    raise RetryLimitExceededError(
        f"Exceeded maximum retries for function {func.__name__}")

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

        # Initialize cached data
        self.cached_tasks = []  # For storing task data
        self.cached_projects = []  # For storing project data
        self.cached_categories = []  # For storing category data

        # Load and cache data from Google Sheets
        self.load_and_cache_data()
        # Load tasks into memory as Task objects
        self.tasks = self.load_tasks()

    def load_and_cache_data(self):
        """
        Fetch and cache task, project, and category data from Google Sheets.
        """
        print("Loading and caching data from Google Sheets...")

        try:
            # Fetch and cache task data
            self.cached_tasks = retry_with_backoff(
                self.tasks_sheet.get_all_values)

            # Fetch and cache project data
            self.cached_projects = retry_with_backoff(
                self.projects_sheet.get_all_values)

            # Fetch and cache category data
            self.cached_categories = retry_with_backoff(
                self.categories_sheet.get_all_values)

            print("Data successfully loaded and cached!")
        except APIError as e:
            print(f"Error while loading data: {e}")
            self.cached_tasks = []
            self.cached_projects = []
            self.cached_categories = []

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
        # Use cached project data
        project_dict = {row[0]: row[1]
                        for row in self.cached_projects[1:]}  # Skip header
        return project_dict.get(project_id, "none")

    def get_category_name(self, category_id):
        """
        Fetches the category name corresponding to a given category ID from cached data.
        Args: category_id (str): The ID of the category.
        Returns: str: The name of the category, or 'Unknown Category' if the ID is not found.
        """
        # Use cached category data
        category_dict = {row[0]: row[1]
                         for row in self.cached_categories[1:]}  # Skip header
        return category_dict.get(category_id, "Unknown Category")

    def load_tasks(self):
        """
        Load tasks from cached data into Task objects.
        """
        task_data = self.cached_tasks[1:]  # Skip header row
        project_dict = {row[0]: row[1]
                        for row in self.cached_projects[1:]}  # Skip header
        category_dict = {row[0]: row[1]
                         for row in self.cached_categories[1:]}  # Skip header

        loaded_tasks = []

        for row in task_data:
            loaded_tasks.append(Task(
                task_id=row[0],
                name=row[1],
                deadline=row[3],
                priority=row[6],
                status=row[5],
                notes=row[9],
                category={"id": row[7], "name": category_dict.get(
                    row[7], "Unknown Category")},
                project={"id": row[8], "name": project_dict.get(
                    row[8], "none")}
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
            new_task.category["id"],
            new_task.project["id"],
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
        Display all tasks in a table-like format, respecting a fixed CONSOLE_WIDTH of 80 characters.
        """
        if not self.tasks:
            print("No tasks found.")
            return

        # Calculate column widths based on CONSOLE_WIDTH
        column_widths = {
            "ID": 4,
            "Deadline": 10,
            "Priority": 8,
            "Status": 12,
            "Project": 20,
            # Remaining space for the 'Name' column
            "Name": CONSOLE_WIDTH - (4 + 10 + 8 + 12 + 20 + 5)
        }

        # Ensure all column widths fit within CONSOLE_WIDTH
        assert sum(column_widths.values()) + len(column_widths) - \
            1 <= CONSOLE_WIDTH, "Column widths exceed console width!"

        # Define the header row for the table
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]
        header_row = (
            f"{headers[0]:<{column_widths['ID']}} {headers[1]:<{column_widths['Deadline']}} "
            f"{headers[2]:<{column_widths['Priority']}} {headers[3]:<{column_widths['Status']}} "
            f"{headers[4]:<{column_widths['Project']}} {headers[5]:<{column_widths['Name']}}"
        )
        # Print the header with enforced left alignment and styling
        print(Style.BRIGHT + Fore.BLUE + header_row + Style.RESET_ALL)
        print("-" * CONSOLE_WIDTH)

        # Sort tasks by priority, ensuring 'High' is at the top
        priority_order = {"High": 1, "Medium": 2, "Low": 3, "": 4}
        sorted_tasks = sorted(
            self.tasks, key=lambda task: priority_order.get(task.priority, 5))

        # Print each task as a row in the table
        for task in sorted_tasks:
            # Truncate long text for display
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            project_display = project_display[:column_widths["Project"] - 3] + "..." if len(
                project_display) > column_widths["Project"] else project_display
            name_display = task.name[:column_widths["Name"] - 3] + \
                "..." if len(task.name) > column_widths["Name"] else task.name

            # Colorize priorities
            if task.priority == "High":
                priority_display = Back.RED + Fore.WHITE + "High  " + Style.RESET_ALL
            elif task.priority == "Medium":
                priority_display = Back.MAGENTA + Fore.WHITE + "Medium" + Style.RESET_ALL
            elif task.priority == "Low":
                priority_display = Back.GREEN + Fore.WHITE + "Low   " + Style.RESET_ALL
            elif not task.priority:
                priority_display = Back.BLACK + Fore.WHITE + "      " + Style.RESET_ALL
            else:
                priority_display = task.priority.ljust(6)

            # Print the task row
            print(
                f"{task.task_id:<{column_widths['ID']}} {task.deadline:<{column_widths['Deadline']}} "
                f"{priority_display:<{column_widths['Priority']}} {task.status:<{column_widths['Status']}} "
                f"{project_display:<{column_widths['Project']}} {name_display:<{column_widths['Name']}}"
            )

    def review_deadlines(self):
        """
        Display all tasks with their deadlines in a table-like format,
        respecting a fixed CONSOLE_WIDTH of 80 characters.
        """
        if not self.tasks:
            print("No tasks available.")
            return

        # Calculate column widths based on CONSOLE_WIDTH
        column_widths = {
            "ID": 5,
            "Name": 40,
            "Deadline": 12,
            "Priority": 10,
            "Status": 10
        }

        # Ensure all column widths fit within CONSOLE_WIDTH
        assert sum(column_widths.values()) + len(column_widths) - \
            1 <= CONSOLE_WIDTH, "Column widths exceed console width!"

        # Define the header row for the table
        headers = ["ID", "Name", "Deadline", "Priority", "Status"]
        header_row = (
            f"{headers[0]:<{column_widths['ID']}} {headers[1]:<{column_widths['Name']}} "
            f"{headers[2]:<{column_widths['Deadline']}} {headers[3]:<{column_widths['Priority']}} "
            f"{headers[4]:<{column_widths['Status']}}"
        )
        # Print the header with enforced left alignment and styling
        print(Style.BRIGHT + Fore.BLUE + header_row + Style.RESET_ALL)
        print("-" * CONSOLE_WIDTH)

        # Sort tasks by deadlines (earliest first)
        sorted_tasks = sorted(self.tasks, key=lambda task: task.deadline or "")

        # Print each task as a row in the table
        for task in sorted_tasks:
            # Truncate long text for display
            name_display = task.name[:column_widths["Name"] - 3] + \
                "..." if len(task.name) > column_widths["Name"] else task.name

            # Colorize priorities
            if task.priority == "High":
                priority_display = Back.RED + Fore.WHITE + "High  " + Style.RESET_ALL
            elif task.priority == "Medium":
                priority_display = Back.MAGENTA + Fore.WHITE + "Medium" + Style.RESET_ALL
            elif task.priority == "Low":
                priority_display = Back.GREEN + Fore.WHITE + "Low   " + Style.RESET_ALL
            elif not task.priority:
                priority_display = Back.BLACK + Fore.WHITE + "      " + Style.RESET_ALL
            else:
                priority_display = task.priority.ljust(6)

            # Print the task row
            print(
                f"{task.task_id:<{column_widths['ID']}} {name_display:<{column_widths['Name']}} "
                f"{task.deadline:<{column_widths['Deadline']}} {priority_display:<{column_widths['Priority']}} "
                f"{task.status:<{column_widths['Status']}}"
            )


    def update_task(self):
        """
        Update a task's name or other fields in both the cached data and Google Sheets.
        """
        if not self.cached_tasks or len(self.cached_tasks) <= 1:  # Ensure there are tasks beyond headers
            print("No tasks available to update.")
            return

        # Extract headers and task data
        headers = self.cached_tasks[0]  # Header row
        tasks_data = self.cached_tasks[1:]  # Task rows

        # Display tasks to help the user choose
        print("\n--- Update a Task ---")
        print("Available Tasks:")
        for task in tasks_data:
            try:
                print(f"ID: {task[0]}, Name: {task[1]}, Deadline: {task[2]}, "
                      f"Priority: {task[3]}, Status: {task[4]}, "
                      f"Category: {task[5]}, Project: {task[6]}, Notes: {task[7]}")
            except IndexError:
                print("Error: Task structure is incorrect.")
                return

        # Get Task ID from the user
        task_id = input(
            "Enter the ID of the task you want to update: ").strip()

        # Find the task in cached data
        task_to_update = next(
            (task for task in tasks_data if str(task[0]) == task_id), None)

        if not task_to_update:
            print("Task ID not found. Please try again.")
            return

        # Display the fields as a numbered list
        print("\nFields available to update:")
        field_map = {  # Create a mapping of numbers to field names
            1: "task_name",
            2: "deadline",
            3: "priority",
            4: "notes",
            5: "status",
            6: "category",
            7: "project"
        }
        for num, field in field_map.items():
            print(f"{num}. {field}")

        # Get the field number to update
        try:
            field_num = int(input(
                "Enter the number corresponding to the field you want to update: ").strip())
            # Map the number to the field name
            field_to_update = field_map.get(field_num)
            if not field_to_update:
                print("Invalid field number. Please try again.")
                return
        except ValueError:
            print("Invalid input. Please enter a number.")
            return

        # Get the new value for the selected field
        new_value = input(
            f"Enter the new value for {field_to_update}: ").strip()
        if not new_value:
            print(f"{field_to_update} cannot be empty.")
            return

        # Perform validation based on the field being updated
        if field_to_update == "task_name":
            validation_result = self.validate_task_name(new_value)
            if validation_result:
                print(validation_result)
                return

        if field_to_update == "deadline":
            validation_result = self.validate_deadline(new_value)
            if validation_result:
                print(validation_result)
                return

        if field_to_update == "priority":
            validation_result = self.validate_priority(new_value)
            if validation_result:
                print(validation_result)
                return

        if field_to_update == "category":
            validation_result = self.validate_category_id(new_value)
            if validation_result:
                print(validation_result)
                return

        if field_to_update == "project":
            validation_result = self.validate_project_id(new_value)
            if validation_result:
                print(validation_result)
                return

        # Update the selected field in the cached data
        try:
            # Get the column index dynamically
            col_index = headers.index(field_to_update)
            task_to_update[col_index] = new_value  # Update the cached task
        except ValueError:
            print(
                f"Error: Could not find '{field_to_update}' column in headers.")
            return

        # Update the relevant cell in Google Sheets
        try:
            row_index = self.cached_tasks.index(
                task_to_update)  # Find the row in the cache
            tasks.update_cell(row_index + 1, col_index + 1,
                              new_value)  # Update the correct cell
            print(f"{field_to_update} updated successfully in Google Sheets.")
        except APIError as e:
            print(f"Error while updating Google Sheets: {e}")
            return

        # Synchronize the cached data to match the updated Google Sheet
        self.cached_tasks = [headers] + \
            tasks.get_all_values()[1:]  # Reload cached data

        print(
            f"Task '{task_to_update[0]}' {field_to_update} has been updated to '{new_value}'.")




    def delete_task(self):
        """
        Archive a task by moving it to the 'Deleted' tab in Google Sheets
        and removing it from the 'Tasks' tab and in-memory cache.
        """
        if not self.cached_tasks or len(self.cached_tasks) <= 1:  # Ensure there are tasks beyond headers
            print("No tasks available to delete.")
            return

        # Extract headers and task data
        headers = self.cached_tasks[0]  # Header row
        tasks_data = self.cached_tasks[1:]  # Task rows

        # Display tasks to help the user choose
        print("\n--- Delete (Archive) a Task ---")
        print("Available Tasks:")
        for task in tasks_data:
            try:
                print(f"ID: {task[0]}, Name: {task[1]}, Status: {task[4]}")
            except IndexError:
                print("Error: Task structure is incorrect.")
                return

        # Get Task ID from the user
        task_id = input(
            "Enter the ID of the task you want to delete: ").strip()

        # Find the task in cached data
        task_to_delete = next(
            (task for task in tasks_data if str(task[0]) == task_id), None)

        if not task_to_delete:
            print("Task ID not found. Please try again.")
            return

        # Ensure the "Deleted" tab exists in Google Sheets
        try:
            deleted_sheet = SHEET.worksheet("deleted")
        except gspread.exceptions.WorksheetNotFound:
            print("'Deleted' tab not found. Creating it now...")
            deleted_sheet = SHEET.add_worksheet(
                title="deleted", rows="100", cols="20")
            # Add headers to the "Deleted" tab
            deleted_sheet.append_row(["ID", "Name", "Deletion Date", "Deadline", "Complete Date", "Status",
                                      "Priority", "Category", "Project", "Notes"])

        # Flatten the task data
        flattened_task = [
            str(task_to_delete[0]),  # Task ID
            str(task_to_delete[1]),  # Task Name
            datetime.now().strftime("%Y-%m-%d"),  # Deletion Date
            str(task_to_delete[2] if len(task_to_delete)
                > 2 else ""),  # Deadline
            str(task_to_delete[3] if len(task_to_delete)
                > 3 else ""),  # Complete Date
            str(task_to_delete[4] if len(
                task_to_delete) > 4 else ""),  # Status
            str(task_to_delete[5] if len(task_to_delete)
                > 5 else ""),  # Priority
            str(task_to_delete[6] if len(task_to_delete)
                > 6 else ""),  # Category
            str(task_to_delete[7] if len(
                task_to_delete) > 7 else ""),  # Project
            str(task_to_delete[8] if len(task_to_delete) > 8 else ""),  # Notes
        ]

        # Add the task to the "Deleted" tab
        deleted_sheet.append_row(flattened_task)

        # Find the task row in the "Tasks" tab and delete it
        task_rows = tasks.get_all_values()  # Fetch all rows from the "Tasks" tab
        for i, row in enumerate(task_rows):
            if row[0] == str(task_to_delete[0]):  # Match the Task ID
                tasks.delete_rows(i + 1)  # Row index is 1-based
                print(
                    f"Task '{task_to_delete[1]}' has been removed from the 'Tasks' tab.")
                break

        # Remove the task from the cached tasks
        self.cached_tasks = [
            headers] + [task for task in tasks_data if str(task[0]) != task_id]

        print(
            f"Task '{task_to_delete[1]}' has been archived and moved to the 'Deleted' tab.")

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
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} \
                {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        # Print each task
        for task in filtered_tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")

    def view_tasks_by_priority(self):
        """
        Display tasks filtered by a specific priority in a table-like format.
        """
        if not self.tasks:
            print("No tasks available.")
            return

        # Ask the user to specify a priority
        print("\n --- View Tasks by Priority ---")
        print("\n Available priorities: High, Medium, Low")
        selected_priority = input(
            "Enter the priority to filter by: ").strip().capitalize()

        # Validate the user's input
        if selected_priority not in ["High", "Medium", "Low"]:
            print("Invalid priority. Please choose from High, Medium, or Low.")
            return

        # Filter tasks by the selected priority
        filtered_tasks = [
            task for task in self.tasks if task.priority == selected_priority]

        if not filtered_tasks:
            print(f"No tasks found with priority: {selected_priority}.")
            return

        # Define headers for the table
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]

        # Print the header row
        print(
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} \
                {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        # Print each filtered task
        for task in filtered_tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")

    def view_tasks_by_category(self):
        """
        Display tasks filtered by a specific category in a table-like format.
        """
        if not self.tasks:
            print("No tasks available.")
            return

        # Retrieve the list of categories dynamically from the Google Sheets
        print("\n--- View Tasks by Category ---")
        category_data = retry_with_backoff(self.categories_sheet.get_all_values)[
            1:]  # Skip the header row
        # Extract category names
        available_categories = [row[1] for row in category_data if row[1]]

        if not available_categories:
            print("No categories found in the Google Sheet.")
            return

        # Display the available categories
        print("Available Categories:")
        for category in available_categories:
            print(f"- {category}")

        # Ask the user to select a category
        selected_category = input(
            "\nEnter the category to filter by: ").strip()

        # Validate the selected category
        if selected_category not in available_categories:
            print("Invalid category. Please select a valid category from the list.")
            return

        # Filter tasks by the selected category (compare against task.category["name"])
        filtered_tasks = [
            task for task in self.tasks if task.category["name"] == selected_category]

        if not filtered_tasks:
            print(f"No tasks found in category: {selected_category}.")
            return

        # Define headers for the table
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]

        # Print the header row
        print(
            f"\n{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} {headers[3]:<12} \
                {headers[4]:<25} {headers[5]:<40}")
        print("-" * 130)

        # Print each filtered task
        for task in filtered_tasks:
            project_display = f"{task.project['name']}: " if task.project["name"] else ""
            print(f"{task.task_id:<5} {task.deadline:<12} {task.priority:<10} {task.status:<12} "
                  f"{project_display:<25} {task.name:<40}")

# Initialize the TaskManager
def main():
    """
    Entry point for the Task Manager application.
    """
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
        print("8 - View tasks by priority")
        print("9 - View tasks by category")
        print("10 - Exit")

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
            manager.view_tasks_by_priority()
        elif choice == "9":
            manager.view_tasks_by_category()
        elif choice == "10":
            print("Exiting Task Manager. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


# Ensure the script runs only when executed directly
if __name__ == "__main__":
    main()
