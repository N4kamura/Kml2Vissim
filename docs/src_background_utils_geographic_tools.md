# Documentación de src/background/utils/geographic_tools.py

## Descripción
Este archivo contiene funciones utilitarias para la conversión de coordenadas geográficas y manipulación de geometrías. Las funciones principales se enfocan en convertir coordenadas de formato geográfico a proyección Mercator, que es utilizada por Vissim.

## Constantes
- `RADIUS`: Radio de la Tierra en metros (6371000)
- `A`: Factor de escala (1)
- `B`: Factor de escala (1)

## Funciones

### convert_to_mercator(lon, lat)
Convierte coordenadas geográficas (longitud, latitud) a coordenadas en proyección Mercator.

#### Parámetros
- `lon`: Longitud en grados decimales
- `lat`: Latitud en grados decimales

#### Retorno
Lista con las coordenadas en proyección Mercator [lon_mer, lat_mer]

#### Fórmulas
- `lon_mer = lon * RADIUS * π / 180 / B`
- `lat_mer = RADIUS * ln(tan(0.5 * (lat * π / 180 / A + π / 2)))`

### convert_coordinates_to_utm(coordinates)
Convierte una lista de coordenadas geográficas a coordenadas en proyección Mercator.

#### Parámetros
- `coordinates`: Lista de tuplas (lon, lat) con coordenadas geográficas

#### Retorno
Lista de tuplas con coordenadas en proyección Mercator

### process_geometry(wkt)
Procesa una cadena WKT (Well-Known Text) de tipo LINESTRING para extraer las coordenadas.

#### Parámetros
- `wkt`: Cadena WKT que representa una línea

#### Proceso
1. Elimina los prefijos 'LINESTRING (' y el paréntesis final ')'
2. Divide la cadena en pares de coordenadas separados por ', '
3. Convierte cada par de coordenadas en una tupla de números flotantes

#### Retorno
Lista de tuplas con las coordenadas extraídas

### apply_desfase(coordinates, desfase_x, desfase_y)
Aplica un desfase a una lista de coordenadas.

#### Parámetros
- `coordinates`: Lista de tuplas (lon, lat) con coordenadas
- `desfase_x`: Desfase en el eje X
- `desfase_y`: Desfase en el eje Y

#### Retorno
Lista de tuplas con coordenadas desplazadas

## Dependencias
- math

## Notas
- Las coordenadas se manejan en formato (longitud, latitud)
- La proyección Mercator es necesaria para la compatibilidad con Vissim
- Las constantes A y B se utilizan como factores de escala en las conversiones