# Task Manager Project

Welcome to the `Task Manager`, a Python command-line application designed to create, organize, and manage tasks effectively. This project interacts with Google Sheets to store and process data, making it both powerful and dynamic. The last update to this file was: `March 13, 2025.`

## Features

- Add Tasks: Easily create new tasks with validation for name, deadline, priority, category, and project.
- Review Deadlines: View upcoming tasks sorted by their deadlines.
- Task Listings: List tasks based on specific projects.
- Update Tasks: Modify task details like status, deadline, and more.
- Task Completion: Mark tasks as completed and optionally archive them in a dedicated tab.
- Delete (Archive) Tasks: Move unnecessary tasks to a "Deleted" tab without permanently erasing them.

## Reminders

- Code Placement: Your code should reside in the `run.py` file.
- Dependencies: Include all required dependencies in the `requirements.txt` file.
- Google Sheets API Setup: Configure the connection to Google Sheets by adding the necessary credentials in your environment variables.
- Data Validation: Built-in validation ensures accurate and clean data input.

## Deployment

To deploy the application to Heroku, follow these steps:

**1. Set Up Your Heroku Environment:**

- Create a new Heroku app.
- Go to the _Settings_ tab of your Heroku app.
- Add the following buildpacks in this order:
  - `heroku/python`
  - `heroku/nodejs`

**2. Set Config Vars:**

- Add a Config Var called `PORT` and set it to `8000`.
- If you use Google Sheets credentials, add another _Config Var_ called `CREDS` and paste the `JSON` credentials into the value field.

**3. Prepare Your Repository:**

- Ensure your code is properly committed to a _GitHub_ repository.
- Your main script file must be named run.py.
- Include a requirements.txt file listing all your dependencies.

**4. Connect Heroku to GitHub:**

- Under the Deploy tab in Heroku, connect your _GitHub_ repository.
- Select the branch you want to deploy (usually main).

**5. Deploy the Application:**

- Click on `Deploy Branch` in the _Heroku_ dashboard.
- Once deployed, your application can be accessed here.

**6. Test Your Application:**

- Make sure all features are functional in the deployed environment.
- Verify your integration with Google Sheets works as intended.

## Using the Task Manager

1. Launch the application in the terminal.
2. Choose from the intuitive menu options:
    1. Add a new task
    2. Review deadlines
    3. View tasks list
    4. Update a task
    5. Delete (archive) a task
    6. Mark a task as completed
    7. Exit the application

3. Follow the prompts to interact with the application features.

## Project Constraints

The command-line interface is set to 80 columns by 24 rows. Ensure all outputs stay within these constraints for better readability.

## Requirements

To run this project, you’ll need:

- Python 3.8 or higher
- Required libraries (install using `pip install -r requirements.txt`)
- Google Sheets credentials for API integration

## How It Works

This application uses the Google Sheets API to store and organize task data:

- Tasks Tab: Contains all active tasks.
- Completed Tab: Stores completed tasks.
- Deleted Tab: Archives deleted tasks for future reference.
- Projects & Categories Tabs: Used for validation when assigning projects and categories to tasks.

**Happy Coding!**

We hope this task manager helps simplify your workflow and improves productivity.
