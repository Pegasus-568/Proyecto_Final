from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from utils.consulta_utils import obtener_ciudades_por_provincia  # Asegúrate de tener esta función
from utils.ruta_utils import calcular_ruta_optima
from DB import get_connection

usuario_bp = Blueprint("usuario", __name__)

@usuario_bp.route('/consultar', methods=['GET'])
@login_required
def consultar_rutas():
    ciudades_por_provincia = obtener_ciudades_por_provincia()

    # Para visualización Leaflet, transformar ciudades a un solo array plano
    ciudades_list = []
    for ciudades in ciudades_por_provincia.values():
        ciudades_list.extend(ciudades)

    # Las vías aún pueden estar vacías si no se procesan (puedes agregar luego)
    vias_json = []
    ruta_resultado = []

    return render_template("consultar.html",
                           ciudades_por_provincia=ciudades_por_provincia,
                           ciudades_json=ciudades_list,
                           vias_json=vias_json,
                           ruta_resultado=ruta_resultado)

@usuario_bp.route('/api/calcular_ruta', methods=['POST'])
@login_required
def api_calcular_ruta():
    data = request.json
    origen = int(data['origen'])
    destino = int(data['destino'])

    resultado = calcular_ruta_optima(origen, destino)
    return jsonify(resultado)

@usuario_bp.route('/api/ciudades')
@login_required
def api_ciudades():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, latitud AS lat, longitud AS lng FROM ciudades ORDER BY nombre")
    ciudades = cursor.fetchall()
    conn.close()
    return jsonify(ciudades)
