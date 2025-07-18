from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from DB import get_connection
from decimal import Decimal
import json
from datetime import datetime

historial_bp = Blueprint("historial", __name__)

def safe_float(value):
    """Convierte cualquier valor numérico a float de manera segura"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)

@historial_bp.route("/historial")
@login_required
def historial():
    """Página principal del historial de consultas"""
    return render_template("historial.html")

@historial_bp.route("/api/historial")
@login_required
def api_historial():
    """API para obtener el historial de consultas del usuario actual"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Obtener historial del usuario actual con información de ciudades
        query = """
        SELECT 
            rq.id,
            rq.username,
            rq.start_city_id,
            rq.end_city_id,
            rq.best_route,
            rq.total_distance,
            rq.query_date,
            c1.nombre as ciudad_origen,
            c2.nombre as ciudad_destino
        FROM route_queries rq
        LEFT JOIN ciudades c1 ON rq.start_city_id = c1.id
        LEFT JOIN ciudades c2 ON rq.end_city_id = c2.id
        WHERE rq.username = %s
        ORDER BY rq.query_date DESC
        LIMIT 50
        """
        
        cursor.execute(query, (current_user.username,))
        historial = cursor.fetchall()
        
        # Procesar los datos para el frontend
        historial_procesado = []
        for item in historial:
            # Parsear la ruta si está en formato JSON
            try:
                best_route = json.loads(item['best_route']) if item['best_route'] else []
            except:
                best_route = []
            
            historial_procesado.append({
                'id': item['id'],
                'ciudad_origen': item['ciudad_origen'],
                'ciudad_destino': item['ciudad_destino'],
                'total_distance': safe_float(item['total_distance']),
                'query_date': item['query_date'].strftime('%d/%m/%Y %H:%M'),
                'best_route': best_route,
                'num_ciudades': len(best_route)
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(historial_procesado)
        
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({"error": f"Error al obtener historial: {str(e)}"}), 500

@historial_bp.route("/api/historial/<int:consulta_id>")
@login_required 
def api_detalle_consulta(consulta_id):
    """API para obtener el detalle completo de una consulta específica"""
    try:
        conn = get_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)
        
        # Obtener detalle de la consulta específica
        query = """
        SELECT 
            rq.id,
            rq.username,
            rq.start_city_id,
            rq.end_city_id,
            rq.best_route,
            rq.total_distance,
            rq.query_date,
            c1.nombre as ciudad_origen,
            c1.latitud as lat_origen,
            c1.longitud as lon_origen,
            c2.nombre as ciudad_destino,
            c2.latitud as lat_destino,
            c2.longitud as lon_destino
        FROM route_queries rq
        LEFT JOIN ciudades c1 ON rq.start_city_id = c1.id
        LEFT JOIN ciudades c2 ON rq.end_city_id = c2.id
        WHERE rq.id = %s AND rq.username = %s
        """
        
        cursor.execute(query, (consulta_id, current_user.username))
        consulta = cursor.fetchone()
        
        if not consulta:
            cursor.close()
            conn.close()
            return jsonify({"error": "Consulta no encontrada"}), 404
        
        # Parsear la ruta completa
        try:
            ruta_completa = json.loads(consulta['best_route']) if consulta['best_route'] else []
        except:
            ruta_completa = []
        
        # Calcular tiempo estimado (usando la misma lógica que en user_routes)
        tiempo_total = safe_float(consulta['total_distance']) * 1.5  # Fallback simple
        
        detalle = {
            'id': consulta['id'],
            'ciudad_origen': consulta['ciudad_origen'],
            'ciudad_destino': consulta['ciudad_destino'],
            'lat_origen': safe_float(consulta['lat_origen']),
            'lon_origen': safe_float(consulta['lon_origen']),
            'lat_destino': safe_float(consulta['lat_destino']),
            'lon_destino': safe_float(consulta['lon_destino']),
            'total_distance': safe_float(consulta['total_distance']),
            'tiempo_estimado': tiempo_total,
            'query_date': consulta['query_date'].strftime('%d/%m/%Y %H:%M:%S'),
            'ruta_completa': ruta_completa,
            'descripcion_ruta': ' → '.join([ciudad['nombre'] for ciudad in ruta_completa])
        }
        
        cursor.close()
        conn.close()
        
        return jsonify(detalle)
        
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({"error": f"Error al obtener detalle: {str(e)}"}), 500

def guardar_consulta_historial(username, origen_id, destino_id, ruta_coords, distancia_total):
    """Función auxiliar para guardar una consulta en el historial"""
    try:
        conn = get_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Convertir ruta_coords a JSON para almacenar
        ruta_json = json.dumps(ruta_coords, ensure_ascii=False)
        
        query = """
        INSERT INTO route_queries (username, start_city_id, end_city_id, best_route, total_distance)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (username, origen_id, destino_id, ruta_json, distancia_total))
        conn.commit()
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error guardando en historial: {str(e)}")
        if 'conn' in locals() and conn:
            conn.close()
        return False