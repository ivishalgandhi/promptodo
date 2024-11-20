from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from app import db
from app.models import Task, User, Tag
from app.nlp_processor import NLPProcessor
from datetime import datetime

main = Blueprint('main', __name__)
nlp = NLPProcessor()

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/tasks')
def tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'tasks': [task.to_dict() for task in tasks]
        })
    return render_template('tasks.html', tasks=tasks)

@main.route('/process_task', methods=['POST'])
def process_task():
    if request.is_json:
        data = request.get_json()
        task_text = data.get('task_description')
    else:
        task_text = request.form.get('task_text')

    if not task_text:
        return jsonify({'success': False, 'error': 'No task text provided'}), 400

    try:
        # Process with NLP
        processed = nlp.process_task(task_text)
        
        # Create new task
        task = Task(
            content=task_text,
            raw_input=task_text,
            status='pending',
            user_id=1,  # Using the test user ID
            priority=processed.get('priority', 'medium'),
            project=processed.get('project'),
            due_date=processed.get('due_date')
        )
        
        # Add task to session first
        db.session.add(task)
        db.session.flush()  # Ensure task has an ID before adding tags
        
        # Handle tags
        if processed.get('tags'):
            for tag_name in processed['tags']:
                # Check if tag exists
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    # Create new tag
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    db.session.flush()  # Ensure tag has an ID
                task.tags.append(tag)
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'task': task.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error in process_task: {str(e)}")  # Add logging
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    try:
        # Update fields if they are present in the request
        if 'content' in data:
            task.content = data['content']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        if 'project' in data:
            task.project = data['project']
        if 'due_date' in data:
            task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
            
        db.session.commit()
        return jsonify({'success': True, 'task': task.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
