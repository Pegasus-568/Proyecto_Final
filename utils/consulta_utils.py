import mysql.connector
import json
from DB import get_connection

# Obtener todas las ciudades del Ecuador (con nombre, lat, lon)
def obtener_ciudades():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre, latitud AS lat, longitud AS lon FROM ciudades")
    ciudades = cursor.fetchall()

    cursor.close()
    conn.close()

    return ciudades


# Obtener todas las vías con información completa y coordenadas de origen/destino
def obtener_vias():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT 
        v.id,
        v.distancia_km AS distancia,
        v.tiempo_minutos AS tiempo,
        v.estado,

        o.id AS origen_id,
        o.nombre AS origen_nombre,
        o.latitud AS origen_lat,
        o.longitud AS origen_lon,

        d.id AS destino_id,
        d.nombre AS destino_nombre,
        d.latitud AS destino_lat,
        d.longitud AS destino_lon

    FROM vias v
    JOIN ciudades o ON v.ciudad_origen_id = o.id
    JOIN ciudades d ON v.ciudad_destino_id = d.id
    """

    cursor.execute(query)
    vias_raw = cursor.fetchall()
    cursor.close()
    conn.close()

    # Reestructurar para el mapa
    vias = []
    for v in vias_raw:
        vias.append({
            "id": v["id"],
            "estado": v["estado"],
            "distancia": v["distancia"],
            "tiempo": v["tiempo"],
            "origen": {
                "id": v["origen_id"],
                "nombre": v["origen_nombre"],
                "lat": v["origen_lat"],
                "lon": v["origen_lon"]
            },
            "destino": {
                "id": v["destino_id"],
                "nombre": v["destino_nombre"],
                "lat": v["destino_lat"],
                "lon": v["destino_lon"]
            }
        })

    return vias


# Obtener las ciudades agrupadas por provincia para los selects del formulario
def obtener_ciudades_por_provincia():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT c.id, c.nombre AS ciudad, p.nombre AS provincia
    FROM ciudades c
    JOIN provincias p ON c.provincia_id = p.id
    ORDER BY p.nombre, c.nombre
    """
    cursor.execute(query)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()

    # Agrupar por provincia
    agrupadas = {}
    for fila in resultados:
        provincia = fila["provincia"]
        ciudad = {"id": fila["id"], "nombre": fila["ciudad"]}
        agrupadas.setdefault(provincia, []).append(ciudad)

    return agrupadas

import networkx as nx

# Construye el grafo a partir de las vías para usar en Dijkstra
def construir_grafo():
    ciudades = obtener_ciudades()
    vias = obtener_vias()

    G = nx.Graph()
    posicion_nodos = {}  # clave: id ciudad, valor: (lat, lon)

    # Añadir nodos
    for ciudad in ciudades:
        ciudad_id = ciudad["id"]
        G.add_node(ciudad_id, nombre=ciudad["nombre"])
        posicion_nodos[ciudad_id] = (ciudad["lon"], ciudad["lat"])  # Leaflet usa lon, lat

    # Añadir aristas (bidireccional)
    for via in vias:
        origen = via["origen"]["id"]
        destino = via["destino"]["id"]
        distancia = via["distancia"]
        tiempo = via["tiempo"]
        estado = via["estado"]

        G.add_edge(origen, destino, distancia=distancia, tiempo=tiempo, estado=estado)

    return G, posicion_nodos

def encontrar_ruta_optima(G, origen_id, destino_id, criterio="distancia"):
    try:
        # Calcula la ruta óptima usando el criterio indicado (distancia o tiempo)
        ruta_ids = nx.shortest_path(G, source=origen_id, target=destino_id, weight=criterio)
        ruta_completa = []

        # Convertimos la ruta en una lista de tramos con datos
        for i in range(len(ruta_ids) - 1):
            origen = ruta_ids[i]
            destino = ruta_ids[i + 1]
            datos_arista = G[origen][destino]

            ruta_completa.append({
                "origen_id": origen,
                "destino_id": destino,
                "distancia": datos_arista["distancia"],
                "tiempo": datos_arista["tiempo"],
                "estado": datos_arista["estado"]
            })

        return ruta_completa

    except nx.NetworkXNoPath:
        return []
    

