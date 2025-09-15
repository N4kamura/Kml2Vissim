from src.background.utils.geographic_tools import *
import requests
import os

class GoogleMapDownloader:
    def __init__(self,points,zoom):
        self.points=points
        self.zoom=zoom

    def polygon_dimensions(self, coordinates) -> list[float, float]:
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

        lat_min, lat_max = x_min, x_max
        lon_min, lon_max = y_min, y_max

        lat_min_mercator, lon_min_mercator = convert_to_mercator(lon_min, lat_min)
        lat_max_mercator, lon_max_mercator = convert_to_mercator(lon_max, lat_max)

        width = lon_max_mercator - lon_min_mercator
        height = lat_max_mercator - lat_min_mercator

        return width, height

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
    
    def generate_image(self,x,y,count,path):
        headers={'User-Agent':'MyApp/1.0'}
        nombre_archivo=f"FOTO_{count}.png"
        url='https://mt0.google.com/vt/lyrs=s&?x=' + str(x) + '&y=' + str(y) + '&z=' + str(self.zoom)

        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            with open(os.path.join(path,nombre_archivo),'wb') as f:
                f.write(response.content)
                # print(f'La imagen {nombre_archivo} se ha guardado exitosamente')
        else:
            print(f"El error es este: {response.status_code}")