# Your code goes here.
# You can delete these comments, but do not change the name of this file
# Write your code to expect a terminal of 80 characters wide and 24 rows high

from datetime import datetime

# import os
# import json
import gspread
from google.oauth2.service_account import Credentials

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

# Add the new functionality here


class Task:
    """
    Represents an individual task with related attributes and methods.
    """

    def __init__(self, task_id, name, deadline, priority, status="Pending", notes="", category=None, project=None):
        self.task_id = task_id
        self.name = name
        self.deadline = deadline
        self.priority = priority
        self.status = status
        self.notes = notes
        self.category = category
        self.project = project
        self.complete_date = None

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
        if not name or len(name) > 50:
            return "Task name must be non-empty and 50 characters or less."
        return None

    def validate_deadline(self, deadline):
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            if deadline_date < datetime.now():
                return "Deadline cannot be in the past."
        except ValueError:
            return "Invalid deadline format. Please use YYYY-MM-DD."
        return None

    def validate_priority(self, priority):
        valid_priorities = ["High", "Medium", "Low"]
        if priority not in valid_priorities:
            return "Invalid priority. Please choose from High, Medium, or Low."
        return None

    def validate_category_id(self, category_id):
        category_ids = [row[0] for row in self.categories_sheet.get_all_values()[
            1:]]  # Skip header
        if category_id not in category_ids:
            return "Invalid category ID. Please choose from the available categories."
        return None

    def validate_project_id(self, project_id, name=None, deadline=None, priority=None, category_id=None):
        """
        Validates various aspects of a task, including project ID, task name, deadline, priority, 
        and category ID.

        Args:
            project_id (str): The project ID to validate.
            name (str, optional): The name of the task to validate. Defaults to None.
            deadline (str, optional): The deadline for the task in the format YYYY-MM-DD. Defaults to None.
            priority (str, optional): The priority level of the task ('High', 'Medium', 'Low'). Defaults to None.
            category_id (str, optional): The category ID to validate. Defaults to None.

        Returns:
            str: An error message if any validation fails, or None if all validations succeed.
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


    def load_tasks(self):
        """
        Load tasks from the Google Sheets into Task objects.
        
        Returns:
            list: A list of Task objects populated with data from the Google Sheets.
        """
        task_data = self.tasks_sheet.get_all_values()[1:]  # Skip header row
        loaded_tasks = []  # Renamed the local variable to avoid conflict with outer 'tasks'

        for row in task_data:
            loaded_tasks.append(Task(
                task_id=row[0],
                name=row[1],
                deadline=row[3],
                priority=row[6],
                status=row[5],
                notes=row[9],
                category=row[7],
                project=row[8]
            ))

        return loaded_tasks


    def add_task(self, name, deadline, priority, category, project, notes=""):
        """
        Create a new Task object, add it to the list of tasks,
        and save it to the Google Sheet.
        """
        # Generate a unique task ID (use length of tasks list + 1 for simplicity)
        task_id = len(self.tasks) + 1

        # Create a new Task object
        new_task = Task(
            task_id=task_id,
            name=name,
            deadline=deadline,
            priority=priority,
            category=category,
            project=project,
            notes=notes
        )

        # Add the task to the in-memory list
        self.tasks.append(new_task)

        # Save the task data to the Google Sheet
        self.tasks_sheet.append_row([
            task_id,                    # Task ID
            name,                       # Task Name
            datetime.now().strftime("%Y-%m-%d"),  # Creation Date
            deadline,                   # Deadline
            "",                         # Complete Date (default empty)
            "Pending",                  # Status (default: Pending)
            priority,                   # Priority
            category,                   # Category ID
            project,                    # Project ID
            notes                       # Notes
        ])
        print(
            f"Task '{name}' added successfully with ID {task_id} and saved to the Google Sheet.")

    def create_task_from_input(self):
        """
        Collect task details interactively from the user with real-time validation.
        """
        print("\n--- Create a New Task ---")

        # Task Name
        while True:
            name = input("Enter task name: ").strip()
            error = self.validate_task_name(name)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Deadline
        while True:
            deadline = input("Enter deadline (YYYY-MM-DD): ").strip()
            error = self.validate_deadline(deadline)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Priority
        while True:
            priority = input(
                "Enter priority (High, Medium, Low): ").strip().capitalize()
            error = self.validate_priority(priority)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Category
        category_ids = [row[0] for row in self.categories_sheet.get_all_values()[
            1:]]  # Skip header row
        print(f"Available Categories: {', '.join(category_ids)}")
        while True:
            category_id = input("Enter category ID: ").strip()
            error = self.validate_category_id(category_id)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Project
        project_ids = [row[0] for row in self.projects_sheet.get_all_values()[
            1:]]  # Skip header row
        print(f"Available Projects: {', '.join(project_ids)}")
        while True:
            project_id = input("Enter project ID: ").strip()
            error = self.validate_project_id(project_id)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Notes (Optional)
        notes = input("Enter notes (optional): ").strip()
        if len(notes) > 250:
            print("Warning: Notes exceeded 250 characters. It will be truncated.")
            notes = notes[:250]

        # Add the task after all inputs are validated
        self.add_task(name, deadline, priority,
                      category_id, project_id, notes)
        print(f"Task '{name}' added successfully!")

    def view_tasks(self):
        """
        Display all tasks with details.
        """
        if not self.tasks:
            print("No tasks found.")
        else:
            print("\nTasks List:")
            for task in self.tasks:
                print(task)

    def review_deadlines(self):
        """
        Display tasks sorted by their deadlines.
        """
        if not self.tasks:
            print("No tasks found.")
            return

        # Sort tasks by deadline (convert to datetime for proper sorting)
        sorted_tasks = sorted(
            self.tasks,
            key=lambda task: datetime.strptime(task.deadline, "%Y-%m-%d")
        )

        # Display the sorted tasks
        print("\n--- Tasks Sorted by Deadline ---")
        for task in sorted_tasks:
            print(f"ID: {task.task_id}, Name: {task.name}, Deadline: {task.deadline}, "
                  f"Priority: {task.priority}, Status: {task.status}")

    def update_task(self):
        """
        Update an existing task by modifying its attributes, with a retry mechanism
        for invalid inputs. Changes are saved to both the in-memory list and Google Sheets.
        """
        if not self.tasks:
            print("No tasks available to update.")
            return

        # Display tasks to help the user choose
        print("\n--- Update a Task ---")
        print("Available Tasks:")
        for task in self.tasks:
            print(
                f"ID: {task.task_id}, Name: {task.name}, Deadline: {task.deadline}, Priority: {task.priority}, Status: {task.status}")

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
        task_rows = self.tasks_sheet.get_all_values()
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
        Display tasks filtered by a specific project ID.
        """
        if not self.tasks:
            print("No tasks available to view.")
            return

        # Display available projects
        print("\n--- View Tasks by Project ---")
        print("Available Projects:")
        project_ids = [row[0] for row in self.projects_sheet.get_all_values()[
            1:]]  # Skip header
        for row in self.projects_sheet.get_all_values()[1:]:  # Skip header
            print(f"ID: {row[0]}, Name: {row[1]}")

        # Get the project ID from the user
        project_id = input(
            "Enter the Project ID to view tasks for: ").strip()
        if project_id not in project_ids:
            print("Invalid Project ID. Please try again.")
            return

        # Filter tasks by project ID
        filtered_tasks = [
            task for task in self.tasks if task.project == project_id]

        if not filtered_tasks:
            print(f"No tasks found for Project ID {project_id}.")
        else:
            print(f"\n--- Tasks for Project ID {project_id} ---")
            for task in filtered_tasks:
                print(f"ID: {task.task_id}, Name: {task.name}, Deadline: {task.deadline}, "
                      f"Status: {task.status}, Priority: {task.priority}, Notes: {task.notes}")


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
