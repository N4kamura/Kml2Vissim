from src.background.utils.geographic_tools import *
from shapely.geometry import box
import requests
import os
import math

class GoogleMapDownloader:
    def __init__(self,points,zoom):
        self.points=points
        self.zoom=zoom

    def calculate_polygon_bounds(self, coordinates) -> list[float, float, float, float]:
        if not coordinates:
            return None, None, None, None
        
        x_min = x_max = coordinates [0][0]
        y_min = y_max = coordinates [0][1]

        for x, y in coordinates:
            if x<x_min:
                x_min = x
            elif x>x_max:
                x_max = x
            if y<y_min:
                y_min = y
            elif y>y_max:
                y_max = y

        return x_min, x_max, y_min, y_max
    
    def get_tile_bounds(self,x,y) -> list[float, float, float, float]:
        numTiles = 1 << self.zoom

        #Calculo de longitud
        lon_deg = x/numTiles*360 - 180

        #Calculo de latitud
        lat_rad = math.atan(math.sinh(math.pi*(1-2*y/numTiles)))
        lat_deg = math.degrees(lat_rad)

        #Coordenadas de las esquinas.
        north   = lat_deg
        south   = lat_deg - 360 / numTiles
        west    = lon_deg
        east    = lon_deg + 360 / numTiles

        return [north,south,west,east]
    
    def get_XY(self,lat,lng):
        tile_size=256 #Tamaño en píxeles del Tile, dejarlo tal como esta.
        numTiles=1 << self.zoom

        point_x=(tile_size/ 2 + lng* tile_size / 360.0) * numTiles // tile_size
        sin_y=math.sin(lat* (math.pi / 180.0))
        point_y=((tile_size / 2) + 0.5 * math.log((1+sin_y)/(1-sin_y)) * -(tile_size / (2 * math.pi))) * numTiles // tile_size

        return int(point_x),int(point_y)
    
    def world_pixel(self,lat,lng) -> tuple[float,float]:
        tile_size=256
        numTiles=1 << self.zoom

        world_x=(lng + 180.0) / 360.0 * numTiles * tile_size
        lat_rad=math.radians(lat)
        world_y=(1 - math.log(math.tan(lat_rad) + 1/math.cos(lat_rad)) / math.pi) / 2 * numTiles * tile_size

        return world_x,world_y

    def lat_to_tile_y(self,lat) -> int:
        numTiles=1 << self.zoom
        lat_rad=math.radians(lat)
        world_y=(1 - math.log(math.tan(lat_rad) + 1/math.cos(lat_rad)) / math.pi) / 2 * numTiles

        return int(math.floor(world_y))

    def tiles_for_polygon(self,polygon) -> set:
        # polygon es un shapely.Polygon en orden (lon,lat)
        numTiles=1 << self.zoom
        min_lon,min_lat,max_lon,max_lat=polygon.bounds

        min_x=self.get_XY(min_lat,min_lon)[0]
        max_x=self.get_XY(max_lat,max_lon)[0]
        min_y=self.lat_to_tile_y(max_lat)
        max_y=self.lat_to_tile_y(min_lat)

        epsilon=1e-9
        tiles=set()
        for x in range(min_x,max_x + 1):
            lon_west=x / numTiles * 360 - 180
            lon_east=(x + 1) / numTiles * 360 - 180
            column=box(lon_west,min_lat - epsilon,lon_east,max_lat + epsilon)
            intersection=polygon.intersection(column)
            if intersection.is_empty:
                continue
            inter_min_lat=intersection.bounds[1]
            inter_max_lat=intersection.bounds[3]
            top_y=max(self.lat_to_tile_y(inter_max_lat),min_y)
            bottom_y=min(self.lat_to_tile_y(inter_min_lat),max_y)
            for y in range(top_y,bottom_y + 1):
                if 0 <= y < numTiles:
                    tiles.add((x,y))

        return tiles

    def download_image(self,x,y):
        headers={'User-Agent':'MyApp/1.0'}
        url='https://mt0.google.com/vt/lyrs=s&?x=' + str(x) + '&y=' + str(y) + '&z=' + str(self.zoom)

        try:
            response=requests.get(url,headers=headers)
        except requests.RequestException as error:
            print(f"El error es este: {error}")
            return None

        if response.status_code == 200:
            return response.content
        else:
            print(f"El error es este: {response.status_code}")
            return None

    def generate_image(self,x,y,count,path,filename=None):
        content=self.download_image(x,y)
        if content is None:
            return
        nombre_archivo=filename if filename else f"FOTO_{count}.png"
        with open(os.path.join(path,nombre_archivo),'wb') as f:
            f.write(content)
            # print(f'La imagen {nombre_archivo} se ha guardado exitosamente')