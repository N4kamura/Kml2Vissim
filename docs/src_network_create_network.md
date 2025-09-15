# Documentación de src/network/create_network.py

## Descripción
Este archivo contiene la función principal `vissim_creator` que se encarga de crear redes de tráfico en formato Vissim (.inpx) a partir de archivos KML y datos de OpenStreetMap (OSM). La función procesa las coordenadas del polígono definido en el KML, obtiene datos de carreteras de OSM y genera un archivo de red compatible con Vissim.

## Funciones

### vissim_creator(kml_path, inpx_file_name) -> None
Función principal que crea una red de tráfico en Vissim a partir de un archivo KML.

#### Parámetros
- `kml_path`: Ruta al archivo KML que define el área de interés
- `inpx_file_name`: Nombre base para el archivo de salida .inpx

#### Proceso

1. **Lectura del archivo KML**:
   - Parsea el archivo KML para extraer las coordenadas del polígono
   - Convierte las coordenadas a formato (longitud, latitud)
   - Crea un objeto `Polygon` con las coordenadas

2. **Cálculo del bounding box**:
   - Crea un objeto `GoogleMapDownloader` con las coordenadas
   - Calcula los límites del polígono en coordenadas de tile
   - Convierte los límites a proyección Mercator
   - Calcula el punto de referencia como el centroide del bounding box

3. **Extracción de datos de OSM**:
   - Utiliza `osmnx` para obtener datos de carreteras del área definida por el polígono
   - Convierte el grafo de OSM a GeoDataFrames de nodos y aristas

4. **Procesamiento de geometrías**:
   - Procesa las geometrías de las aristas usando `process_geometry`
   - Convierte las coordenadas a proyección Mercator

5. **Procesamiento de nodos**:
   - Reinicia el índice del DataFrame de nodos
   - Renombra columnas para facilitar la combinación

6. **Procesamiento de aristas**:
   - Reinicia el índice del DataFrame de aristas
   - Renombra columnas para identificar nodos de inicio y fin
   - Combina con el DataFrame de nodos para obtener coordenadas de nodos

7. **Conversión a coordenadas UTM**:
   - Convierte las coordenadas de nodos a proyección Mercator
   - Convierte los valores a cadenas de texto

8. **Filtrado de tipos de carretera**:
   - Elimina aristas de tipo 'pedestrian', 'footway' y 'cycleway'

9. **Generación del archivo INPX**:
   - Copia una plantilla XML vacía
   - Agrega el punto de referencia al archivo
   - Crea elementos XML para cada arista:
     - Configura propiedades del link (velocidad, dirección, etc.)
     - Agrega información del nombre de la carretera
     - Define la geometría con puntos 3D de inicio y fin
     - Crea carriles para cada link (actualmente fijo en 2 carriles)

10. **Guardado del archivo**:
    - Escribe el archivo XML resultante con extensión .inpx

#### Notas sobre el código
- Hay secciones comentadas que sugieren diferentes enfoques para determinar el número de carriles
- La función actualmente crea 2 carriles por link sin considerar el número real de carriles en OSM
- Se utiliza una plantilla XML vacía como base para construir el archivo de salida

## Dependencias
- src.background.utils.geographic_tools
- src.background.get_background (GoogleMapDownloader)
- xml.etree.ElementTree
- shapely.geometry.Polygon
- osmnx
- shutil
- os
- pandas
- src.network.utils.coordinate_tools

## Consideraciones
- La función asume que el archivo KML contiene un polígono cerrado
- Los datos de OSM se obtienen en línea, por lo que se requiere conexión a internet
- El número de carriles está actualmente fijado en 2, sin considerar los datos reales de OSM
- La función imprime "FIN DE CREACIÓN DE REDES EN VISSIM" al completar el proceso