# Documentación del Proyecto Kml2Vissim

## Descripción
Este proyecto convierte archivos KML que contienen polígonos en redes de tráfico para el software Vissim. Utiliza datos de OpenStreetMap y descarga imágenes de Google Maps para crear un entorno completo que puede ser utilizado en simulaciones de tráfico.

## Estructura de Documentación

### Archivos Principales

1. [main.py](main.md) - Punto de entrada principal de la aplicación con interfaz gráfica
2. [interface/ui.py](interface_ui.md) - Implementación de la interfaz de usuario generada automáticamente

### Módulo de Red (`src/network`)

1. [create_network.py](src_network_create_network.md) - Función principal para crear redes de tráfico en Vissim
2. [utils/coordinate_tools.py](src_network_utils_coordinate_tools.md) - Herramientas para conversión de coordenadas

### Módulo de Fondo (`src/background`)

1. [get_background.py](src_background_get_background.md) - Funciones para procesar archivos KML y generar imágenes de fondo
2. [utils/geographic_tools.py](src_background_utils_geographic_tools.md) - Funciones utilitarias para conversión de coordenadas geográficas
3. [utils/google_map_downloader.py](src_background_utils_google_map_downloader.md) - Clase para descargar imágenes de Google Maps

## Notas Generales

- Los archivos `__init__.py` vacíos no requieren documentación específica
- La documentación se ha generado sin modificar el código fuente
- Todos los archivos .py del proyecto han sido documentados
- Las dependencias y flujos de trabajo se han descrito en cada archivo de documentación

## Dependencias Principales

- PyQt5: Para la interfaz gráfica
- osmnx: Para obtener datos de OpenStreetMap
- shapely: Para manipulación de geometrías
- OpenCV (cv2): Para procesamiento de imágenes
- GDAL: Para conversión de formatos geoespaciales
- requests: Para descarga de imágenes de Google Maps
- geopy: Para cálculos de distancias geográficas
- tqdm: Para barras de progreso

## Flujo de Trabajo General

1. El usuario selecciona un archivo KML con un polígono
2. Se procesa el KML para obtener coordenadas del polígono
3. Se descargan imágenes de Google Maps del área definida
4. Se combinan las imágenes en una sola imagen de fondo
5. Se obtienen datos de carreteras de OpenStreetMap
6. Se crea la red de tráfico en formato Vissim (.inpx)
7. Se integra la imagen de fondo con la red de tráfico