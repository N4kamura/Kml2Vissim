import requests
import math
import os
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import cv2
import numpy as np
from geographic_tools import *
import subprocess
import time
from geopy.distance import geodesic

class GoogleMapDownloader:
    def __init__(self,points,zoom):
        self.points=points
        self.zoom=zoom

    def Calculate_box_use(self,coordinates):
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
        print(x_min,x_max,y_min,y_max)
        lat_min=x_min
        lat_max=x_max
        lon_min=y_min
        lon_max=y_max
        print("geografica\tLatitud",lat_min,lat_max,"\tLongtud",lon_min,lon_max)
        Lat_M_min,Long_M_min=Convert_to_mercator(lon_min,lat_min)
        Lat_M_max,Long_M_max=Convert_to_mercator(lon_max,lat_max)
        print("Latitud",Lat_M_min,Lat_M_max,"\tLongtud",Long_M_min,Long_M_max)
        ancho=Long_M_max-Long_M_min
        alto=Lat_M_max-Lat_M_min

        # # Calcular ancho (Este-Oeste)
        # lat_promedio = (lat_min + lat_max) / 2
        # punto_oeste = (lat_promedio, lon_min)
        # punto_este = (lat_promedio, lon_max)
        # ancho = geodesic(punto_oeste, punto_este).meters
        
        # # Calcular alto (Norte-Sur)
        # lon_promedio = (lon_min + lon_max) / 2
        # punto_sur = (lat_min, lon_promedio)
        # punto_norte = (lat_max, lon_promedio)
        # alto = geodesic(punto_sur, punto_norte).meters

        width = ancho
        Hight = alto


        print("funcion",width,Hight)
        return width, Hight



    def CalculatePolygonBounds(self,coordinates):
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

        lat_promedio = (y_min + y_max) / 2
        delta_x = x_max - x_min
        delta_y = y_max - y_min
        width = delta_x*111319.9 * math.cos(math.radians(lat_promedio))

        Hight = delta_y*111319.9

        #print("funcion",width,Hight)
        return x_min, x_max, y_min, y_max
        #return x_min, x_max, y_min, y_max
    
    def getTileBounds(self,x,y):
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
    
    def getXY(self,lat,lng):
        tile_size=256 #Tamaño en píxeles del Tile, dejarlo tal como esta.
        numTiles=1 << self.zoom

        point_x=(tile_size/ 2 + lng* tile_size / 360.0) * numTiles // tile_size
        sin_y=math.sin(lat* (math.pi / 180.0))
        point_y=((tile_size / 2) + 0.5 * math.log((1+sin_y)/(1-sin_y)) * -(tile_size / (2 * math.pi))) * numTiles // tile_size

        return int(point_x),int(point_y)
    
    def generateImage(self,x,y,count,path):
        headers={'User-Agent':'MyApp/1.0'}
        nombre_archivo=f"FOTO_{count}.png"
        url='https://mt0.google.com/vt/lyrs=s&?x=' + str(x) + '&y=' + str(y) + '&z=' + str(self.zoom)

        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            with open(os.path.join(path,nombre_archivo),'wb') as f:
                f.write(response.content)
                #print(f'La imagen {nombre_archivo} se ha guardado exitosamente')
        else:
            print(f"El error es este: {response.status_code}")

def shape2png_function(kml_file,inpx_file_name) -> None:
    tree = ET.parse(kml_file)
    root = tree.getroot()

    coordinates_element = root.find('.//{http://www.opengis.net/kml/2.2}coordinates')

    if coordinates_element is not None:
        coordinates_text = coordinates_element.text
        coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
        polygon_coordinates = [(float(lat), float(lon)) for lon, lat in coordinates_list]
        polygon = Polygon(polygon_coordinates)
        vertices_polygon = list(polygon.exterior.coords)
        print("vertices_polygon",vertices_polygon)
    tile=GoogleMapDownloader(vertices_polygon,zoom=20)
    vertices=[]

    #En este bucle obtengo las coordenadas en TILE
    for i in range(len(vertices_polygon)):
        vertices.append(tile.getXY(vertices_polygon[i][0],vertices_polygon[i][1]))
        print("vertices",vertices)
    #Valores de los límites de los TILES
    min_x,max_x,min_y,max_y=tile.CalculatePolygonBounds(vertices)
    #width_pluss,Hight_pluss = tile.seccion_box(vertices)
    #print("para vissim",width_pluss,Hight_pluss)

    #Extracción de coordenadas de las esquinas de los TILEs
    count = 0

    #MANIPULACION DE PATH PARA SUBIR LAS FOTOGRAFIAS
    directory, _ = os.path.split(kml_file)
    path = directory + '/' + 'FOTOGRAFIAS_'+inpx_file_name
    os.makedirs(path)

    for i in range(min_x,max_x+1):
        for j in range(min_y,max_y+1):
            print(f"Descargando imagenes: {round((count+1)/(max_x+1-min_x)/(max_y+1-min_y)*100,0)}%")
            tile.generateImage(i,j,count=count,path=path)
            count += 1
            if count%30 == 0:
                time.sleep(1)

    #PROCESO DE MATCH DE IMÁGENES
    path = path +"\\"
    image_width     = 256
    image_height    = 256

    num_images = ((max_x-min_x+1))*((max_y-min_y+1))
    num_columns = max_x-min_x+1
    num_rows    = max_y-min_y+1

    grid_image = np.zeros((image_height * num_rows, image_width * num_columns, 3), dtype=np.uint8)
    count = 0
    for col in range(num_columns):
        for row in range(num_rows):
            if count >= num_images:
                break
            print(f"Cargando y procesando fotos: {round((count+1)/num_images*100,0)}%")
            image_path = f"FOTO_{count}.png"
            image = cv2.imread(path+image_path)
            start_row   = row*image_height
            end_row     = start_row + image_height
            start_col   = col*image_width
            end_col     = start_col + image_width

            grid_image[start_row:end_row,start_col:end_col,:] = image
            count += 1

    cv2.imwrite(path+'\\FOTO_TOTAL.png',grid_image)
    print("FOTOGRAFIAS UNIDAS EXITOSAMENTE")

def convert_background(kml_file,inpx_file_name) -> None:
    tree = ET.parse(kml_file)
    root = tree.getroot()

    coordinates_element = root.find('.//{http://www.opengis.net/kml/2.2}coordinates')

    if coordinates_element is not None:
        coordinates_text = coordinates_element.text
        coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
        polygon_coordinates = [(float(lat), float(lon)) for lon, lat in coordinates_list]
        polygon = Polygon(polygon_coordinates)
        vertices_polygon = list(polygon.exterior.coords)
    
    tile=GoogleMapDownloader(vertices_polygon,zoom=20)
    vertices=[]

    #En este bucle obtengo las coordenadas en TILE
    for i in range(len(vertices_polygon)):
        vertices.append(tile.getXY(vertices_polygon[i][0],vertices_polygon[i][1]))

    #Valores de los límites de los TILES
    min_x,max_x,min_y,max_y=tile.CalculatePolygonBounds(vertices)
    #width_pluss,Hight_pluss = tile.seccion_box(vertices)


    width_pluss,Hight_pluss = tile.Calculate_box_use(vertices_polygon)
    print("para vissim_sumando",width_pluss,Hight_pluss)

    #Extracción de coordenadas de las esquinas de los TILEs
    esquina_sup_izq = (min_x,min_y)
    esquina_inf_der = (max_x,max_y)

    upper_left_coord = tile.getTileBounds(esquina_sup_izq[0],esquina_sup_izq[1])    #[north,south,west,east]
    bottom_right_coord = tile.getTileBounds(esquina_inf_der[0],esquina_inf_der[1])  #[north,south,west,east]
    
    definitive_upper_left = (upper_left_coord[2],upper_left_coord[0]) #(lon,lat)
    definitive_bottom_right = (bottom_right_coord[3],bottom_right_coord[1]) #(lon,lat)

    definitive_upper_right = (bottom_right_coord[3],upper_left_coord[0])
    definitive_bottom_left = (upper_left_coord[2],bottom_right_coord[1])

    #Para Vissim
    coordTR = Convert_to_mercator(definitive_upper_right[0],definitive_upper_right[1])
    coordBL = Convert_to_mercator(definitive_bottom_left[0],definitive_bottom_left[1])
    print("Coordenadas para Vissim dtR:",coordTR,"de :",definitive_upper_right[0],definitive_upper_right[1])
    coordTR2 = (coordBL[0]+Hight_pluss,coordBL[1]+width_pluss)
    print("Coordenadas para Vissim dtR2:",coordTR2,"de :",definitive_upper_right[0]+width_pluss,definitive_upper_right[1]+Hight_pluss)
    print("para vissim_sumando",width_pluss,Hight_pluss)

    #coordTR = convert_coords(definitive_upper_right[0],definitive_upper_right[1])
    #coordBL = convert_coords(definitive_bottom_left[0],definitive_bottom_left[1])

    #print("Coordenadas para Vissim dtR:",coordTR,"de :",definitive_upper_right[0],definitive_upper_right[1])
    #print("Coordenadas para Vissim dBL:",coordBL,"de :",definitive_bottom_left[0],definitive_bottom_left[1])

    ###CONVERSION A FORMATO .tif
    final_route2, _ = os.path.split(kml_file)
    input_png = final_route2 + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.png'
    output_tif = final_route2 + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.tif'
    output_jpg = final_route2 + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.jpg'

    #Coordenadas para transformar a .TIF
    lon1, lat1 = definitive_upper_left[0],definitive_upper_left[1]
    lon2, lat2 = definitive_bottom_right[0],definitive_bottom_right[1]

    comando = f'gdal_translate -of GTiff -a_srs EPSG:4326 -a_ullr {lon1} {lat1} {lon2} {lat2} "{input_png}" "{output_tif}"'
    proceso = subprocess.Popen(comando, shell=True)
    proceso.wait()
    comando2 = f'gdal_translate -of JPEG -co QUALITY=90 "{output_tif}" "{output_jpg}"'
    proceso = subprocess.Popen(comando2, shell=True)
    proceso.wait()

    #Eliminación de archivos innecesarios:
    photos_path = os.path.join(final_route2,'FOTOGRAFIAS_'+inpx_file_name)
    photos_list = os.listdir(photos_path)
    photos_list = [photo for photo in photos_list if not photo.endswith('.jpg')]
    for photo in photos_list:
        delete_file = os.path.join(photos_path, photo)
        os.remove(delete_file)

    #ESCRITURA EXTRA EN ARCHIVO DE INPX
    archivo_inpx = final_route2 +'\\'+ inpx_file_name + '.inpx'
    
    tree = ET.parse(archivo_inpx)
    root = tree.getroot()

    #APLICACION DE DESFASE
    #print("aplicación",coordBL[0],coordBL[1],coordTR[0],coordTR[1])

    coordBL[0] = str(float(coordBL[0]))
    coordBL[1] = str(float(coordBL[1]))
    coordTR3=[None,None]
    coordTR3[0] = str(float(coordTR2[0]))
    coordTR3[1] = str(float(coordTR2[1]))
    print("aplicación",coordBL[0],coordBL[1],coordTR3[0],coordTR3[1])

    #INGRESO DE BACKGROUND
    backgroundImages = ET.SubElement(root,'backgroundImages')
    backgroundImage = ET.SubElement(backgroundImages,'backgroundImage')
    backgroundImage.set('anisoFilt','true')
    backgroundImage.set('level','1')
    backgroundImage.set('no','1')
    #AQUÍ TAMBIÉN DEBO COLOCAR LA RUTA DEL .TIF ya creado.
    backgroundImage.set('pathFilename',f'./FOTOGRAFIAS_{inpx_file_name}/FOTO_TOTAL.jpg')
    backgroundImage.set('res3D','HIGH')
    backgroundImage.set('tileSizeHoriz','512')
    backgroundImage.set('tileSizeVert','512')
    backgroundImage.set('type','FROMFILE')
    backgroundImage.set('zOffset','-0.2')
    #VISSIM 23
    coordBL_inpx = ET.SubElement(backgroundImage,'coordBL')
    coordBL_inpx.set('x',coordBL[0])
    coordBL_inpx.set('y',coordBL[1])
    coordTR_inpx = ET.SubElement(backgroundImage,'coordTR')
    coordTR_inpx.set('x',coordTR3[0])
    coordTR_inpx.set('y',coordTR3[1])
    #VISSIM 10
    posBL_inpx = ET.SubElement(backgroundImage,'posBL')
    posBL_inpx.set('x',coordBL[0])
    posBL_inpx.set('y',coordBL[1])
    posTR_inpx = ET.SubElement(backgroundImage,'posTR')
    posTR_inpx.set('x',coordTR3[0])
    posTR_inpx.set('y',coordTR3[1])
    
    ET.indent(root)
    et = ET.ElementTree(root)
    et.write(final_route2+"\\"+inpx_file_name+"_Background"+".inpx",xml_declaration=True)
    print("FIN DE ESCRITURA DE ARCHIVO .INPX CON BACKGROUND INCLUIDO")