from flask import Flask
from .storage import init_db
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Initialize Database
    with app.app_context():
        init_db()

    # Register Blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
