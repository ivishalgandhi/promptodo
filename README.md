# PromptoDo - Natural Language Task Manager

A modern Flask-based task management application that understands natural language input. PromptoDo uses AI to intelligently parse task descriptions, automatically extracting information like due dates, priorities, tags, and assignments.

## Features

- Natural language task input processing
- Automatic extraction of:
  - Due dates
  - Priority levels
  - Project associations
  - Milestones
  - Tags
  - User assignments (using @mentions)
- Modern Bootstrap UI
- Task filtering by status
- Configurable LLM providers (OpenAI, Anthropic, Groq)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure LLM provider:
Edit `config.toml` and add your API key for your chosen provider (Anthropic, OpenAI, or Groq).

3. Run the application:
```bash
python run.py
```

## Usage

1. Enter tasks in natural language:
```
Create a high priority presentation for the Q2 review meeting @john @sarah due next Friday #project-alpha
```

The application will automatically parse this into:
- Task: Create presentation for Q2 review
- Priority: High
- Due Date: Next Friday
- Assigned: John, Sarah
- Project: Alpha
- Tags: project-alpha

2. View and manage tasks:
- Filter tasks by status
- Edit task details
- Mark tasks as complete
- Track projects and milestones

## Configuration

The `config.toml` file allows you to:
- Choose your LLM provider (Anthropic, OpenAI, Groq)
- Configure API keys
- Set application secrets
- Configure database settings

## Development

The application is built with:
- Flask
- SQLAlchemy
- Bootstrap 5
- Various LLM APIs for natural language processing
