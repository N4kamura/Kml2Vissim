from geographic_tools import *
from get_background import GoogleMapDownloader  
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import osmnx as ox
import shutil
import os
import pandas as pd

def vissimcreator(kml_path,inpx_file_name) -> None:
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

    x_min, x_max, y_min, y_max = bbox.CalculatePolygonBounds(polygon_coordinates)

    [x_min,y_min] = Convert_to_mercator(x_min,y_min)
    [x_max,y_max] = Convert_to_mercator(x_max,y_max)

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
    template_path   = "images/vacio.xml"
    new_path        = "images/template_processing.xml"

    shutil.copyfile(template_path,new_path)

    tree2 = ET.parse(new_path)
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
    final_route = directory + '/' + inpx_file_name + '.inpx'

    et.write(final_route,xml_declaration=True)
    #et.write("test.inpx",xml_declaration=True)

    print("FIN DE CREACIÓN DE REDES EN VISSIM")