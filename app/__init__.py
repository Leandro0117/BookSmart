from flask import Flask
from config import Config  # 🆕 IMPORTAR CONFIG

def create_app():
    """
    Inicializa la aplicación Flask de BookSmart
    """
    app = Flask(__name__)
    app.config.from_object(Config)  # 🆕 USAR CONFIG EN LUGAR DE MANUAL
    
    # Registrar blueprints
    from app.routes import main_bp
    from app.auth.routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    return app