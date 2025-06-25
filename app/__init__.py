from flask import Flask
from .config import Config
from .routes import register_routes
from flask_cors import CORS
from flasgger import Swagger

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
        # Agrega Swagger
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "E. coli Genomic API",
            "description": "API para subir, comparar y analizar archivos genómicos de E. coli.",
            "version": "1.0.0"
        },
        "basePath": "/api",  # Esto depende de cómo registres tus rutas
        "schemes": ["http", "https"]
    })
    register_routes(app)

    return app
