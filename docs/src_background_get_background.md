# Documentación de src/background/get_background.py

## Descripción
Este archivo contiene funciones para procesar archivos KML y generar imágenes de fondo que pueden ser utilizadas en Vissim. Incluye funciones para convertir archivos KML en imágenes PNG y luego convertirlas a formatos compatibles con Vissim como TIFF y JPEG.

## Funciones

### kml2png_function(kml_file, inpx_file_name) -> None
Función principal que procesa un archivo KML y genera una imagen compuesta a partir de múltiples fotografías satelitales.

#### Parámetros
- `kml_file`: Ruta al archivo KML de entrada
- `inpx_file_name`: Nombre base para los archivos de salida

#### Proceso
1. Parsea el archivo KML para extraer las coordenadas del polígono
2. Crea un objeto `GoogleMapDownloader` con las coordenadas y nivel de zoom 20
3. Convierte las coordenadas geográficas a coordenadas de tile
4. Calcula los límites de los tiles necesarios
5. Descarga las imágenes satelitales correspondientes a cada tile con barra de progreso
6. Combina todas las imágenes descargadas en una sola imagen grande
7. Guarda la imagen combinada como 'FOTO_TOTAL.png'

### convert_background(kml_file, inpx_file_name) -> None
Función que convierte la imagen PNG generada a formatos TIFF y JPEG, y actualiza el archivo INPX de Vissim con la información del fondo.

#### Parámetros
- `kml_file`: Ruta al archivo KML de entrada
- `inpx_file_name`: Nombre base para los archivos de salida

#### Proceso
1. Parsea el archivo KML para extraer las coordenadas del polígono
2. Crea un objeto `GoogleMapDownloader` con las coordenadas y nivel de zoom 20
3. Convierte las coordenadas geográficas a coordenadas de tile
4. Calcula los límites de los tiles y las dimensiones del polígono
5. Obtiene las coordenadas de las esquinas del área total
6. Convierte las coordenadas a proyección Mercator
7. Utiliza GDAL para convertir la imagen PNG a TIFF con georreferenciación
8. Convierte el TIFF a JPEG con calidad del 90%
9. Elimina archivos temporales innecesarios
10. Actualiza el archivo INPX de Vissim con la información del fondo:
    - Agrega la imagen de fondo al XML
    - Establece las coordenadas de la esquina inferior izquierda (coordBL)
    - Establece las coordenadas de la esquina superior derecha (coordTR)
    - Configura parámetros de visualización del fondo

## Dependencias
- os
- xml.etree.ElementTree
- shapely.geometry.Polygon
- cv2 (OpenCV)
- numpy
- src.background.utils.geographic_tools
- src.background.utils.google_map_downloader
- subprocess
- time
- geopy.distance.geodesic
- tqdm

## Notas
- La función utiliza Google Maps para descargar las imágenes satelitales
- El nivel de zoom está fijado en 20 para obtener imágenes de alta resolución
- Se implementa un sistema de espera cada 30 imágenes descargadas para evitar sobrecargar el servidor
- Las coordenadas se manejan en formato (latitud, longitud) y se convierten a (longitud, latitud) según sea necesario
- La conversión a proyección Mercator es necesaria para la compatibilidad con Vissim