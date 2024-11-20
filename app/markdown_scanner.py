import os
from typing import List, Dict, Any
import re
from datetime import datetime
import frontmatter

class MarkdownScanner:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        # Patterns for extracting information from markdown
        self.patterns = {
            'task': r'[-*] \[([ x])\] (.*)',  # Matches - [ ] or - [x]
            'header': r'^#+\s+(.+)$',          # Matches markdown headers
            'tag': r'#(\w+)',                  # Matches hashtags
            'mention': r'@(\w+)',              # Matches @mentions
            'due_date': r'due:?\s*(\d{4}-\d{2}-\d{2}|today|tomorrow|\d{1,2}/\d{1,2}/\d{4})',
            'priority': r'priority:?\s*(high|medium|low)',
            'project': r'project:?\s*([^\s,]+)',
            'milestone': r'milestone:?\s*([^\s,]+)'
        }

    def scan_markdown_directory(self, directory_path: str) -> None:
        """Scan a directory of markdown files and extract context."""
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(('.md', '.markdown')):
                    file_path = os.path.join(root, file)
                    try:
                        self._process_markdown_file(file_path)
                    except Exception as e:
                        print(f"Error processing {file_path}: {str(e)}")

    def _process_markdown_file(self, file_path: str) -> None:
        """Process a single markdown file."""
        try:
            # Parse frontmatter and content
            with open(file_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                
            metadata = post.metadata
            content = post.content

            # Extract file context
            context = {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                'frontmatter': metadata,
                'headers': self._extract_headers(content),
                'tasks': self._extract_tasks(content),
                'tags': self._extract_tags(content),
                'mentions': self._extract_mentions(content)
            }

            # Store in vector database with different sections
            self._store_markdown_context(context)

        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")

    def _extract_headers(self, content: str) -> List[str]:
        """Extract markdown headers."""
        headers = []
        for line in content.split('\n'):
            match = re.match(self.patterns['header'], line)
            if match:
                headers.append(match.group(1))
        return headers

    def _extract_tasks(self, content: str) -> List[Dict[str, Any]]:
        """Extract tasks and their metadata from markdown content."""
        tasks = []
        current_section = None

        for line in content.split('\n'):
            # Track current section
            header_match = re.match(self.patterns['header'], line)
            if header_match:
                current_section = header_match.group(1)
                continue

            # Extract tasks
            task_match = re.match(self.patterns['task'], line)
            if task_match:
                status = 'completed' if task_match.group(1) == 'x' else 'pending'
                task_content = task_match.group(2)
                
                task = {
                    'content': task_content,
                    'status': status,
                    'section': current_section,
                    'due_date': self._extract_pattern(task_content, 'due_date'),
                    'priority': self._extract_pattern(task_content, 'priority'),
                    'project': self._extract_pattern(task_content, 'project'),
                    'milestone': self._extract_pattern(task_content, 'milestone'),
                    'tags': self._extract_tags(task_content),
                    'mentions': self._extract_mentions(task_content)
                }
                tasks.append(task)

        return tasks

    def _extract_tags(self, content: str) -> List[str]:
        """Extract hashtags from content."""
        return re.findall(self.patterns['tag'], content)

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content."""
        return re.findall(self.patterns['mention'], content)

    def _extract_pattern(self, content: str, pattern_key: str) -> str:
        """Extract a pattern from content."""
        match = re.search(self.patterns[pattern_key], content, re.IGNORECASE)
        return match.group(1) if match else None

    def _store_markdown_context(self, context: Dict[str, Any]) -> None:
        """Store markdown context in vector database."""
        # Store file-level context
        file_content = f"""
        File: {context['filename']}
        Headers: {' > '.join(context['headers'])}
        Tags: {', '.join(context['tags'])}
        Last Modified: {context['last_modified']}
        """
        
        self.vector_store.projects_collection.add(
            documents=[file_content],
            metadatas=[{
                'type': 'markdown_file',
                'path': context['file_path'],
                'tags': context['tags'],
                'headers': context['headers']
            }],
            ids=[f"md_{os.path.basename(context['file_path'])}"]
        )

        # Store each task as a separate vector
        for i, task in enumerate(context['tasks']):
            task_id = f"md_task_{os.path.basename(context['file_path'])}_{i}"
            self.vector_store.tasks_collection.add(
                documents=[task['content']],
                metadatas=[{
                    'type': 'markdown_task',
                    'file_path': context['file_path'],
                    'section': task['section'],
                    'status': task['status'],
                    'due_date': task['due_date'],
                    'priority': task['priority'],
                    'project': task['project'],
                    'milestone': task['milestone'],
                    'tags': task['tags'],
                    'mentions': task['mentions']
                }],
                ids=[task_id]
            )
