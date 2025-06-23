from .files import bp as files_bp

def register_routes(app):
    app.register_blueprint(files_bp, url_prefix='/api')
