from app import create_app, db
from app.models import User, Task, Tag
from app.vector_store import VectorStore

def init_database():
    app = create_app()
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        # Create a test user
        test_user = User(
            username='test',
            email='test@example.com'
        )
        db.session.add(test_user)
        db.session.commit()
        
        print("Database initialized successfully!")
        print(f"Created test user with ID: {test_user.id}")

if __name__ == '__main__':
    init_database()
