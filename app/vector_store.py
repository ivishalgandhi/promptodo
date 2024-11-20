import os
from typing import List, Dict, Any
import json
from datetime import datetime
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import joblib

class VectorStore:
    def __init__(self, persist_directory: str = "vector_db"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('wordnet')
        
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        self.tasks_file = os.path.join(persist_directory, 'tasks.json')
        self.projects_file = os.path.join(persist_directory, 'projects.json')
        self.vectors_file = os.path.join(persist_directory, 'vectors.joblib')
        self.vocab_file = os.path.join(persist_directory, 'vocab.joblib')
        
        # Load or initialize data
        self.tasks_data = self._load_json(self.tasks_file, [])
        self.projects_data = self._load_json(self.projects_file, [])
        self._load_vectors()

    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text by tokenizing, removing stopwords, and lemmatizing."""
        # Tokenize
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token.isalnum() and token not in self.stop_words
        ]
        
        return tokens

    def _text_to_vector(self, text: str) -> np.ndarray:
        """Convert text to a binary vector using vocabulary."""
        tokens = self._preprocess_text(text)
        vector = np.zeros(len(self.vocabulary))
        
        for token in tokens:
            if token in self.vocabulary:
                vector[self.vocabulary[token]] = 1
                
        return vector

    def _build_vocabulary(self, texts: List[str]) -> Dict[str, int]:
        """Build vocabulary from all texts."""
        vocab = set()
        for text in texts:
            tokens = self._preprocess_text(text)
            vocab.update(tokens)
        
        return {word: idx for idx, word in enumerate(sorted(vocab))}

    def _load_json(self, file_path: str, default: Any) -> Any:
        """Load JSON data from file or return default if file doesn't exist."""
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default

    def _save_json(self, file_path: str, data: Any) -> None:
        """Save data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _load_vectors(self) -> None:
        """Load or initialize vectors and vocabulary."""
        if os.path.exists(self.vectors_file) and os.path.exists(self.vocab_file):
            self.vectors = joblib.load(self.vectors_file)
            self.vocabulary = joblib.load(self.vocab_file)
        else:
            self.vectors = None
            self.vocabulary = {}

    def _save_vectors(self) -> None:
        """Save vectors and vocabulary."""
        if self.vectors is not None:
            joblib.dump(self.vectors, self.vectors_file)
            joblib.dump(self.vocabulary, self.vocab_file)

    def _compute_similarity(self, query_vector: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query vector and all vectors."""
        # Add small epsilon to avoid division by zero
        epsilon = 1e-8
        return np.dot(vectors, query_vector) / (
            np.maximum(
                np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector),
                epsilon
            )
        )

    def add_task(self, task_id: int, content: str, metadata: Dict[str, Any]) -> None:
        """Add a task to the vector store."""
        self.tasks_data.append({
            'id': task_id,
            'content': content,
            'metadata': metadata
        })
        self._save_json(self.tasks_file, self.tasks_data)
        self._update_vectors()

    def find_similar_tasks(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Find similar tasks using binary term vectors."""
        if not self.tasks_data:
            return []

        # Update vectors if needed
        if self.vectors is None:
            self._update_vectors()
            
        if not self.vocabulary:
            return []

        # Get query vector
        query_vector = self._text_to_vector(query)
        
        # Calculate similarities
        similarities = self._compute_similarity(query_vector, self.vectors)
        
        # Get top N similar tasks
        top_indices = np.argsort(similarities)[-n_results:][::-1]
        
        return [
            {
                'id': self.tasks_data[idx]['id'],
                'metadata': self.tasks_data[idx]['metadata'],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
            if similarities[idx] > 0
        ]

    def scan_git_project(self, repo_path: str) -> None:
        """Scan a Git repository for project context."""
        try:
            import git
            repo = git.Repo(repo_path)
            
            # Get recent commits
            commits = list(repo.iter_commits('HEAD', max_count=100))
            
            # Extract commit messages and files
            for commit in commits:
                context = {
                    'type': 'commit',
                    'message': commit.message,
                    'author': str(commit.author),
                    'date': datetime.fromtimestamp(commit.committed_date).isoformat(),
                    'files': [item.a_path for item in commit.diff(commit.parents[0])] if commit.parents else [],
                    'repo': repo_path
                }
                self.projects_data.append(context)
            
            self._save_json(self.projects_file, self.projects_data)
            self._update_vectors()

        except Exception as e:
            print(f"Error scanning repository: {str(e)}")

    def get_project_context(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Get relevant project context based on a query."""
        if not self.projects_data:
            return []

        # Get all project texts
        texts = [
            f"{item.get('message', '')} {' '.join(item.get('files', []))}"
            for item in self.projects_data
        ]
        
        # Build vocabulary and vectors for project texts
        project_vocabulary = self._build_vocabulary(texts)
        project_vectors = np.array([
            self._text_to_vector(text) for text in texts
        ])
        
        # Get query vector
        query_vector = self._text_to_vector(query)
        
        # Calculate similarities
        similarities = self._compute_similarity(query_vector, project_vectors)
        
        # Get top N similar contexts
        top_indices = np.argsort(similarities)[-n_results:][::-1]
        
        return [
            {
                'context': self.projects_data[idx],
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
            if similarities[idx] > 0
        ]

    def suggest_tags_from_context(self, content: str) -> List[str]:
        """Suggest tags based on project context and similar tasks."""
        tags = set()
        
        # Get tags from similar tasks
        similar_tasks = self.find_similar_tasks(content)
        for task in similar_tasks:
            if 'tags' in task['metadata']:
                tags.update(task['metadata']['tags'])
        
        # Get tags from project context
        project_context = self.get_project_context(content)
        for item in project_context:
            context = item['context']
            if isinstance(context, dict):
                # Extract potential tags from commit messages and files
                message = context.get('message', '').lower()
                files = context.get('files', [])
                
                # Add commit type tags
                for prefix in ['feature/', 'fix/', 'docs/', 'test/']:
                    if prefix in message:
                        tags.add(message.split(prefix)[1].split()[0])
                
                # Add file type tags
                for file in files:
                    ext = os.path.splitext(file)[1]
                    if ext:
                        tags.add(ext[1:])  # Remove the dot
        
        return list(tags)

    def _update_vectors(self) -> None:
        """Update vectors for all content."""
        if not self.tasks_data:
            return
            
        # Get all task contents
        contents = [task['content'] for task in self.tasks_data]
        
        # Build or update vocabulary
        self.vocabulary = self._build_vocabulary(contents)
        
        # Compute vectors for all tasks
        self.vectors = np.array([
            self._text_to_vector(content) for content in contents
        ])
        
        self._save_vectors()
