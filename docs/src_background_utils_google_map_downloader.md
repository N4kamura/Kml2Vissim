# Documentación de src/background/utils/google_map_downloader.py

## Descripción
Este archivo contiene la clase `GoogleMapDownloader` que se encarga de descargar imágenes de Google Maps basadas en coordenadas geográficas y niveles de zoom. También incluye métodos para convertir coordenadas geográficas a coordenadas de tile y calcular dimensiones de polígonos.

## Clase

### GoogleMapDownloader
Clase principal para descargar imágenes de Google Maps y realizar conversiones de coordenadas.

#### Constructor
```python
GoogleMapDownloader(points, zoom)
```

##### Parámetros
- `points`: Lista de coordenadas que definen el área de interés
- `zoom`: Nivel de zoom para las imágenes de Google Maps

#### Métodos

##### polygon_dimensions(self, coordinates) -> list[float, float]
Calcula el ancho y alto de un polígono en metros utilizando la proyección Mercator.

###### Parámetros
- `coordinates`: Lista de coordenadas (latitud, longitud) del polígono

###### Retorno
Lista con el ancho y alto del polígono en metros

###### Proceso
1. Encuentra los límites mínimos y máximos de latitud y longitud
2. Convierte las coordenadas a proyección Mercator
3. Calcula el ancho y alto en metros

##### calculate_polygon_bounds(self, coordinates) -> list[float, float, float, float]
Calcula los límites de un polígono en coordenadas de tile.

###### Parámetros
- `coordinates`: Lista de coordenadas (x, y) en formato de tile

###### Retorno
Lista con los límites [x_min, x_max, y_min, y_max]

##### get_tile_bounds(self, x, y) -> list[float, float, float, float]
Obtiene las coordenadas geográficas de las esquinas de un tile.

###### Parámetros
- `x`: Coordenada X del tile
- `y`: Coordenada Y del tile

###### Retorno
Lista con las coordenadas [norte, sur, oeste, este] del tile

###### Fórmulas
- `numTiles = 1 << self.zoom`
- `lon_deg = x / numTiles * 360 - 180`
- `lat_rad = atan(sinh(π * (1 - 2 * y / numTiles)))`
- `lat_deg = degrees(lat_rad)`

##### get_XY(self, lat, lng)
Convierte coordenadas geográficas a coordenadas de tile.

###### Parámetros
- `lat`: Latitud en grados decimales
- `lng`: Longitud en grados decimales

###### Retorno
Tupla con las coordenadas de tile (x, y)

###### Fórmulas
- `point_x = (tile_size / 2 + lng * tile_size / 360.0) * numTiles // tile_size`
- `sin_y = sin(lat * (π / 180.0))`
- `point_y = ((tile_size / 2) + 0.5 * log((1 + sin_y) / (1 - sin_y)) * -(tile_size / (2 * π))) * numTiles // tile_size`

##### generate_image(self, x, y, count, path)
Descarga una imagen de Google Maps para un tile específico.

###### Parámetros
- `x`: Coordenada X del tile
- `y`: Coordenada Y del tile
- `count`: Número secuencial para nombrar la imagen
- `path`: Ruta donde se guardará la imagen

###### Proceso
1. Construye la URL de Google Maps con las coordenadas y zoom
2. Realiza la solicitud HTTP con un User-Agent personalizado
3. Guarda la imagen en el directorio especificado con el nombre "FOTO_{count}.png"
4. Muestra un mensaje de error si la descarga falla

## Dependencias
- src.background.utils.geographic_tools
- requests
- os
- math

## Notas
- El tamaño de tile está fijado en 256 píxeles
- Se utiliza un User-Agent personalizado para evitar bloqueos por parte de Google Maps
- Las imágenes se descargan en formato PNG
- El nivel de zoom se establece en el constructor de la clase