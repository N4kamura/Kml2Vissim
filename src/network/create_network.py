from src.background.utils.geographic_tools import *
from src.background.utils.google_map_downloader import GoogleMapDownloader  
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import osmnx as ox
import shutil
import os
import pandas as pd
from src.network.utils.coordinate_tools import *

def vissim_creator(kml_path,inpx_file_name) -> None:
    #------------------------------------------------------------------------------#
    # Reading kml files to obtain coordinates #
    #------------------------------------------------------------------------------#

    tree0 = ET.parse(kml_path)
    root0 = tree0.getroot()
    coordinates_element = root0.find('.//{http://www.opengis.net/kml/2.2}coordinates')

    if coordinates_element is not None:
        coordinates_text = coordinates_element.text
        coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
        polygon_coordinates = [(float(lon), float(lat)) for lon, lat in coordinates_list]
        polygon = Polygon(polygon_coordinates)

    bbox = GoogleMapDownloader(polygon_coordinates,20)

    x_min, x_max, y_min, y_max = bbox.calculate_polygon_bounds(polygon_coordinates)

    [x_min,y_min] = convert_to_mercator(x_min,y_min)
    [x_max,y_max] = convert_to_mercator(x_max,y_max)

    reference_point = ((x_min+x_max)/2,(y_min+y_max)/2)

    #Extracting data from OSM
    OSM_DATA = ox.graph_from_polygon(polygon,network_type='all',retain_all=True,truncate_by_edge=True)

    nodes,edges = ox.graph_to_gdfs(OSM_DATA)
    #When is number: string, when is nan: float <- None
    
    #Tratamiento de los geometry
    edges['coordinates'] = edges['geometry'].apply(process_geometry)
    #edges['utm_coordinates_sin_desfase']=edges['coordinates'].apply(convert_coordinates_to_utm)
    edges['utm_coordinates']=edges['coordinates'].apply(convert_coordinates_to_utm)
    
    #Tratamiento de los nodes
    #nodes.drop(['street_count','geometry'], axis=1, inplace=True)
    nodes.reset_index(inplace=True)
    nodes.rename(columns={'level_0':'osmid'},inplace=True)

    #Tratamiento de los edges
    #edges.drop(['length', 'geometry', 'maxspeed','coordinates'], axis=1, inplace=True)
    edges.reset_index(inplace=True)
    edges.rename(columns={'level_0':'u','level_1':'v','level_2':'key'}, inplace=True)

    #Combinación de dataframes
    edges = edges.merge(nodes[['osmid','y','x']],left_on='u',right_on='osmid',how='left')
    edges.rename(columns={'y':'u_y','x':'u_x'},inplace=True)
    edges.drop(['osmid_y'],axis=1,inplace=True)

    edges = edges.merge(nodes[['osmid','y','x']],left_on='v',right_on='osmid',how='left')
    edges.rename(columns={'y':'v_y','x':'v_x'},inplace=True)
    edges.drop(['osmid'],axis=1,inplace=True)

    #Convertion to UTM
    edges['u_y_UTM'] = edges.apply(lambda row: convert_to_mercator_lat(row['u_y']),axis=1)
    edges['u_x_UTM'] = edges.apply(lambda row: convert_to_mercator_lon(row['u_x']),axis=1)
    edges['v_y_UTM'] = edges.apply(lambda row: convert_to_mercator_lat(row['v_y']),axis=1)
    edges['v_x_UTM'] = edges.apply(lambda row: convert_to_mercator_lon(row['v_x']),axis=1)

    #Convertion to String
    #I remove .astype(float)
    edges['u_y_UTM'] = (edges['u_y_UTM']).astype(str)
    edges['u_x_UTM'] = (edges['u_x_UTM']).astype(str)
    edges['v_y_UTM'] = (edges['v_y_UTM']).astype(str)
    edges['v_x_UTM'] = (edges['v_x_UTM']).astype(str)

    edges.drop(['u_y','u_x','v_y','v_x'],axis=1,inplace=True)

    #Eliminación de footway y pedestrian
    edges = edges[~((edges['highway']=='pedestrian') | (edges['highway']=='footway') | (edges['highway']=='cycleway'))]

    #CONVERSIÓN DEL DATAFRAME A INPX
    #Rutas
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    template_path   = os.path.join(base_dir, "images", "vacio.xml")

    tree2 = ET.parse(template_path)
    root2 = tree2.getroot()

    #INGRESO DE PUNTO DE REFERENCIA: netPara
    netPara = root2.find(".//netPara")
    refPointMap = ET.SubElement(netPara,'refPointMap')
    refPointMap.set('x',str(reference_point[0])) #Cambiar por centreoide bbox
    refPointMap.set('y',str(reference_point[1])) #Camibiar por centroiude bbox

    refPointNet = ET.SubElement(netPara,'refPointNet')
    refPointNet.set('x',str(reference_point[0]))
    refPointNet.set('y',str(reference_point[1]))

    #INGRESO DE DATOS DE GEOMETRIA
    links = ET.SubElement(root2,'links')
    #ANALIZE: LINKS 27 & 19
    count = 1
    #print(edges.columns)
    """ for i in range(3):
        print(edges.iloc[i]) """
    for i in range(len(edges)):
        #Escritura de los datos propios del link
        link=ET.SubElement(links,'link')
        link.set('assumSpeedOncom','60')
        link.set('costPerKm','0')
        link.set('direction','ALL')
        link.set('displayType','1')
        link.set('emergStopDist','5')
        link.set('gradient','0')
        link.set('hasOvtLn','false')
        link.set('isPedArea','false')
        link.set('level','1')
        link.set('linkBehavType','1')
        link.set('linkEvalAct','true')
        link.set('linkEvalSegLen','10')
        link.set('lnChgDist','200')
        link.set('lnChgDistIsPerLn','false')
        link.set('lnChgEvalAct','true')
        link.set('lookAheadDistOvt','500')
        link.set('mesoFollowUpGap','0')
        link.set('mesoSpeed','50')
        link.set('mesoSpeedModel','VEHICLEBASED')
        if isinstance(edges['name'].iloc[i],list):
            name_value=edges['name'].iloc[i]
            if len(name_value)>0:
                link.set('name',name_value[0])
            else:
                link.set('name','')
        elif pd.notna(edges['name'].iloc[i]):
            link.set('name',edges['name'].iloc[i])
        else:
            link.set('name','')
        link.set('no',str(count))
        link.set('ovtOnlyPT','false')
        link.set('ovtSpeedFact','1.3')
        link.set('showClsfValues','true')
        link.set('showLinkBar','true')
        link.set('showVeh','true')
        link.set('surch1','0')
        link.set('surch2','0')
        link.set('thickness','0')
        link.set('vehRecAct','true')

        #INGRESO DE GEOMETRIA DEL EDGE
        geometry = ET.SubElement(link,'geometry')
        points3D = ET.SubElement(geometry,'points3D')
        #Nodo de inicio
        point3D = ET.SubElement(points3D,'point3D')
        point3D.set('x',edges.iloc[i]['u_x_UTM'])
        point3D.set('y',edges.iloc[i]['u_y_UTM'])
        #Nodo de fin
        point3D = ET.SubElement(points3D,'point3D')
        point3D.set('x',edges.iloc[i]['v_x_UTM'])
        point3D.set('y',edges.iloc[i]['v_y_UTM'])

        #INGRESO DE LANES
        lanes = ET.SubElement(link, 'lanes')
        for _ in range(2):
            lane = ET.SubElement(lanes,'lane')
            lane.set('wdith','3.3')

        """ if edges['oneway'].iloc[i]==False:
            divisor = 2
        else:
            divisor = 1

        if int(edges['lanes'].iloc[i])%2==0:
            number_lanes = int(int(edges['lanes'].iloc[i])/divisor)

        lanes = ET.SubElement(link,'lanes')
        for _ in range(number_lanes):
            lane = ET.SubElement(lanes,'lane')
            lane.set('width','3.3') """

        """ if isinstance(edges['lanes'].iloc[i],str):
            number_lanes = int(edges['lanes'].iloc[i])
            for _ in range(number_lanes):
                lane = ET.SubElement(lanes,'lane')
                lane.set('width','3.3')
        else:
            for _ in range(2):
                lane = ET.SubElement(lanes,'lane')
                lane.set('width','3.3') """
        '''if isinstance(edges['lanes'].iloc[i],list):
            number_lanes = int(edges['lanes'].iloc[i])
            if len(number_lanes)>0:
                i_for = int(number_lanes[0])
                if i_for == 4 and edges['oneway'].iloc[i]==True:
                    for j in range(i_for//divisor//2):
                        lane = ET.SubElement(lanes,'lane')
                        lane.set('width','3.3')
                else:
                    for j in range(i_for//divisor):
                        lane = ET.SubElement(lanes,'lane')
                        lane.set('width','3.3')
            else:
                for j in range(2):
                    lane = ET.SubElement(lanes,'lane')
                    lane.set('width','3.3')
        elif pd.notna(edges['lanes'].iloc[i]):
            number_lanes = int(edges['lanes'].iloc[i])
            if number_lanes == 4 and edges['oneway'].iloc[i]==True:
                for j in range(number_lanes//divisor//2):
                    lane = ET.SubElement(lanes,'lane')
                    lane.set('width','3.3')
            else:
                for j in range(number_lanes//divisor):
                    lane = ET.SubElement(lanes,'lane')
                    lane.set('width','3.3')'''

        count +=1

    ET.indent(root2)
    et = ET.ElementTree(root2)

    #TRATAMIENTO DE LA RUTA DESTINO:
    original_path = kml_path
    directory, _ = os.path.split(original_path)
    background_dir = os.path.join(directory, 'background')
    os.makedirs(background_dir, exist_ok=True)
    final_route = os.path.join(directory, inpx_file_name + '.inpx')

    et.write(final_route, xml_declaration=True)

    print("FIN DE CREACIÓN DE REDES EN VISSIM")


def download_osm_data(min_lon: float, min_lat: float, max_lon: float, max_lat: float, output_file: str) -> bool:
    """
    Descarga datos de OpenStreetMap (vías y polígonos/áreas) directamente dentro de los límites
    de coordenadas del KML (rectángulo delimitador).
    Primero intenta con la API oficial de OSM (api.openstreetmap.org/api/0.6/map), que descarga
    únicamente el área acotada sin desbordar relaciones a toda la ciudad, y tiene respaldo en Overpass.
    """
    import requests

    # 1. Intentar con la API oficial de OSM (rápida, precisa y estrictamente limitada a la bbox del KML)
    osm_api_url = f"https://api.openstreetmap.org/api/0.6/map?bbox={min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"
    headers = {'User-Agent': 'Mozilla/5.0 Kml2Vissim/2.0'}
    try:
        print(f"Descargando datos OSM delimitados desde OSM API ({min_lon:.4f},{min_lat:.4f} a {max_lon:.4f},{max_lat:.4f})...")
        resp = requests.get(osm_api_url, headers=headers, timeout=25)
        if resp.status_code == 200 and b"<osm" in resp.content[:1000]:
            with open(output_file, "wb") as f:
                f.write(resp.content)
            print(f"Datos OSM descargados exitosamente desde API oficial ({len(resp.content)} bytes).")
            return True
    except Exception as e:
        print(f"OSM API no disponible ({e}), intentando servidores Overpass...")

    # 2. Respaldo: Overpass API con consulta acotada a vías y sus nodos (sin relaciones extensas de transporte)
    xml_query = f"""<osm-script timeout="60">
<union>
  <query type="way">
    <bbox-query n="{max_lat:.6f}" s="{min_lat:.6f}" w="{min_lon:.6f}" e="{max_lon:.6f}"/>
  </query>
  <recurse type="way-node"/>
</union>
<print mode="body"/>
</osm-script>"""

    overpass_headers = {
        'Content-Type': 'application/xml',
        'User-Agent': 'Eclipse SUMO osmGet.py (sumo@dlr.de)',
        'Accept-Encoding': 'gzip'
    }

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    for url in endpoints:
        try:
            print(f"Descargando datos OSM desde {url}...")
            resp = requests.post(url, data=xml_query.encode('utf-8'), headers=overpass_headers, timeout=25)
            if resp.status_code == 200 and b"<osm" in resp.content[:1000]:
                with open(output_file, "wb") as f:
                    f.write(resp.content)
                print(f"Datos OSM descargados exitosamente ({len(resp.content)} bytes).")
                return True
        except Exception as e:
            print(f"Error conectando a {url}: {e}. Intentando siguiente servidor...")
            continue

    return False


def sumo_creator(kml_path: str, output_name: str) -> None:
    """
    Crea la red (.net.xml) y las áreas/polígonos (.poly.xml) de SUMO
    a partir del polígono definido en un archivo KML, usando netconvert y polyconvert de SUMO.
    No descarga imágenes, ya que estas son gestionadas por kml2sumo_decal.
    """
    import subprocess

    # 1. Leer archivo KML para obtener las coordenadas del polígono
    tree0 = ET.parse(kml_path)
    root0 = tree0.getroot()
    coordinates_element = root0.find('.//{http://www.opengis.net/kml/2.2}coordinates')

    if coordinates_element is None:
        print("No se encontraron coordenadas en el KML")
        return

    coordinates_text = coordinates_element.text
    coordinates_list = [coord.strip().split(',')[:2] for coord in coordinates_text.split()]
    polygon_coordinates = [(float(lon), float(lat)) for lon, lat in coordinates_list]

    min_lon = min(lon for lon, lat in polygon_coordinates)
    max_lon = max(lon for lon, lat in polygon_coordinates)
    min_lat = min(lat for lon, lat in polygon_coordinates)
    max_lat = max(lat for lon, lat in polygon_coordinates)

    directory, _ = os.path.split(os.path.abspath(kml_path))
    background_dir = os.path.join(directory, 'background')
    os.makedirs(background_dir, exist_ok=True)

    # 2. Localizar instalación de SUMO y sus ejecutables
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        for candidate in [
            r"D:\Programs\Eclipse\Sumo",
            r"C:\Program Files (x86)\Eclipse\Sumo",
            r"C:\Program Files\Eclipse\Sumo",
        ]:
            if os.path.isdir(candidate):
                sumo_home = candidate
                break

    netconvert_bin = None
    polyconvert_bin = None
    if sumo_home:
        cand_nc = os.path.join(sumo_home, "bin", "netconvert.exe" if os.name == "nt" else "netconvert")
        cand_pc = os.path.join(sumo_home, "bin", "polyconvert.exe" if os.name == "nt" else "polyconvert")
        if os.path.isfile(cand_nc):
            netconvert_bin = cand_nc
        if os.path.isfile(cand_pc):
            polyconvert_bin = cand_pc

    if not netconvert_bin:
        netconvert_bin = shutil.which("netconvert")
    if not polyconvert_bin:
        polyconvert_bin = shutil.which("polyconvert")

    if not netconvert_bin or not polyconvert_bin:
        raise RuntimeError("No se encontraron netconvert y polyconvert. Verifique que SUMO esté instalado y en el PATH.")

    # 3. Descargar datos OSM acotados al rectángulo del KML (en carpeta background)
    osm_file = os.path.join(background_dir, f"{output_name}_bbox.osm.xml")
    ok = download_osm_data(min_lon, min_lat, max_lon, max_lat, osm_file)
    if not ok or not os.path.isfile(osm_file):
        raise RuntimeError("No se pudo descargar el mapa desde OpenStreetMap.")

    # 4. Configurar typemaps de SUMO
    typemapdir = os.path.join(sumo_home, "data", "typemap") if sumo_home else ""
    typemaps = {
        "net": os.path.join(typemapdir, "osmNetconvert.typ.xml"),
        "poly": os.path.join(typemapdir, "osmPolyconvert.typ.xml"),
        "urban": os.path.join(typemapdir, "osmNetconvertUrbanDe.typ.xml"),
        "pedestrians": os.path.join(typemapdir, "osmNetconvertPedestrians.typ.xml"),
        "bicycles": os.path.join(typemapdir, "osmNetconvertBicycle.typ.xml"),
    }

    typefiles = [
        typemaps["net"],
        typemaps["urban"],
        typemaps["pedestrians"],
        typemaps["bicycles"],
    ]
    typefiles = [f for f in typefiles if os.path.isfile(f)]

    # 5. Ejecutar netconvert para generar la red (.net.xml) acotada a la frontera del KML
    bbox_geo = f"{min_lon:.6f},{min_lat:.6f},{max_lon:.6f},{max_lat:.6f}"
    net_file = os.path.join(directory, f"{output_name}.net.xml")
    net_cmd = [
        netconvert_bin,
        "--osm-files", osm_file,
        "-o", net_file,
        "--keep-edges.in-geo-boundary", bbox_geo,
        "--geometry.remove",
        "--ramps.guess",
        "--junctions.join",
        "--tls.guess-signals",
        "--tls.discard-simple",
        "--tls.join",
        "--tls.default-type", "actuated",
        "--crossings.guess",
        "--osm.sidewalks",
        "--osm.bike-access",
        "--output.original-names",
        "--output.street-names"
    ]
    if typefiles:
        net_cmd += ["-t", ",".join(typefiles)]

    print(f"Ejecutando netconvert para crear {output_name}.net.xml delimitado...")
    res_net = subprocess.run(net_cmd, capture_output=True, text=True, cwd=directory)
    if res_net.returncode != 0:
        print("Advertencia en netconvert:", res_net.stderr)

    # 6. Ejecutar polyconvert para generar los polígonos (.poly.xml) en background/
    poly_file = os.path.join(background_dir, f"{output_name}.poly.xml")
    poly_cmd = [
        polyconvert_bin,
        "--osm-files", osm_file,
        "-n", net_file,
        "-o", poly_file,
        "--prune.in-net",
        "--osm.keep-full-type",
        "--osm.merge-relations", "1"
    ]
    if os.path.isfile(typemaps["poly"]):
        poly_cmd += ["--type-file", typemaps["poly"]]

    print(f"Ejecutando polyconvert para crear {output_name}.poly.xml...")
    res_poly = subprocess.run(poly_cmd, capture_output=True, text=True, cwd=directory)
    if res_poly.returncode != 0:
        print("Advertencia en polyconvert:", res_poly.stderr)

    # 7. Generar archivo de vista (.view.xml) en background/
    view_file = os.path.join(background_dir, f"{output_name}.view.xml")
    decals_filename = f"{output_name}_decals.xml"
    with open(view_file, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<viewsettings>\n')
        f.write('    <scheme name="real world"/>\n')
        f.write('    <delay value="20"/>\n')
        f.write(f'    <include href="{decals_filename}"/>\n')
        f.write('</viewsettings>\n')

    # 8. Generar archivo de configuración (.sumocfg) referenciando background/
    cfg_file = os.path.join(directory, f"{output_name}.sumocfg")
    net_rel = f"{output_name}.net.xml"
    poly_rel = f"background/{output_name}.poly.xml"
    view_rel = f"background/{output_name}.view.xml"
    poly_exists = os.path.isfile(poly_file)

    with open(cfg_file, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">\n')
        f.write('    <input>\n')
        f.write(f'        <net-file value="{net_rel}"/>\n')
        if poly_exists:
            f.write(f'        <additional-files value="{poly_rel}"/>\n')
        f.write('    </input>\n')
        f.write('    <gui_only>\n')
        f.write(f'        <gui-settings-file value="{view_rel}"/>\n')
        f.write('    </gui_only>\n')
        f.write('</configuration>\n')

    # 9. Generar script bat para ejecución directa
    run_bat = os.path.join(directory, f"run_{output_name}.bat")
    with open(run_bat, "w", encoding="utf-8") as f:
        f.write(f'@echo off\nsumo-gui -c "{output_name}.sumocfg"\n')

    print(f"RED Y POLÍGONOS DE SUMO GENERADOS EXITOSAMENTE EN: {directory}")