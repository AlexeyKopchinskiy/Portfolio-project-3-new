# Your code goes here.
# You can delete these comments, but do not change the name of this file
# Write your code to expect a terminal of 80 characters wide and 24 rows high

# --- CONFIGURATION ---
# Toggle between the OOP implementation and the old procedural code.
use_oop = True  # Set to False to run the old code.
if use_oop:
     # --- NEW OOP CODE START ---
    print("Running Task Manager in OOP mode...")
    
    # Add the new functionality here
else:
    print("Running Task Manager in procedural mode...")
    # Call old functions and retain the existing workflow

    # --- OLD CODE START ---
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

    # Helper function to prevent empty and too long task names
    def validate_task_name(task_name):
        if not task_name.strip():
            return "Task name cannot be empty."
        if len(task_name) > 50:
            return "Task name must be 50 characters or less."
        return None

    # Helper function to validate deadline
    def validate_deadline(deadline):
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
        except ValueError:
            try:
                deadline_date = datetime.strptime(deadline, "%d-%m-%Y")
            except ValueError:
                return "Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY."
        if deadline_date < datetime.now():
            return "Deadline cannot be in the past."
        return None

    # Helper function for validation of proirity 
    def validate_priority(priority):
        if priority not in ["High", "Medium", "Low"]:
            return "Priority must be 'High', 'Medium', or 'Low'."
        return None

    # Helper function for validation of category 
    def validate_category(category, valid_categories):
        if category not in valid_categories:
            return "Invalid category ID."
        return None

    # Helper function to check if the project is valid
    def validate_project(project, valid_projects):
        if project not in valid_projects:
            return "Invalid project ID."
        return None

    # Helper function to control notes length
    def validate_notes(notes):
        if len(notes) > 250:
            return "Notes exceeded 250 characters. It will be truncated."
        return None

    # Add task to the Google sheet
    def add_task():
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

        # Validate Task Name
        while True:
            task_name = input("Task Name: ").strip()
            error = validate_task_name(task_name)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Validate Deadline
        while True:
            deadline = input("Deadline (YYYY-MM-DD or DD-MM-YYYY): ").strip()
            error = validate_deadline(deadline)
            if error:
                print(f"Error: {error}")
            else:
                deadline = datetime.strptime(deadline, "%Y-%m-%d").strftime("%Y-%m-%d")
                break

        # Validate Priority
        while True:
            priority = input("Priority (High, Medium, Low): ").strip().capitalize()
            error = validate_priority(priority)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Validate Category
        valid_categories = [row[0] for row in categories_data]
        while True:
            category = input(f"Category (Choose ID from: {category_options}): ").strip()
            error = validate_category(category, valid_categories)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Validate Project
        valid_projects = [row[0] for row in projects_data]
        while True:
            project = input(f"Project (Choose ID from: {project_options}): ").strip()
            error = validate_project(project, valid_projects)
            if error:
                print(f"Error: {error}")
            else:
                break

        # Validate Notes (Optional)
        notes = input("Notes (Optional, max 250 characters): ").strip()
        error = validate_notes(notes)
        if error:
            print(f"Warning: {error}")
            notes = notes[:250]  # Trim to 250 characters if too long

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
        Update an existing task in the 'tasks' sheet with validation for inputs.
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

        # Ask the user for the task ID to update
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

        # Perform the update based on the user's choice
        if choice == "1":
            # Validate and update Task Name
            while True:
                new_task_name = input("Enter new task name: ").strip()
                error = validate_task_name(new_task_name)
                if error:
                    print(f"Error: {error}")
                else:
                    tasks.update_cell(task_row, 2, new_task_name)  # Column 2 is 'Task Name'
                    print("Task name updated successfully!")
                    break

        elif choice == "2":
            # Validate and update Status
            while True:
                new_status = input("Enter new status (Pending/In Progress/Completed): ").strip()
                if new_status not in ["Pending", "In Progress", "Completed"]:
                    print("Error: Status must be 'Pending', 'In Progress', or 'Completed'.")
                else:
                    tasks.update_cell(task_row, 6, new_status)  # Column 6 is 'Status'
                    print("Task status updated successfully!")
                    break

        elif choice == "3":
            # Validate and update Deadline
            while True:
                new_deadline = input("Enter new deadline (YYYY-MM-DD or DD-MM-YYYY): ").strip()
                error = validate_deadline(new_deadline)
                if error:
                    print(f"Error: {error}")
                else:
                    new_deadline = datetime.strptime(new_deadline, "%Y-%m-%d").strftime("%Y-%m-%d")
                    tasks.update_cell(task_row, 4, new_deadline)  # Column 4 is 'Deadline'
                    print("Task deadline updated successfully!")
                    break

        elif choice == "4":
            # Validate and update Priority
            while True:
                new_priority = input("Enter new priority (High/Medium/Low): ").strip().capitalize()
                error = validate_priority(new_priority)
                if error:
                    print(f"Error: {error}")
                else:
                    tasks.update_cell(task_row, 7, new_priority)  # Column 7 is 'Priority'
                    print("Task priority updated successfully!")
                    break

        elif choice == "5":
            # Validate and update Notes
            new_notes = input("Enter new notes: ").strip()
            error = validate_notes(new_notes)
            if error:
                print(f"Warning: {error}")
                new_notes = new_notes[:250]  # Trim to 250 characters if too long
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

        # Display the tasks for the selected project
        if filtered_tasks:
            print(f"\nTasks for Project ID {project_id}:")
            for task in filtered_tasks:
                print(f"- ID: {task[0]}, Name: {task[1]}, Deadline: {task[3]}, "
                    f"Status: {task[5]}, Priority: {task[6]}, Notes: {task[9]}")
        else:
            print(f"No tasks found for Project ID {project_id}.")

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
            print("7 - View tasks by project")
            print("8 - Exit")

            # Get the user's choice
            user_choice = input("Enter the number of your choice: ").strip()

            if user_choice == "1":
                add_task()
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
                view_tasks_by_project()
            elif user_choice == "8":
                print("Exiting the Task Manager. Have a great day!")
                break
            else:
                print("Invalid input. Please enter a number between 1 and 7.")


    # Entry point for the program
    main()

    # --- OLD CODE END ---
