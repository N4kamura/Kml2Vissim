import math
from pyproj import Transformer

#RADIUS = 6390602.66473445
#A = 1.0030289588831154
#B = 1.003076128580129

#RADIUS = 6378137
RADIUS = 6371000
A=1
B=1


# Function to convert coordinates from WGS84 to Web Mercator (EPSG:3857)
def convert_coords(lon, lat):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
    x, y = transformer.transform(lat, lon)
    return [x, y]

def Convert_to_mercator(lon,lat): #Convierte de Geográficas a MERCATOR.
    lon_mer = lon*RADIUS*math.pi/180/B
    lat_mer = RADIUS*math.log(math.tan(0.5*(lat*math.pi/180/A+math.pi/2)))

    return [lon_mer,lat_mer]

def convert_to_mercator_lat(lat):
    lat_mer = RADIUS*math.log(math.tan(0.5*(lat*math.pi/180/A+math.pi/2)))

    return str(lat_mer)

def convert_to_mercator_lon(lon):
    lon_mer = lon*RADIUS*math.pi/180/B

    return str(lon_mer)

def convert_coordinates_to_utm(coordinates):
    utm_coordinates = [(lon*RADIUS*math.pi/180/B,RADIUS*math.log(math.tan(0.5*(lat*math.pi/180/A+math.pi/2)))) for lon,lat in coordinates]
    return utm_coordinates

def process_geometry(wkt):
    wkt = str(wkt)
    wkt = wkt.replace('LINESTRING (','').replace(')','')
    coordinate_pairs = wkt.split(', ')
    coordinates = [tuple(map(float,pair.split())) for pair in coordinate_pairs]
    return coordinates

def apply_desfase(coordinates,desfase_x,desfase_y):
    return [(lon + desfase_x, lat + desfase_y) for lon, lat in coordinates]