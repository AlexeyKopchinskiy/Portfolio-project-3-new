"""
This module is the sole component of the Task Manager application, handling all functionality 
within a single file using Object-Oriented Programming (OOP). It integrates task, category, 
and project management features while maintaining clear and modular design principles.

Features:
- Fully self-contained application for managing tasks, categories, and projects.
- Encapsulates all logic within a single module using classes and methods.
- Loads, updates, and manages tasks with data persistence through Google Sheets.
- Provides a user interface for efficient task management operations.

Modules and Dependencies:
- Google Sheets API: Used to connect to and interact with task, category, and project data.
- datetime: Facilitates deadline validation and date-related functionality.

Classes and Functions:
- TaskManager: Central class that encapsulates all task management logic.
- Task: Represents individual tasks and their attributes (e.g., name, deadline, priority).
- load_tasks(), add_task(), update_task(): Key methods for handling task operations.
"""

from datetime import datetime
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError
import gspread

# Import colorama for console colorization
import colorama
from colorama import Fore, Back, Style, init
init(convert=True)

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
            self.cached_tasks = self.tasks_sheet.get_all_values()

            # Fetch and cache project data
            self.cached_projects = self.projects_sheet.get_all_values()

            # Fetch and cache category data
            self.cached_categories = self.categories_sheet.get_all_values()

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
        """
        if not name or len(name) > 50:
            return "Task name must be non-empty and 50 characters or less."
        return None

    def validate_deadline(self, deadline):
        """
        Validates the task deadline to ensure it is in the correct date format (YYYY-MM-DD)
        and not set in the past.
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
        """
        valid_priorities = ["High", "Medium", "Low"]
        if priority not in valid_priorities:
            return "Invalid priority. Please choose from High, Medium, or Low."
        return None

    def validate_category_id(self, category_id):
        """
        Validates the category ID to ensure it exists within the valid categories
        retrieved from the categories sheet.
        """
        category_ids = [row[0] for row in self.categories_sheet.get_all_values()[
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
        """

        # Fetch valid project IDs and category IDs
        project_ids = [row[0] for row in self.projects_sheet.get_all_values()[
            1:]]  # Skip header row
        category_ids = [row[0] for row in self.categories_sheet.get_all_values()[
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
        """
        # Use cached project data
        project_dict = {row[0]: row[1]
                        for row in self.cached_projects[1:]}  # Skip header
        return project_dict.get(project_id, "none")

    def get_category_name(self, category_id):
        """
        Fetches the category name corresponding to a given category ID from cached data.
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
        category_data = self.categories_sheet.get_all_values()[
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
        project_date = self.projects_sheet.get_all_values()[
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

    def view_tasks(self, sort_by="priority"):
        """
        Display tasks in a table-like format with sorting options.
        Default sorting is by priority.
        Args:
            sort_by (str): The attribute to sort the tasks by. Options: \
                "priority", "deadline", "status", etc.
        """
        if not self.tasks:
            print("No tasks found.")
            return

        # Filter out tasks with the status 'Deleted'
        visible_tasks = [
            task for task in self.tasks if task.status.lower() != "deleted"]

        if not visible_tasks:
            print("No tasks available to display (all are marked as 'Deleted').")
            return

        # Determine the sorting key
        if sort_by == "priority":
            priority_order = {"High": 1, "Medium": 2, "Low": 3, "": 4}
            sorted_tasks = sorted(
                visible_tasks, key=lambda task: priority_order.get(
                    task.priority, 5)
            )
        elif sort_by == "deadline":
            sorted_tasks = sorted(
                visible_tasks, key=lambda task: task.deadline or "")
        elif sort_by == "status":
            sorted_tasks = sorted(
                visible_tasks, key=lambda task: task.status.lower())
        elif sort_by == "project":
            sorted_tasks = sorted(visible_tasks, key=lambda task: task.project["name"].lower(
            ) if task.project["name"] else "")
        elif sort_by == "name":
            sorted_tasks = sorted(
                visible_tasks, key=lambda task: task.name.lower())
        else:
            print(
                f"Invalid sort option: '{sort_by}'. Displaying tasks without sorting.")
            sorted_tasks = visible_tasks

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

        # Print each task as a row in the table
        for task in sorted_tasks:
            # Ensure each value fits within the column widths
            task_id_display = f"{task.task_id:<{column_widths['ID']}}"
            deadline_display = f"{task.deadline:<{column_widths['Deadline']}}"
            status_display = f"{task.status:<{column_widths['Status']}}"
            project_display = (
                f"{task.project['name']}"[
                    :column_widths["Project"] - 3] + "..."
                if len(task.project["name"]) > column_widths["Project"] else task.project["name"]
            )
            project_display = f"{project_display:<{column_widths['Project']}}"
            name_display = (
                f"{task.name}"[:column_widths["Name"] - 3] + "..."
                if len(task.name) > column_widths["Name"] else task.name
            )
            name_display = f"{name_display:<{column_widths['Name']}}"

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
                priority_display = f"{task.priority:<{column_widths['Priority']}}"

            # Print the formatted row
            print(
                f"{task_id_display} {deadline_display} {priority_display} {status_display} {project_display} {name_display}"
            )

    def review_deadlines(self):
        """
        Display all tasks with their deadlines in a table-like format,
        respecting a fixed CONSOLE_WIDTH of 80 characters, excluding tasks marked as 'Deleted'.
        """
        if not self.tasks:
            print("No tasks available.")
            return

        # Filter out tasks with the status 'Deleted'
        visible_tasks = [
            task for task in self.tasks if task.status.lower() != "deleted"]

        if not visible_tasks:
            print("No tasks available to display (all are marked as 'Deleted').")
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
        sorted_tasks = sorted(
            visible_tasks, key=lambda task: task.deadline or "")

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
                f"{task.task_id:<{column_widths['ID']}} \
                    {name_display:<{column_widths['Name']}} "
                f"{task.deadline:<{column_widths['Deadline']}} \
                    {priority_display:<{column_widths['Priority']}} "
                f"{task.status:<{column_widths['Status']}}"
            )


    def update_task(self):
        """
        Update an existing task by modifying its attributes.
        Changes are saved to both the in-memory list and Google Sheets.
        """
        if not self.tasks:
            print("No tasks available to update.")
            return

        # Display tasks in a formatted table-like format (like Option 3)
        print("\n--- Update a Task ---")
        headers = ["ID", "Deadline", "Priority", "Status", "Project", "Name"]
        print(
            f"{headers[0]:<5} {headers[1]:<12} {headers[2]:<10} \
                {headers[3]:<12} {headers[4]:<25} {headers[5]:<40}")
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
        print("\n What would you like to update?")
        print("1 - Task Name")
        print("2 - Deadline")
        print("3 - Priority")
        print("4 - Notes")
        print("5 - Status")
        print("6 - Category")
        print("7 - Project")

        # Main update loop
        while True:
            loaded_choice = input("Enter the number of your choice: ").strip()

            if loaded_choice == "1":  # Update Task Name
                while True:
                    print(
                        "Enter the new task name or type 'cancel' to go back to the task list.")
                    new_name = input("New task name: ").strip()

                    if new_name.lower() == "cancel":  # Check for cancellation
                        print(
                            "Task name update canceled. Returning to the task list...")
                        return  # Exit this operation and go back to the main task list

                    error = self.validate_task_name(
                        new_name)  # Validate task name
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
                    print(
                        "Enter the new notes or type 'cancel' to go back to the task list.")
                    new_notes = input("New notes: ").strip()

                    if new_notes.lower() == "cancel":  # Check for cancellation
                        print("Notes update canceled. Returning to the task list...")
                        return  # Exit the notes update operation and return to the main task list

                    # Check for maximum length
                    if len(new_notes) > 250:
                        print(
                            "Warning: Notes exceeded 250 characters and will be truncated.")
                        new_notes = new_notes[:250]

                    # Update the task and the sheet
                    task.notes = new_notes
                    self.tasks_sheet.update_cell(
                        int(task.task_id) + 1, 10, new_notes)
                    print("Task notes updated successfully!")
                    break

            elif loaded_choice == "5":  # Update Status
                while True:
                    new_status = input(
                        "Enter the new status (Pending, In Progress, \
                            Completed): ").strip()
                    if new_status not in ["Pending", "In Progress", "Completed"]:
                        print(
                            "Invalid status. Please choose from Pending, \
                                In Progress, or Completed.")
                    else:
                        task.status = new_status
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 6, new_status)
                        print("Task status updated successfully!")
                        break

            elif loaded_choice == "6":  # Update Category
                # Display available categories
                print("Available categories:")
                category_data = self.categories_sheet.get_all_values()[
                    1:]  # Skip header row
                for row in category_data:
                    print(f"ID: {row[0]}, Name: {row[1]}")

                # Prompt the user to select a new category
                while True:
                    new_category_id = input(
                        "Enter the new category ID: ").strip()
                    error = self.validate_category_id(new_category_id)
                    if error:
                        print(f"Error: {error}")
                    else:
                        new_category_name = self.get_category_name(
                            new_category_id)
                        task.category = {"id": new_category_id,
                                         "name": new_category_name}
                        # Update category in Google Sheet
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 8, new_category_id)
                        print("Task category updated successfully!")
                        break

            elif loaded_choice == "7":  # Update Project
                # Display available projects
                print("Available projects:")
                project_data = self.projects_sheet.get_all_values()[
                    1:]  # Skip header row
                for row in project_data:
                    print(f"ID: {row[0]}, Name: {row[1]}")

                # Prompt the user to select a new project
                while True:
                    new_project_id = input(
                        "Enter the new project ID: ").strip()
                    error = self.validate_project_id(new_project_id)
                    if error:
                        print(f"Error: {error}")
                    else:
                        new_project_name = self.get_project_name(
                            new_project_id)
                        task.project = {"id": new_project_id,
                                        "name": new_project_name}
                        # Update project in Google Sheet
                        self.tasks_sheet.update_cell(
                            int(task.task_id) + 1, 9, new_project_id)
                        print("Task project updated successfully!")
                        break

            else:
                print("Invalid choice. Please choose a valid option.")
                continue  # Prompt user again for a valid choice

            # Exit the update loop after successful editing
            break

    def delete_task(self):
        """
        Update the status of a task to 'Deleted' in both the cached data
        and Google Sheets without removing it or moving it to another tab.
        """
        # Ensure there are tasks beyond headers
        if not self.cached_tasks or len(self.cached_tasks) <= 1:
            print("No tasks available to update to 'Deleted' status.")
            return

        # Extract headers and task data
        headers = self.cached_tasks[0]  # Header row
        tasks_data = self.cached_tasks[1:]  # Task rows

        # Filter out 'Completed' tasks
        visible_tasks = [task for task in tasks_data if task[5].lower() != "deleted"]

        # Display tasks to help the user choose
        print("\n--- Mark a Task as Deleted ---")
        print("Available Tasks:")
        for task in visible_tasks:
            try:
                print(f"ID: {task[0]}, Name: {task[1]}, Status: {task[5]}")
            except IndexError:
                print("Error: Task structure is incorrect.")
                return

        # Get Task ID or cancel option from the user
        while True:
            task_id = input(
                "Enter the ID of the task you want to mark as 'Deleted', \
                    or type 'cancel' or 'x' to return to the main menu: ").strip()

            if task_id.lower() == "cancel" or task_id.lower() == "x":  # Check for cancel input
                print("Task deletion canceled. Returning to the main menu...")
                return  # Exit the delete task method
            # elif task_id.lower() == "x":


            # Find the task in cached data
            task_to_update = next(
                (task for task in tasks_data if str(task[0]) == task_id), None)

            if not task_to_update:
                print("Task ID not found. Please try again.")
            else:
                break  # Exit the input loop if the task is found

        # Update the status of the task in the cached data
        try:
            # Find the column index for the "Status" field
            col_index = headers.index("status")
            # Update the cached task's status
            task_to_update[col_index] = "Deleted"
        except ValueError:
            print("Error: 'Status' column not found in headers.")
            return

        try:
            # Update the status in cached data
            status_col_index = self.cached_tasks[0].index("status")  # Find "status" column
            task_to_update[status_col_index] = "Deleted"

            # Update Google Sheets
            row_index = self.cached_tasks.index(task_to_update)
            self.tasks_sheet.update_cell(row_index + 1, status_col_index + 1, "Deleted")

            # Refresh cached data and in-memory tasks
            self.load_and_cache_data()  # Refresh cached data
            self.tasks = self.load_tasks()  # Refresh in-memory tasks

            print(f"Task '{task_to_update[1]}' has been marked as 'Deleted'.")
        except Exception as e:
            print(f"Error while updating Google Sheets: {e}")

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
        print("9 - Exit")

        choice = input("Enter your choice: ").strip()
        if choice == "1":
            manager.create_task_from_input()
        elif choice == "2":
            manager.view_tasks(sort_by="deadline")
        elif choice == "3":
            manager.view_tasks()
        elif choice == "4":
            manager.update_task()
        elif choice == "5":
            manager.delete_task()
        elif choice == "6":
            manager.mark_task_completed()
        elif choice == "7":
            manager.view_tasks(sort_by="project")
        elif choice == "8":
            manager.view_tasks(sort_by="priority")
        elif choice == "9":
            print("Exiting Task Manager. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


# Ensure the script runs only when executed directly
if __name__ == "__main__":
    main()
