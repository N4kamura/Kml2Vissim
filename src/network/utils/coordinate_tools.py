import math

RADIUS = 6390602.66473445
A = 1.0030289588831154
B = 1.003076128580129

def convert_to_mercator_lat(lat):
    lat_mer = RADIUS*math.log(math.tan(0.5*(lat*math.pi/180/A+math.pi/2)))

    return str(lat_mer)

def convert_to_mercator_lon(lon):
    lon_mer = lon*RADIUS*math.pi/180/B

    return str(lon_mer)