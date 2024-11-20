import sys
import os
from app.vector_store import VectorStore
from app.markdown_scanner import MarkdownScanner

def scan_markdown_directories(directories):
    """Scan provided directories for markdown files and extract context."""
    vector_store = VectorStore()
    scanner = MarkdownScanner(vector_store)
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            continue
            
        print(f"Scanning markdown files in: {directory}")
        scanner.scan_markdown_directory(directory)
        print(f"Finished scanning: {directory}")
        
        # Print summary of found tasks
        tasks = vector_store.tasks_collection.get(
            where={"type": "markdown_task"}
        )
        
        if tasks and tasks['metadatas']:
            print("\nFound tasks:")
            for metadata in tasks['metadatas']:
                status = metadata.get('status', 'unknown')
                project = metadata.get('project', 'no project')
                file_path = metadata.get('file_path', '')
                print(f"- [{status}] {project} ({os.path.basename(file_path)})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_markdown.py /path/to/markdown/dir1 [/path/to/markdown/dir2 ...]")
        print("\nThis script will scan markdown files for:")
        print("- Tasks (- [ ] or - [x] format)")
        print("- Projects and milestones")
        print("- Tags (#tag format)")
        print("- @mentions")
        print("- Due dates (due: YYYY-MM-DD)")
        print("- Priorities (priority: high/medium/low)")
        sys.exit(1)
    
    scan_markdown_directories(sys.argv[1:])
