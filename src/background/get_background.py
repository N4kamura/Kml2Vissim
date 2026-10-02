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

def kml2png_function(kml_file, inpx_file_name) -> bool:
    """
    Descarga mosaicos satelitales y genera background.jpg dentro de la carpeta 'background'.
    Si background.jpg ya existe, no descarga nada y retorna True indicando que fue reutilizado.
    """
    directory, _ = os.path.split(kml_file)
    path = os.path.join(directory, 'background')
    os.makedirs(path, exist_ok=True)
    bg_jpg = os.path.join(path, 'background.jpg')

    # Si ya existe background.jpg, se reutiliza
    if os.path.isfile(bg_jpg):
        print(f"IMAGEN DE FONDO EXISTENTE ENCONTRADA: {bg_jpg}. Se reutilizará.")
        return True

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
    vertices = []

    for i in range(len(vertices_polygon)):
        vertices.append(tile.get_XY(vertices_polygon[i][0], vertices_polygon[i][1]))

    min_x, max_x, min_y, max_y = tile.calculate_polygon_bounds(vertices)

    polygon_lonlat = Polygon([(lon, lat) for lat, lon in polygon_coordinates])
    tiles_to_download = sorted(tile.tiles_for_polygon(polygon_lonlat))

    image_width = 256
    image_height = 256
    num_columns = max_x - min_x + 1
    num_rows = max_y - min_y + 1

    grid_image = np.full((image_height * num_rows, image_width * num_columns, 3), 255, dtype=np.uint8)

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
                    start_row = row * image_height
                    end_row = start_row + image_height
                    start_col = col * image_width
                    end_col = start_col + image_width
                    grid_image[start_row:end_row, start_col:end_col, :] = image
            pbar.update(1)
            if (count + 1) % 30 == 0:
                time.sleep(1)

    cv2.imwrite(bg_jpg, grid_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"IMAGEN DE FONDO GENERADA EXITOSAMENTE EN: {bg_jpg}")
    return False

def convert_background(kml_file, inpx_file_name) -> None:
    folder_path, _ = os.path.split(kml_file)
    background_dir = os.path.join(folder_path, 'background')
    os.makedirs(background_dir, exist_ok=True)
    bg_jpg = os.path.join(background_dir, 'background.jpg')

    if not os.path.isfile(bg_jpg):
        print(f"No se encontró la imagen de fondo: {bg_jpg}. Se mantiene el archivo de red .inpx sin background.")
        return

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
    vertices = []
    for i in range(len(vertices_polygon)):
        vertices.append(tile.get_XY(vertices_polygon[i][0], vertices_polygon[i][1]))

    min_x, max_x, min_y, max_y = tile.calculate_polygon_bounds(vertices)
    upper_left_coord = tile.get_tile_bounds(min_x, min_y)
    bottom_right_coord = tile.get_tile_bounds(max_x, max_y)

    definitive_upper_right = (bottom_right_coord[3], upper_left_coord[0])
    definitive_bottom_left = (upper_left_coord[2], bottom_right_coord[1])

    coordTR = convert_to_mercator(definitive_upper_right[0], definitive_upper_right[1])
    coordBL = convert_to_mercator(definitive_bottom_left[0], definitive_bottom_left[1])

    archivo_inpx = os.path.join(folder_path, inpx_file_name + '.inpx')
    if not os.path.isfile(archivo_inpx):
        print(f"No se encontró el archivo base de red: {archivo_inpx}")
        return

    tree_inpx = ET.parse(archivo_inpx)
    root_inpx = tree_inpx.getroot()

    coordBL = [str(float(coordinate)) for coordinate in coordBL]
    coordTR = [str(float(coordinate)) for coordinate in coordTR]

    backgroundImages = ET.SubElement(root_inpx, 'backgroundImages')
    backgroundImage = ET.SubElement(backgroundImages, 'backgroundImage')
    backgroundImage.set('anisoFilt', 'true')
    backgroundImage.set('level', '1')
    backgroundImage.set('no', '1')
    backgroundImage.set('pathFilename', './background/background.jpg')
    backgroundImage.set('res3D', 'HIGH')
    backgroundImage.set('tileSizeHoriz', '512')
    backgroundImage.set('tileSizeVert', '512')
    backgroundImage.set('type', 'FROMFILE')
    backgroundImage.set('zOffset', '-0.2')
    # VISSIM 23
    coordBL_inpx = ET.SubElement(backgroundImage, 'coordBL')
    coordBL_inpx.set('x', coordBL[0])
    coordBL_inpx.set('y', coordBL[1])
    coordTR_inpx = ET.SubElement(backgroundImage, 'coordTR')
    coordTR_inpx.set('x', coordTR[0])
    coordTR_inpx.set('y', coordTR[1])
    # VISSIM 10
    posBL_inpx = ET.SubElement(backgroundImage, 'posBL')
    posBL_inpx.set('x', coordBL[0])
    posBL_inpx.set('y', coordBL[1])
    posTR_inpx = ET.SubElement(backgroundImage, 'posTR')
    posTR_inpx.set('x', coordTR[0])
    posTR_inpx.set('y', coordTR[1])

    ET.indent(root_inpx)
    et = ET.ElementTree(root_inpx)
    temp_bg_inpx = os.path.join(folder_path, inpx_file_name + "_Background.inpx")
    et.write(temp_bg_inpx, xml_declaration=True)

    if os.path.isfile(temp_bg_inpx):
        if os.path.isfile(archivo_inpx):
            os.remove(archivo_inpx)
        os.replace(temp_bg_inpx, archivo_inpx)
        print(f"FIN DE ESCRITURA DE ARCHIVO .INPX CON BACKGROUND INCLUIDO: {archivo_inpx}")


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

def kml2sumo_decal(kml_file, output_name, jpg_quality=95) -> bool:
    """
    Genera background.jpg georreferenciado para SUMO dentro de la carpeta 'background'.
    Si background.jpg ya existe, lo reutiliza y retorna True indicando que fue reutilizado.
    """
    tree = ET.parse(kml_file)
    root = tree.getroot()

    coordinates_element = root.find('.//{http://www.opengis.net/kml/2.2}coordinates')
    if coordinates_element is None:
        print("No se encontraron coordenadas en el KML")
        return False

    coordinates_text = coordinates_element.text
    coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
    polygon_coordinates = [(float(lat), float(lon)) for lon, lat in coordinates_list]
    polygon = Polygon(polygon_coordinates)
    vertices_polygon = list(polygon.exterior.coords)

    tile = GoogleMapDownloader(vertices_polygon, zoom=20)
    vertices = [tile.get_XY(lat, lon) for lat, lon in vertices_polygon]
    min_x, max_x, min_y, max_y = tile.calculate_polygon_bounds(vertices)

    directory, _ = os.path.split(kml_file)
    out_dir = os.path.join(directory, 'background')
    os.makedirs(out_dir, exist_ok=True)
    bg_image_path = os.path.join(out_dir, 'background.jpg')

    # Dimensiones en píxeles del mosaico completo
    num_columns = max_x - min_x + 1
    num_rows = max_y - min_y + 1
    width_px = num_columns * SOURCE_TILE_PIXELS
    height_px = num_rows * SOURCE_TILE_PIXELS

    # 1. Comprobar si ya existe background.jpg
    reused = os.path.isfile(bg_image_path)
    if not reused:
        polygon_lonlat = Polygon([(lon, lat) for lat, lon in polygon_coordinates])
        tiles_to_download = sorted(tile.tiles_for_polygon(polygon_lonlat))
        canvas = np.full((height_px, width_px, 3), 255, dtype=np.uint8)

        with tqdm(total=len(tiles_to_download), desc="Descargando imagenes") as pbar:
            for count, (x, y) in enumerate(tiles_to_download):
                content = tile.download_image(x, y)
                if content is not None:
                    image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is not None:
                        if image.shape[0] != SOURCE_TILE_PIXELS or image.shape[1] != SOURCE_TILE_PIXELS:
                            image = cv2.resize(image, (SOURCE_TILE_PIXELS, SOURCE_TILE_PIXELS))
                        row = y - min_y
                        col = x - min_x
                        canvas[row * SOURCE_TILE_PIXELS:(row + 1) * SOURCE_TILE_PIXELS, col * SOURCE_TILE_PIXELS:(col + 1) * SOURCE_TILE_PIXELS, :] = image
                pbar.update(1)
                if (count + 1) % 30 == 0:
                    time.sleep(1)

        cv2.imwrite(bg_image_path, canvas, [cv2.IMWRITE_JPEG_QUALITY, jpg_quality])
        print(f"IMAGEN DE FONDO GENERADA EXITOSAMENTE EN: {bg_image_path}")
    else:
        print(f"IMAGEN DE FONDO EXISTENTE ENCONTRADA: {bg_image_path}. Se reutilizará.")

    # 2. Cargar red SUMO para georreferenciación exacta
    net_path = os.path.join(directory, output_name + ".net.xml")
    net = None
    if os.path.exists(net_path):
        try:
            import sumolib
            net = sumolib.net.readNet(net_path)
        except Exception:
            net = None

    total_px = (1 << tile.zoom) * SOURCE_TILE_PIXELS

    def world_pixel_to_lonlat(wx, wy):
        lon = (wx / total_px) * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * wy / total_px)))
        lat = math.degrees(lat_rad)
        return lon, lat

    world_px_left = min_x * SOURCE_TILE_PIXELS
    world_py_top = min_y * SOURCE_TILE_PIXELS
    world_px_right = world_px_left + width_px
    world_py_bottom = world_py_top + height_px

    world_px_center = (world_px_left + world_px_right) / 2.0
    world_py_center = (world_py_top + world_py_bottom) / 2.0

    lon_west, lat_north = world_pixel_to_lonlat(world_px_left, world_py_top)
    lon_east, lat_south = world_pixel_to_lonlat(world_px_right, world_py_bottom)
    lon_center, lat_center = world_pixel_to_lonlat(world_px_center, world_py_center)

    # 3. Archivo World (.jgw) para background.jpg
    dx_deg = (lon_east - lon_west) / width_px
    dy_deg = (lat_south - lat_north) / height_px
    x_center_tl = lon_west + dx_deg / 2.0
    y_center_tl = lat_north + dy_deg / 2.0

    jgw_filename = "background.jgw"
    with open(os.path.join(out_dir, jgw_filename), 'w', encoding='utf-8') as jgw_file:
        jgw_file.write(f"{dx_deg:.12f}\n")
        jgw_file.write("0.000000000000\n")
        jgw_file.write("0.000000000000\n")
        jgw_file.write(f"{dy_deg:.12f}\n")
        jgw_file.write(f"{x_center_tl:.12f}\n")
        jgw_file.write(f"{y_center_tl:.12f}\n")

    # 4. Coordenadas georreferenciadas para SUMO
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

    # 5. Archivo de decals de SUMO apuntando a background.jpg
    xml_path = os.path.join(out_dir, output_name + '_decals.xml')
    with open(xml_path, 'w', encoding='utf-8') as xml_file:
        xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xml_file.write('<viewsettings>\n')
        xml_file.write(
            f'    <decal file="background.jpg" centerX="{utm_center_x:.4f}" centerY="{utm_center_y:.4f}" '
            f'width="{block_width_m:.4f}" height="{block_height_m:.4f}" layer="0"/>\n'
        )
        xml_file.write('</viewsettings>\n')

    print(f"DECALS DE SUMO GENERADOS EXITOSAMENTE EN: {out_dir}")
    return reused