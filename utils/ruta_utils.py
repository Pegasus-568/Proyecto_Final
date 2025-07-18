import networkx as nx
import mysql.connector

def calcular_ruta_optima(origen_id, destino_id):
    # Conexión a la base de datos
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="rutas_ecuador"
    )
    cursor = conn.cursor(dictionary=True)

    # Crear grafo dirigido
    G = nx.DiGraph()

    # Cargar nodos (ciudades)
    cursor.execute("SELECT id, nombre, lat, lng FROM ciudades")
    ciudades = cursor.fetchall()
    ciudad_dict = {c['id']: c for c in ciudades}

    for ciudad in ciudades:
        G.add_node(ciudad['id'], nombre=ciudad['nombre'], lat=ciudad['lat'], lng=ciudad['lng'])

    # Cargar aristas (vías)
    cursor.execute("""
        SELECT v.origen_id, v.destino_id, v.distancia_km, v.tiempo_min, v.estado,
               c1.lat AS lat_origen, c1.lng AS lng_origen,
               c2.lat AS lat_destino, c2.lng AS lng_destino
        FROM vias v
        JOIN ciudades c1 ON v.origen_id = c1.id
        JOIN ciudades c2 ON v.destino_id = c2.id
    """)
    vias = cursor.fetchall()

    for via in vias:
        G.add_edge(via['origen_id'], via['destino_id'],
                   distancia=via['distancia_km'],
                   tiempo=via['tiempo_min'],
                   estado=via['estado'],
                   lat_origen=via['lat_origen'], lng_origen=via['lng_origen'],
                   lat_destino=via['lat_destino'], lng_destino=via['lng_destino'])

    try:
        ruta = nx.dijkstra_path(G, source=origen_id, target=destino_id, weight='distancia')
    except nx.NetworkXNoPath:
        return {'error': 'No existe una ruta entre las ciudades seleccionadas'}

    # Construir respuesta con ciudades y vías
    ciudades_ruta = [ciudad_dict[ciudad_id] for ciudad_id in ruta]
    vias_ruta = []

    for i in range(len(ruta) - 1):
        u, v = ruta[i], ruta[i+1]
        data = G.get_edge_data(u, v)
        vias_ruta.append({
            'lat_origen': data['lat_origen'],
            'lng_origen': data['lng_origen'],
            'lat_destino': data['lat_destino'],
            'lng_destino': data['lng_destino'],
            'distancia': data['distancia'],
            'tiempo': data['tiempo'],
            'estado': data['estado']
        })

    conn.close()

    return {
        'ciudades': ciudades_ruta,
        'vias': vias_ruta
    }