from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from DB import get_connection
from decimal import Decimal

usuario_bp = Blueprint("usuario", __name__)

def safe_float(value):
    """Convierte cualquier valor numérico a float de manera segura"""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)

@usuario_bp.route("/consultar")
@login_required
def consultar_rutas():
    return render_template("consultar.html")

@usuario_bp.route("/api/ciudades")
def api_ciudades():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, latitud AS lat, longitud AS lon FROM ciudades ORDER BY nombre")
    ciudades = cursor.fetchall()
    conn.close()
    return jsonify(ciudades)

@usuario_bp.route("/api/calcular_ruta", methods=["POST"])
def api_calcular_ruta():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        try:
            origen = int(data['origen'])
            destino = int(data['destino'])
        except (ValueError, KeyError) as e:
            return jsonify({"error": f"Parámetros inválidos: {str(e)}"}), 400
            
        criterio = data.get('criterio', 'distancia')  # 'distancia' o 'tiempo'

        conn = get_connection()
        if not conn:
            return jsonify({"error": "Error de conexión a la base de datos"}), 500
            
        cursor = conn.cursor(dictionary=True)

        # Obtener todas las ciudades
        cursor.execute("SELECT * FROM ciudades")
        ciudades = {row['id']: row for row in cursor.fetchall()}

        if origen not in ciudades or destino not in ciudades:
            conn.close()
            return jsonify({"error": "Ciudad origen o destino no válida"}), 400

        from collections import defaultdict
        import heapq

        grafo_distancia = defaultdict(list)
        grafo_tiempo = defaultdict(list)
        
        # Verificar qué columnas existen en la tabla vias
        cursor.execute("SHOW COLUMNS FROM vias")
        columnas = [col['Field'] for col in cursor.fetchall()]
        
        # Adaptar la consulta según las columnas disponibles
        if 'ciudad_origen_id' in columnas:
            origen_col = 'ciudad_origen_id'
            destino_col = 'ciudad_destino_id'
        else:
            origen_col = 'origen_id'
            destino_col = 'destino_id'
            
        cursor.execute("SELECT * FROM vias")
        vias_dict = defaultdict(dict)

        for via in cursor.fetchall():
            origen_id = via[origen_col]
            destino_id = via[destino_col]
            distancia = safe_float(via['distancia_km'])
            # Verificar si existe la columna tiempo_minutos
            if 'tiempo_minutos' in via and via['tiempo_minutos'] is not None:
                tiempo = safe_float(via['tiempo_minutos'])
            else:
                tiempo = distancia * 1.5  # Fallback si no existe tiempo
            estado = via.get('estado', 'BUENA')

            grafo_distancia[origen_id].append((destino_id, distancia))
            grafo_distancia[destino_id].append((origen_id, distancia))
            grafo_tiempo[origen_id].append((destino_id, tiempo))
            grafo_tiempo[destino_id].append((origen_id, tiempo))

            vias_dict[(origen_id, destino_id)] = {
                'estado': estado,
                'distancia': distancia,
                'tiempo': tiempo
            }
            vias_dict[(destino_id, origen_id)] = {
                'estado': estado,
                'distancia': distancia,
                'tiempo': tiempo
            }

        # Seleccionar el grafo según el criterio
        grafo = grafo_distancia if criterio == 'distancia' else grafo_tiempo

        dist = {c: float('inf') for c in ciudades}
        prev = {c: None for c in ciudades}
        dist[origen] = 0
        heap = [(0, origen)]

        while heap:
            d_actual, actual = heapq.heappop(heap)
            if actual == destino:
                break
            for vecino, peso in grafo[actual]:
                nueva_dist = d_actual + peso
                if nueva_dist < dist[vecino]:
                    dist[vecino] = nueva_dist
                    prev[vecino] = actual
                    heapq.heappush(heap, (nueva_dist, vecino))

        # Verificar si se encontró una ruta
        if dist[destino] == float('inf'):
            conn.close()
            return jsonify({"error": "No se encontró ruta entre las ciudades seleccionadas"}), 404

        ruta = []
        actual = destino
        while actual:
            ruta.insert(0, actual)
            actual = prev[actual]

        ruta_coords = []
        distancia_total = 0
        tiempo_total = 0
        
        for i, cid in enumerate(ruta):
            punto = {
                "id": cid,
                "nombre": ciudades[cid]["nombre"],
                "lat": safe_float(ciudades[cid]["latitud"]),
                "lon": safe_float(ciudades[cid]["longitud"])
            }
            if i > 0:
                origen_id = ruta[i-1]
                destino_id = cid
                via_info = vias_dict.get((origen_id, destino_id), {})
                punto["estado"] = via_info.get('estado', 'BUENA')
                distancia_total += safe_float(via_info.get('distancia', 0))
                tiempo_total += safe_float(via_info.get('tiempo', 0))
            ruta_coords.append(punto)

        ruta_nombres = " → ".join([ciudades[cid]["nombre"] for cid in ruta])
        distancia_total = round(distancia_total, 2)
        tiempo_total = round(tiempo_total, 2)

        cursor.close()
        conn.close()

        # Guardar consulta en el historial
        from .historial_routes import guardar_consulta_historial
        guardar_consulta_historial(
            current_user.username, 
            origen, 
            destino, 
            ruta_coords, 
            distancia_total
        )

        return jsonify({
            "ruta": ruta_coords,
            "descripcion": f"Ruta: {ruta_nombres}",
            "distancia_total": distancia_total,
            "tiempo_total": tiempo_total,
            "criterio_usado": criterio
        })
        
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.close()
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500
