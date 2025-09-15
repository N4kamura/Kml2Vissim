# Documentación de src/network/utils/coordinate_tools.py

## Descripción
Este archivo contiene funciones especializadas para convertir coordenadas geográficas (latitud y longitud por separado) a coordenadas en proyección Mercator. Estas funciones son utilizadas específicamente en el proceso de creación de redes de tráfico para Vissim.

## Constantes
- `RADIUS`: Radio de la Tierra en metros (6390602.66473445)
- `A`: Factor de escala para latitud (1.0030289588831154)
- `B`: Factor de escala para longitud (1.003076128580129)

## Funciones

### convert_to_mercator_lat(lat)
Convierte una latitud geográfica a coordenada Y en proyección Mercator.

#### Parámetros
- `lat`: Latitud en grados decimales

#### Retorno
Cadena de texto con la coordenada Y en proyección Mercator

#### Fórmula
`lat_mer = RADIUS * ln(tan(0.5 * (lat * π / 180 / A + π / 2)))`

### convert_to_mercator_lon(lon)
Convierte una longitud geográfica a coordenada X en proyección Mercator.

#### Parámetros
- `lon`: Longitud en grados decimales

#### Retorno
Cadena de texto con la coordenada X en proyección Mercator

#### Fórmula
`lon_mer = lon * RADIUS * π / 180 / B`

## Dependencias
- math

## Notas
- Las coordenadas se manejan en formato (longitud, latitud)
- Las constantes A y B son factores de escala específicos para este proyecto
- El radio de la Tierra utilizado es ligeramente diferente al estándar (6371000)
- Ambas funciones retornan cadenas de texto en lugar de números flotantes
- Estas funciones son utilizadas en el proceso de creación de redes de tráfico para Vissim