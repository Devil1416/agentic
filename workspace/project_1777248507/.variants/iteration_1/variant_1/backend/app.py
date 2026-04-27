import os
import sys
sys.path.append(os.path.abspath('../config/settings.py'))
from config.settings import Config
# rest of the code...
from config.settings import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from settings module
db = SQLAlchemy(app)  # Initialize SQLAlchemy
api_bp = Blueprint('api', __name__)  # Initialize blueprint for API endpoints
api = Api(api_bp)  # Initialize Flask-RESTful API

# Import models and routes after initializing db to avoid circular imports
from backend.db.models import Todo  
from backend.api.routes import api as todo_api

app.register_blueprint(api_bp)  # Register blueprint for API endpoints

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    db.create_all()  # Create tables in database if they don't exist
    app.run(debug=True)