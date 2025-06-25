from flask import Flask
from .config import Config
from .routes import register_routes
from flask_cors import CORS
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    register_routes(app)

    return app
