from .home_routes import home_bp

try:
    from .auth_routes import auth_bp  # Importa el blueprint de autenticación
except ImportError as e:
    print(f"Error importando auth_bp: {e}")
    auth_bp = None

from .admin_routes import admin_bp
from .user_routes import usuario_bp  # Corrige el nombre del blueprint
from .historial_routes import historial_bp  # Nuevo blueprint de historial

def register_routes(app):
    app.register_blueprint(home_bp)
    if auth_bp:
        app.register_blueprint(auth_bp)
    else:
        print("auth_bp no está disponible, solo se registra home_bp")
    app.register_blueprint(admin_bp)
    app.register_blueprint(usuario_bp)  # Corrige el nombre del blueprint
    app.register_blueprint(historial_bp)  # Registrar historial blueprint