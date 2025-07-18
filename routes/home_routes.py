from flask import Blueprint, render_template, jsonify
from DB import get_connection

home_bp = Blueprint("home", __name__)

@home_bp.route("/")
def index():
    return render_template("index.html")

@home_bp.route("/test-db")
def test_db():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ciudades")
        count = cursor.fetchone()[0]
        conn.close()
        return jsonify({"conexion": "exitosa", "ciudades_en_bd": count})
    else:
        return jsonify({"conexion": "fallida"})
