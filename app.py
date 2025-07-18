# Importa los módulos principales de Flask y extensiones
from flask import Flask, request, jsonify
from flask_login import LoginManager
from routes import register_routes
from models.user import User
from DB import get_connection

# ✅ Crea la instancia principal de la aplicación Flask
app = Flask(__name__)
app.secret_key = "clave_super_secreta"  # Clave para sesiones seguras

# ✅ Configuración de Flask-Login para manejo de usuarios
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"  # Redirige a login si no está autenticado

# ✅ Función para cargar el usuario desde la base de datos
@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        # Retorna una instancia de User si existe
        return User(user_data["id"], user_data["username"], user_data["password"], user_data["rol"])
    return None

# ✅ Registra todos los blueprints de rutas en la aplicación
register_routes(app)

# ✅ Ejecuta la aplicación en modo debug si se ejecuta directamente
if __name__ == "__main__":
    app.run(debug=True)
