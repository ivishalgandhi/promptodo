import sys
import os
from app.nlp_processor import NLPProcessor

def scan_projects(directories):
    """Scan provided directories for project context."""
    nlp = NLPProcessor()
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Directory not found: {directory}")
            continue
            
        print(f"Scanning project: {directory}")
        nlp.scan_project(directory)
        print(f"Finished scanning: {directory}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_projects.py /path/to/project1 [/path/to/project2 ...]")
        sys.exit(1)
    
    scan_projects(sys.argv[1:])
