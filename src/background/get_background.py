import os
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import cv2
import numpy as np
from src.background.utils.geographic_tools import *
from src.background.utils.google_map_downloader import GoogleMapDownloader
import subprocess
import time
from geopy.distance import geodesic
from tqdm import tqdm

def kml2png_function(kml_file,inpx_file_name) -> None:
    tree = ET.parse(kml_file)
    root = tree.getroot()

    coordinates_element = root.find('.//{http://www.opengis.net/kml/2.2}coordinates')

    if coordinates_element is not None:
        coordinates_text = coordinates_element.text
        coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
        polygon_coordinates = [(float(lat), float(lon)) for lon, lat in coordinates_list]
        polygon = Polygon(polygon_coordinates)
        vertices_polygon = list(polygon.exterior.coords)

    tile = GoogleMapDownloader(vertices_polygon, zoom=20)
    vertices=[]

    #En este bucle obtengo las coordenadas en TILE
    for i in range(len(vertices_polygon)):
        vertices.append(tile.get_XY(vertices_polygon[i][0],vertices_polygon[i][1]))

    #Valores de los límites de los TILES
    min_x, max_x, min_y, max_y = tile.calculate_polygon_bounds(vertices)

    #Extracción de coordenadas de las esquinas de los TILEs
    count = 0

    #MANIPULACION DE PATH PARA SUBIR LAS FOTOGRAFIAS
    directory, _ = os.path.split(kml_file)
    path = directory + '/' + 'FOTOGRAFIAS_'+inpx_file_name
    os.makedirs(path)

    # Calculate total number of images to download
    total_images = (max_x - min_x + 1) * (max_y - min_y + 1)
    count = 0
    
    with tqdm(total=total_images, desc="Descargando imagenes") as pbar:
        for i in range(min_x, max_x + 1):
            for j in range(min_y, max_y + 1):
                tile.generate_image(i, j, count, path)
                count += 1
                pbar.update(1)  # Update progress bar by 1 for each image
                if count % 30 == 0:
                    time.sleep(1)

    #PROCESO DE MATCH DE IMÁGENES
    path = path +"\\"
    image_width     = 256
    image_height    = 256

    num_images = ((max_x-min_x+1))*((max_y-min_y+1))
    num_columns = max_x-min_x + 1
    num_rows    = max_y-min_y + 1

    grid_image = np.zeros((image_height * num_rows, image_width * num_columns, 3), dtype=np.uint8)
    count = 0
    # Use tqdm with total number of images for more granular progress tracking
    with tqdm(total=num_images, desc="Cargando y procesando fotos") as pbar:
        for col in range(num_columns):
            for row in range(num_rows):
                if count >= num_images:
                    break
                image_path = f"FOTO_{count}.png"
                image = cv2.imread(path+image_path)
                start_row   = row*image_height
                end_row     = start_row + image_height
                start_col   = col*image_width
                end_col     = start_col + image_width

                grid_image[start_row:end_row,start_col:end_col,:] = image
                count += 1
                pbar.update(1)  # Update progress bar by 1 for each image processed

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
    
    tile=GoogleMapDownloader(vertices_polygon, zoom=20)
    vertices=[]

    #En este bucle obtengo las coordenadas en TILE
    for i in range(len(vertices_polygon)):
        vertices.append(tile.get_XY(vertices_polygon[i][0],vertices_polygon[i][1]))

    #Valores de los límites de los TILES
    min_x, max_x, min_y, max_y = tile.calculate_polygon_bounds(vertices)

    width, height = tile.polygon_dimensions(vertices_polygon)

    upper_left_coord = tile.get_tile_bounds(min_x, min_y)    #[north,south,west,east]
    bottom_right_coord = tile.get_tile_bounds(max_x, max_y)  #[north,south,west,east]
    
    definitive_upper_left = (upper_left_coord[2], upper_left_coord[0]) #(lon,lat)
    # definitive_upper_right = (bottom_right_coord[3], upper_left_coord[0])

    definitive_bottom_right = (bottom_right_coord[3], bottom_right_coord[1]) #(lon,lat)
    definitive_bottom_left = (upper_left_coord[2], bottom_right_coord[1])

    #Para Vissim
    # coordTR = convert_to_mercator(definitive_upper_right[0], definitive_upper_right[1])
    coordBL = convert_to_mercator(definitive_bottom_left[0], definitive_bottom_left[1])
    coordTR = (coordBL[0] + height, coordBL[1] + width)

    ###CONVERSION A FORMATO .tif
    folder_path, _ = os.path.split(kml_file)
    input_png = folder_path + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.png'
    output_tif = folder_path + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.tif'
    output_jpg = folder_path + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.jpg'

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
    photos_path = os.path.join(folder_path, 'FOTOGRAFIAS_'+inpx_file_name)
    photos_list = os.listdir(photos_path)
    photos_list = [photo for photo in photos_list if not photo.endswith('.jpg')]
    for photo in photos_list:
        delete_file = os.path.join(photos_path, photo)
        os.remove(delete_file)

    #ESCRITURA EXTRA EN ARCHIVO DE INPX
    archivo_inpx = folder_path +'\\'+ inpx_file_name + '.inpx'
    
    tree = ET.parse(archivo_inpx)
    root = tree.getroot()

    #APLICACION DE DESFASE
    coordBL = [str(float(coordinate)) for coordinate in coordBL]
    coordTR = [str(float(coordinate)) for coordinate in coordTR]

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
    coordTR_inpx.set('x',coordTR[0])
    coordTR_inpx.set('y',coordTR[1])
    #VISSIM 10
    posBL_inpx = ET.SubElement(backgroundImage,'posBL')
    posBL_inpx.set('x',coordBL[0])
    posBL_inpx.set('y',coordBL[1])
    posTR_inpx = ET.SubElement(backgroundImage,'posTR')
    posTR_inpx.set('x',coordTR[0])
    posTR_inpx.set('y',coordTR[1])
    
    ET.indent(root)
    et = ET.ElementTree(root)
    et.write(folder_path + "\\"+inpx_file_name+"_Background"+".inpx",xml_declaration=True)
    print("FIN DE ESCRITURA DE ARCHIVO .INPX CON BACKGROUND INCLUIDO")