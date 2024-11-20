import toml
from datetime import datetime
from dateutil import parser
import anthropic
import openai
from groq import Groq
from .vector_store import VectorStore
import json
import re

class NLPProcessor:
    def __init__(self):
        self.config = toml.load('config.toml')
        self.provider = self.config['llm']['provider']
        self._setup_client()
        self.vector_store = VectorStore()

    def _setup_client(self):
        if self.provider == 'anthropic':
            self.client = anthropic.Anthropic(
                api_key=self.config['anthropic']['api_key']
            )
            self.model = self.config['anthropic']['model']
        elif self.provider == 'openai':
            self.client = openai.OpenAI(
                api_key=self.config['openai']['api_key'],
                base_url=self.config['openai']['base_url']
            )
            self.model = self.config['openai']['model']
        elif self.provider == 'groq':
            self.client = Groq(
                api_key=self.config['groq']['api_key'],
                base_url=self.config['groq']['base_url']
            )
            self.model = self.config['groq']['model']

    def process_task(self, text):
        """Process natural language task input and extract structured information."""
        # Get similar tasks and project context
        similar_tasks = self.vector_store.find_similar_tasks(text)
        suggested_tags = self.vector_store.suggest_tags_from_context(text)
        
        # Create context-aware prompt
        context = ""
        if similar_tasks:
            context += "\nSimilar tasks in the system:"
            for task in similar_tasks[:3]:
                context += f"\n- {task['metadata'].get('content', '')}"
        
        if suggested_tags:
            context += f"\nSuggested tags based on project context: {', '.join(suggested_tags)}"

        prompt = f"""
        Analyze the following task description and extract key information.
        Use the provided context to make better inferences about projects and tags.

        Task: {text}
        {context}
        
        Please extract and format the following information in JSON:
        - task_content: The main task description
        - due_date: Any mentioned due date
        - project: Project name if mentioned (infer from keywords like 'for project X', 'in X project', '#project-X', or similar patterns). If no project is explicitly mentioned, try to infer it from the task context.
        - milestone: Any milestone information
        - priority: High/Medium/Low if mentioned
        - status: Current status if mentioned (default to 'pending')
        - tags: List of relevant tags (combine mentioned tags and suggested tags)
        - assigned_users: List of @mentioned users
        
        Format dates in ISO format (YYYY-MM-DD).
        
        Respond ONLY with the JSON object, no additional text.
        """

        try:
            result = None
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    system="You are a task management assistant that extracts structured information from natural language task descriptions. Always respond with valid JSON.",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                result = response.content[0].text
            elif self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                result = response.choices[0].message.content
            elif self.provider == 'groq':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                result = response.choices[0].message.content

            # Parse the result
            try:
                if not result:
                    raise ValueError("No response from LLM provider")

                # Process the result and convert dates
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    # Try to extract JSON from the response if it contains additional text
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                    else:
                        raise ValueError("Could not parse JSON from response")

                # Set default project to "Inbox" if not specified or empty
                if not parsed.get('project'):
                    parsed['project'] = 'Inbox'

                # Parse the due date if present
                if parsed.get('due_date'):
                    parsed['due_date'] = parser.parse(parsed['due_date'])

                return parsed

            except Exception as e:
                print(f"Error processing task: {str(e)}")
                return None

        except Exception as e:
            print(f"Error processing task: {str(e)}")
            return None

    def validate_task(self, processed_task):
        """Validate the processed task and ensure all required fields are present."""
        required_fields = ['task_content']
        return all(field in processed_task for field in required_fields)

    def scan_project(self, repo_path):
        """Scan a project repository to build context."""
        self.vector_store.scan_git_project(repo_path)
