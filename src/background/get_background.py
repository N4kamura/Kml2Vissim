import os
import math
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import cv2
import numpy as np
from src.background.utils.geographic_tools import *
from src.background.utils.google_map_downloader import GoogleMapDownloader
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

    #Teselas que intersectan el polígono (borde e interior). El resto quedará en blanco.
    polygon_lonlat = Polygon([(lon, lat) for lat, lon in polygon_coordinates])
    tiles_to_download = sorted(tile.tiles_for_polygon(polygon_lonlat))

    #MANIPULACION DE PATH PARA SUBIR LAS FOTOGRAFIAS
    directory, _ = os.path.split(kml_file)
    path = directory + '/' + 'FOTOGRAFIAS_'+inpx_file_name
    os.makedirs(path, exist_ok=True)

    image_width     = 256
    image_height    = 256
    num_columns = max_x-min_x + 1
    num_rows    = max_y-min_y + 1

    #Lienzo blanco: las teselas que no tocan el polígono se quedan en blanco
    grid_image = np.full((image_height * num_rows, image_width * num_columns, 3), 255, dtype=np.uint8)

    #Descarga únicamente las teselas que intersectan el polígono
    with tqdm(total=len(tiles_to_download), desc="Descargando imagenes") as pbar:
        for count, (x, y) in enumerate(tiles_to_download):
            content = tile.download_image(x, y)
            if content is not None:
                image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is not None:
                    if image.shape[0] != image_height or image.shape[1] != image_width:
                        image = cv2.resize(image, (image_width, image_height))
                    row = y - min_y
                    col = x - min_x
                    start_row   = row*image_height
                    end_row     = start_row + image_height
                    start_col   = col*image_width
                    end_col     = start_col + image_width
                    grid_image[start_row:end_row,start_col:end_col,:] = image
            pbar.update(1)
            if (count + 1) % 30 == 0:
                time.sleep(1)

    cv2.imwrite(os.path.join(path,'FOTO_TOTAL.png'),grid_image)
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

    upper_left_coord = tile.get_tile_bounds(min_x, min_y)    #[north,south,west,east]
    bottom_right_coord = tile.get_tile_bounds(max_x, max_y)  #[north,south,west,east]
    
    definitive_upper_right = (bottom_right_coord[3], upper_left_coord[0])
    definitive_bottom_left = (upper_left_coord[2], bottom_right_coord[1])

    #Para Vissim
    coordTR = convert_to_mercator(definitive_upper_right[0], definitive_upper_right[1])
    coordBL = convert_to_mercator(definitive_bottom_left[0], definitive_bottom_left[1])

    ###CONVERSION DIRECTA A FORMATO .jpg (sin GDAL; la georreferencia va en el .inpx)
    folder_path, _ = os.path.split(kml_file)
    input_png = folder_path + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.png'
    output_jpg = folder_path + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.jpg'

    imagen = cv2.imread(input_png)
    if imagen is None:
        print(f"No se pudo leer la imagen de fondo: {input_png}")
        return
    cv2.imwrite(output_jpg, imagen, [cv2.IMWRITE_JPEG_QUALITY, 90])

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


WEB_MERCATOR_RADIUS = 6378137.0
SOURCE_TILE_PIXELS = 256

def ground_resolution(zoom, lat) -> float:
    # Metros reales por píxel de una tesela Web Mercator a la latitud dada.
    return (2 * math.pi * WEB_MERCATOR_RADIUS) / (SOURCE_TILE_PIXELS * (1 << zoom)) * math.cos(math.radians(lat))

def latlon_to_utm(lat, lon):
    try:
        from pyproj import Proj
        zone = int((lon + 180) / 6) + 1
        south = lat < 0
        p = Proj(proj='utm', zone=zone, ellps='WGS84', south=south)
        return p(lon, lat)
    except Exception:
        a = 6378137.0
        f = 1 / 298.257223563
        k0 = 0.9996
        e2 = f * (2 - f)
        e_prime2 = e2 / (1 - e2)
        zone = int((lon + 180) / 6) + 1
        lon0 = (zone - 1) * 6 - 180 + 3
        lon0_rad = math.radians(lon0)
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        N = a / math.sqrt(1 - e2 * math.sin(lat_rad) ** 2)
        T = math.tan(lat_rad) ** 2
        C = e_prime2 * math.cos(lat_rad) ** 2
        A = math.cos(lat_rad) * (lon_rad - lon0_rad)
        M = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat_rad
                 - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * lat_rad)
                 + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * lat_rad)
                 - (35 * e2 ** 3 / 3072) * math.sin(6 * lat_rad))
        x = k0 * N * (A + (1 - T + C) * A ** 3 / 6 + (5 - 18 * T + T ** 2 + 72 * C - 58 * e_prime2) * A ** 5 / 120) + 500000.0
        y = k0 * (M + N * math.tan(lat_rad) * (A ** 2 / 2 + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24
                                              + (61 - 58 * T + T ** 2 + 600 * C - 330 * e_prime2) * A ** 6 / 720))
        if lat < 0:
            y += 10000000.0
        return x, y

def kml2sumo_decal(kml_file, output_name, tile_size=4096, jpg_quality=95) -> None:
    tree = ET.parse(kml_file)
    root = tree.getroot()

    coordinates_element = root.find('.//{http://www.opengis.net/kml/2.2}coordinates')
    if coordinates_element is None:
        print("No se encontraron coordenadas en el KML")
        return

    coordinates_text = coordinates_element.text
    coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
    polygon_coordinates = [(float(lat), float(lon)) for lon, lat in coordinates_list]
    polygon = Polygon(polygon_coordinates)
    vertices_polygon = list(polygon.exterior.coords)

    tile = GoogleMapDownloader(vertices_polygon, zoom=20)
    vertices = [tile.get_XY(lat, lon) for lat, lon in vertices_polygon]
    min_x, max_x, min_y, max_y = tile.calculate_polygon_bounds(vertices)

    polygon_lonlat = Polygon([(lon, lat) for lat, lon in polygon_coordinates])
    tiles_to_download = sorted(tile.tiles_for_polygon(polygon_lonlat))

    # Dimensiones en píxeles del mosaico completo
    num_columns = max_x - min_x + 1
    num_rows = max_y - min_y + 1
    width_px = num_columns * SOURCE_TILE_PIXELS
    height_px = num_rows * SOURCE_TILE_PIXELS

    # El tamaño de bloque debe ser múltiplo del tamaño de tesela para no cortar teselas
    tile_size = max(SOURCE_TILE_PIXELS, int(math.ceil(tile_size / SOURCE_TILE_PIXELS)) * SOURCE_TILE_PIXELS)

    # Carpeta de salida (junto al KML): DECALS_<nombre>/
    directory, _ = os.path.split(kml_file)
    out_dir = os.path.join(directory, 'DECALS_' + output_name)
    os.makedirs(out_dir, exist_ok=True)

    # Intentar cargar la red SUMO si ya fue generada para asegurar alineación perfecta de coordenadas
    net_path = os.path.join(directory, output_name + ".net.xml")
    net = None
    if os.path.exists(net_path):
        try:
            import sumolib
            net = sumolib.net.readNet(net_path)
        except Exception:
            net = None

    # Agrupar teselas fuente por bloque de salida
    out_cols = (width_px + tile_size - 1) // tile_size
    out_rows = (height_px + tile_size - 1) // tile_size
    groups = {}
    for (x, y) in tiles_to_download:
        px = (x - min_x) * SOURCE_TILE_PIXELS
        py = (y - min_y) * SOURCE_TILE_PIXELS
        out_col = px // tile_size
        out_row = py // tile_size
        groups.setdefault((out_row, out_col), []).append(
            (x, y, px - out_col * tile_size, py - out_row * tile_size)
        )

    total_px = (1 << tile.zoom) * SOURCE_TILE_PIXELS

    def world_pixel_to_lonlat(wx, wy):
        lon = (wx / total_px) * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * wy / total_px)))
        lat = math.degrees(lat_rad)
        return lon, lat

    decals = []
    count = 0
    with tqdm(total=len(tiles_to_download), desc="Descargando imagenes") as pbar:
        for out_row in range(out_rows):
            for out_col in range(out_cols):
                if (out_row, out_col) not in groups:
                    continue

                block_width_px = min(tile_size, width_px - out_col * tile_size)
                block_height_px = min(tile_size, height_px - out_row * tile_size)
                canvas = np.full((block_height_px, block_width_px, 3), 255, dtype=np.uint8)

                for (x, y, offset_x, offset_y) in groups.get((out_row, out_col), []):
                    content = tile.download_image(x, y)
                    if content is not None:
                        image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if image is not None:
                            if image.shape[0] != SOURCE_TILE_PIXELS or image.shape[1] != SOURCE_TILE_PIXELS:
                                image = cv2.resize(image, (SOURCE_TILE_PIXELS, SOURCE_TILE_PIXELS))
                            canvas[offset_y:offset_y + SOURCE_TILE_PIXELS, offset_x:offset_x + SOURCE_TILE_PIXELS, :] = image
                    count += 1
                    pbar.update(1)
                    if count % 30 == 0:
                        time.sleep(1)

                filename = f"decal_r{out_row}_c{out_col}.jpg"
                cv2.imwrite(os.path.join(out_dir, filename), canvas, [cv2.IMWRITE_JPEG_QUALITY, jpg_quality])

                # Coordenadas geográficas de las esquinas y centro del bloque
                world_px_left = min_x * SOURCE_TILE_PIXELS + out_col * tile_size
                world_py_top = min_y * SOURCE_TILE_PIXELS + out_row * tile_size
                world_px_right = world_px_left + block_width_px
                world_py_bottom = world_py_top + block_height_px

                world_px_center = (world_px_left + world_px_right) / 2.0
                world_py_center = (world_py_top + world_py_bottom) / 2.0

                lon_west, lat_north = world_pixel_to_lonlat(world_px_left, world_py_top)
                lon_east, lat_south = world_pixel_to_lonlat(world_px_right, world_py_bottom)
                lon_center, lat_center = world_pixel_to_lonlat(world_px_center, world_py_center)

                # 1. Archivo World (.jgw) en WGS84 para posicionamiento automático en SUMO (sumo-gui y netedit)
                dx_deg = (lon_east - lon_west) / block_width_px
                dy_deg = (lat_south - lat_north) / block_height_px  # Negativo
                x_center_tl = lon_west + dx_deg / 2.0
                y_center_tl = lat_north + dy_deg / 2.0

                jgw_filename = f"decal_r{out_row}_c{out_col}.jgw"
                with open(os.path.join(out_dir, jgw_filename), 'w', encoding='utf-8') as jgw_file:
                    jgw_file.write(f"{dx_deg:.12f}\n")
                    jgw_file.write("0.000000000000\n")
                    jgw_file.write("0.000000000000\n")
                    jgw_file.write(f"{dy_deg:.12f}\n")
                    jgw_file.write(f"{x_center_tl:.12f}\n")
                    jgw_file.write(f"{y_center_tl:.12f}\n")

                # 2. Coordenadas georreferenciadas para SUMO viewsettings XML
                if net is not None:
                    nw = net.convertLonLat2XY(lon_west, lat_north)
                    se = net.convertLonLat2XY(lon_east, lat_south)
                    utm_center_x = (nw[0] + se[0]) / 2.0
                    utm_center_y = (nw[1] + se[1]) / 2.0
                    block_width_m = abs(se[0] - nw[0])
                    block_height_m = abs(nw[1] - se[1])
                else:
                    utm_center_x, utm_center_y = latlon_to_utm(lat_center, lon_center)
                    utm_west, _ = latlon_to_utm(lat_center, lon_west)
                    utm_east, _ = latlon_to_utm(lat_center, lon_east)
                    _, utm_north = latlon_to_utm(lat_north, lon_center)
                    _, utm_south = latlon_to_utm(lat_south, lon_center)
                    block_width_m = abs(utm_east - utm_west)
                    block_height_m = abs(utm_north - utm_south)

                decals.append((filename, utm_center_x, utm_center_y, block_width_m, block_height_m))

    # Archivo de decals de SUMO (viewsettings)
    xml_path = os.path.join(out_dir, output_name + '_decals.xml')
    with open(xml_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_file.write('<viewsettings>\n')
        for (filename, center_x, center_y, width_m, height_m) in decals:
            xml_file.write(
                f'    <decal file="{filename}" centerX="{center_x:.4f}" centerY="{center_y:.4f}" '
                f'width="{width_m:.4f}" height="{height_m:.4f}" layer="0"/>\n'
            )
        xml_file.write('</viewsettings>\n')

    print(f"DECALS DE SUMO GENERADOS EXITOSAMENTE EN: {out_dir}")