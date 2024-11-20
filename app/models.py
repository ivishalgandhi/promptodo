from datetime import datetime
from app import db

# Association tables for many-to-many relationships
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

task_assignments = db.Table('task_assignments',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    raw_input = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), nullable=True)
    
    # Project and milestone tracking
    project = db.Column(db.String(100), nullable=True)
    milestone = db.Column(db.String(100), nullable=True)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.relationship('Tag', secondary='task_tags', backref=db.backref('tasks', lazy='dynamic'))
    assigned_users = db.relationship('User', secondary='task_assignments', 
                                   backref=db.backref('assigned_tasks', lazy='dynamic'))

    def __repr__(self):
        return f'<Task {self.id}: {self.content[:30]}...>'

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'raw_input': self.raw_input,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'priority': self.priority,
            'project': self.project,
            'milestone': self.milestone,
            'tags': [tag.name for tag in self.tags]
        }

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'
