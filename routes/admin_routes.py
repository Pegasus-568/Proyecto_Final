from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from functools import wraps
from DB import get_connection
from decimal import Decimal
import json

admin_bp = Blueprint("admin", __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            return redirect(url_for('home.index'))
        return f(*args, **kwargs)
    return decorated_function

def safe_float(value):
    """Convierte cualquier valor numérico a float de manera segura"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)

@admin_bp.route("/admin")
@login_required
@admin_required
def panel_admin():
    return render_template("admin.html")

# ==================== RUTAS PARA PROVINCIAS ====================

@admin_bp.route("/provincias")
@login_required
@admin_required
def provincias():
    return render_template("admin/provincias.html")

@admin_bp.route("/api/admin/provincias")
@login_required
@admin_required
def api_provincias():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM provincias ORDER BY nombre")
        provincias = cursor.fetchall()
        conn.close()
        return jsonify(provincias)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/provincias", methods=["POST"])
@login_required
@admin_required
def crear_provincia():
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return jsonify({"error": "El nombre es requerido"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO provincias (nombre) VALUES (%s)", (nombre,))
        conn.commit()
        provincia_id = cursor.lastrowid
        conn.close()
        
        return jsonify({"id": provincia_id, "nombre": nombre}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/provincias/<int:provincia_id>", methods=["PUT"])
@login_required
@admin_required
def actualizar_provincia(provincia_id):
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        
        if not nombre:
            return jsonify({"error": "El nombre es requerido"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE provincias SET nombre = %s WHERE id = %s", (nombre, provincia_id))
        conn.commit()
        conn.close()
        
        return jsonify({"id": provincia_id, "nombre": nombre})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/provincias/<int:provincia_id>", methods=["DELETE"])
@login_required
@admin_required
def eliminar_provincia(provincia_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si tiene ciudades asociadas
        cursor.execute("SELECT COUNT(*) as count FROM ciudades WHERE provincia_id = %s", (provincia_id,))
        result = cursor.fetchone()
        
        if result['count'] > 0:
            conn.close()
            return jsonify({"error": "No se puede eliminar la provincia porque tiene ciudades asociadas"}), 400
        
        cursor.execute("DELETE FROM provincias WHERE id = %s", (provincia_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Provincia eliminada exitosamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RUTAS PARA CIUDADES ====================

@admin_bp.route("/ciudades")
@login_required
@admin_required
def ciudades():
    return render_template("admin/ciudades.html")

@admin_bp.route("/api/admin/ciudades")
@login_required
@admin_required
def api_ciudades():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT c.*, p.nombre as provincia_nombre 
        FROM ciudades c 
        LEFT JOIN provincias p ON c.provincia_id = p.id 
        ORDER BY c.nombre
        """
        cursor.execute(query)
        ciudades = cursor.fetchall()
        
        # Convertir decimales a float
        for ciudad in ciudades:
            ciudad['latitud'] = safe_float(ciudad['latitud'])
            ciudad['longitud'] = safe_float(ciudad['longitud'])
        
        conn.close()
        return jsonify(ciudades)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/ciudades", methods=["POST"])
@login_required
@admin_required
def crear_ciudad():
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        provincia_id = data.get('provincia_id')
        latitud = data.get('latitud')
        longitud = data.get('longitud')
        
        if not all([nombre, provincia_id, latitud, longitud]):
            return jsonify({"error": "Todos los campos son requeridos"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ciudades (nombre, provincia_id, latitud, longitud) VALUES (%s, %s, %s, %s)",
            (nombre, provincia_id, latitud, longitud)
        )
        conn.commit()
        ciudad_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "id": ciudad_id,
            "nombre": nombre,
            "provincia_id": provincia_id,
            "latitud": float(latitud),
            "longitud": float(longitud)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/ciudades/<int:ciudad_id>", methods=["PUT"])
@login_required
@admin_required
def actualizar_ciudad(ciudad_id):
    try:
        data = request.json
        nombre = data.get('nombre', '').strip()
        provincia_id = data.get('provincia_id')
        latitud = data.get('latitud')
        longitud = data.get('longitud')
        
        if not all([nombre, provincia_id, latitud, longitud]):
            return jsonify({"error": "Todos los campos son requeridos"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ciudades SET nombre = %s, provincia_id = %s, latitud = %s, longitud = %s WHERE id = %s",
            (nombre, provincia_id, latitud, longitud, ciudad_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "id": ciudad_id,
            "nombre": nombre,
            "provincia_id": provincia_id,
            "latitud": float(latitud),
            "longitud": float(longitud)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/ciudades/<int:ciudad_id>", methods=["DELETE"])
@login_required
@admin_required
def eliminar_ciudad(ciudad_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si tiene vías asociadas
        cursor.execute(
            "SELECT COUNT(*) as count FROM vias WHERE ciudad_origen_id = %s OR ciudad_destino_id = %s",
            (ciudad_id, ciudad_id)
        )
        result = cursor.fetchone()
        
        if result['count'] > 0:
            conn.close()
            return jsonify({"error": "No se puede eliminar la ciudad porque tiene vías asociadas"}), 400
        
        cursor.execute("DELETE FROM ciudades WHERE id = %s", (ciudad_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Ciudad eliminada exitosamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RUTAS PARA VÍAS ====================

@admin_bp.route("/vias")
@login_required
@admin_required
def vias():
    return render_template("admin/vias.html")

@admin_bp.route("/api/admin/vias")
@login_required
@admin_required
def api_vias():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT v.*, 
               c1.nombre as ciudad_origen_nombre,
               c2.nombre as ciudad_destino_nombre
        FROM vias v
        LEFT JOIN ciudades c1 ON v.ciudad_origen_id = c1.id
        LEFT JOIN ciudades c2 ON v.ciudad_destino_id = c2.id
        ORDER BY c1.nombre, c2.nombre
        """
        cursor.execute(query)
        vias = cursor.fetchall()
        
        # Convertir decimales a float
        for via in vias:
            via['distancia_km'] = safe_float(via['distancia_km'])
            if 'tiempo_minutos' in via:
                via['tiempo_minutos'] = safe_float(via['tiempo_minutos'])
        
        conn.close()
        return jsonify(vias)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/vias", methods=["POST"])
@login_required
@admin_required
def crear_via():
    try:
        data = request.json
        ciudad_origen_id = data.get('ciudad_origen_id')
        ciudad_destino_id = data.get('ciudad_destino_id')
        distancia_km = data.get('distancia_km')
        tiempo_minutos = data.get('tiempo_minutos')
        estado = data.get('estado', 'bueno')
        
        if not all([ciudad_origen_id, ciudad_destino_id, distancia_km]):
            return jsonify({"error": "Campos requeridos: origen, destino y distancia"}), 400
        
        if ciudad_origen_id == ciudad_destino_id:
            return jsonify({"error": "La ciudad origen y destino no pueden ser iguales"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si la vía ya existe
        cursor.execute(
            "SELECT id FROM vias WHERE (ciudad_origen_id = %s AND ciudad_destino_id = %s) OR (ciudad_origen_id = %s AND ciudad_destino_id = %s)",
            (ciudad_origen_id, ciudad_destino_id, ciudad_destino_id, ciudad_origen_id)
        )
        
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Ya existe una vía entre estas ciudades"}), 400
        
        cursor.execute(
            "INSERT INTO vias (ciudad_origen_id, ciudad_destino_id, distancia_km, tiempo_minutos, estado) VALUES (%s, %s, %s, %s, %s)",
            (ciudad_origen_id, ciudad_destino_id, distancia_km, tiempo_minutos, estado)
        )
        conn.commit()
        via_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            "id": via_id,
            "ciudad_origen_id": ciudad_origen_id,
            "ciudad_destino_id": ciudad_destino_id,
            "distancia_km": float(distancia_km),
            "tiempo_minutos": float(tiempo_minutos) if tiempo_minutos else None,
            "estado": estado
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/vias/<int:via_id>", methods=["PUT"])
@login_required
@admin_required
def actualizar_via(via_id):
    try:
        data = request.json
        distancia_km = data.get('distancia_km')
        tiempo_minutos = data.get('tiempo_minutos')
        estado = data.get('estado', 'bueno')
        
        if not distancia_km:
            return jsonify({"error": "La distancia es requerida"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE vias SET distancia_km = %s, tiempo_minutos = %s, estado = %s WHERE id = %s",
            (distancia_km, tiempo_minutos, estado, via_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "id": via_id,
            "distancia_km": float(distancia_km),
            "tiempo_minutos": float(tiempo_minutos) if tiempo_minutos else None,
            "estado": estado
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route("/api/admin/vias/<int:via_id>", methods=["DELETE"])
@login_required
@admin_required
def eliminar_via(via_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vias WHERE id = %s", (via_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Vía eliminada exitosamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== RUTA ESPECIAL PARA CAMBIO DE ESTADO ====================

@admin_bp.route("/api/admin/vias/<int:via_id>/estado", methods=["PUT"])
@login_required
@admin_required
def cambiar_estado_via(via_id):
    try:
        data = request.json
        estado = data.get('estado')
        
        if estado not in ['bueno', 'regular', 'malo']:
            return jsonify({"error": "Estado inválido. Debe ser bueno, regular o malo"}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE vias SET estado = %s WHERE id = %s", (estado, via_id))
        conn.commit()
        conn.close()
        
        return jsonify({"message": f"Estado cambiado a {estado}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500