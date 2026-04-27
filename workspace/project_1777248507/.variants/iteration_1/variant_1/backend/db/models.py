import os
import sys
sys.path.append(os.path.abspath('../../backend/config/settings.py'))
from backend.db.models import Todo
# rest of the code...
    """Todo model."""

    __tablename__ = 'todos'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)