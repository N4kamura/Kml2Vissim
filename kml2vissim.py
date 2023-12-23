from PyQt5.QtWidgets import QMainWindow, QLineEdit, QApplication, QPushButton,QLabel,QFileDialog
from PyQt5 import uic

import osmnx as ox
import math
import shutil
import xml.etree.ElementTree as ET
import pandas as pd
import os
from shapely.geometry import Polygon
import requests
import numpy as np
import cv2
import subprocess

#DEFINICIÓN DE CLASES Y FUNCIONES

#VALORES GLOBALES
#Estos valores se han calibrado gracias a scipy
RADIUS = 6390602.66473445
A = 1.0030289588831154
B = 1.003076128580129

class GoogleMapDownloader:
    def __init__(self,points,zoom):
        self.points=points
        self.zoom=zoom

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

        return x_min, x_max, y_min, y_max
    
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

def vissimcreator(kml_path,inpx_file_name):
    #CÓDIGO PRINCIPAL

    # Convierte las coordenadas en un objeto Polygon
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

    G6 = ox.graph_from_polygon(polygon,network_type='all',retain_all=True,truncate_by_edge=True)
    
    #CORRECCIONES
    #delta_x = 9393.4+210-5-3
    #delta_y = 1485.5+40-8-3+3
    delta_x = 0
    delta_y = 0

    nodes,edges = ox.graph_to_gdfs(G6)

    #Tratamiento de los geometry
    edges['coordinates'] = edges['geometry'].apply(process_geometry)
    edges['utm_coordinates_sin_desfase']=edges['coordinates'].apply(convert_coordinates_to_utm)
    edges['utm_coordinates']=edges['utm_coordinates_sin_desfase'].apply(apply_desfase,args=(delta_x,delta_y))

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

    #Conversion a UTM
    edges['u_y_UTM'] = edges.apply(lambda row: convert_to_mercator_lat(row['u_y']),axis=1)
    edges['u_x_UTM'] = edges.apply(lambda row: convert_to_mercator_lon(row['u_x']),axis=1)
    edges['v_y_UTM'] = edges.apply(lambda row: convert_to_mercator_lat(row['v_y']),axis=1)
    edges['v_x_UTM'] = edges.apply(lambda row: convert_to_mercator_lon(row['v_x']),axis=1)

    edges['u_y_UTM'] = (edges['u_y_UTM'].astype(float) + delta_y).astype(str)
    edges['u_x_UTM'] = (edges['u_x_UTM'].astype(float) + delta_x).astype(str)
    edges['v_y_UTM'] = (edges['v_y_UTM'].astype(float) + delta_y).astype(str)
    edges['v_x_UTM'] = (edges['v_x_UTM'].astype(float) + delta_x).astype(str)

    edges.drop(['u_y','u_x','v_y','v_x'],axis=1,inplace=True)

    #Eliminación de footway y pedestrian
    edges = edges[~((edges['highway']=='pedestrian') | (edges['highway']=='footway') | (edges['highway']=='cycleway'))]

    #CONVERSIÓN DEL DATAFRAME A INPX
    #Rutas
    template_path   = "vacio.xml"
    new_path        = "template_processing.xml"

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

    count = 1

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
        '''if edges['oneway'].iloc[i]==False:
            divisor = 2
        else:
            divisor = 1'''

        lanes = ET.SubElement(link,'lanes')
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
        lane = ET.SubElement(lanes,'lane')
        lane.set('width','3.3')
        lane = ET.SubElement(lanes,'lane')
        lane.set('width','3.3')

        count +=1

    ET.indent(root2)
    et = ET.ElementTree(root2)

    #TRATAMIENTO DE LA RUTA DESTINO:
    original_path = kml_path
    directory, _ = os.path.split(original_path)
    final_route = directory + '/' + inpx_file_name + '.inpx'

    et.write(final_route,xml_declaration=True)

    print("FIN DE CREACIÓN DE REDES EN VISSIM")

def shape2png_function(kml_file,inpx_file_name):
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

    #Extracción de coordenadas de las esquinas de los TILEs
    count = 0

    #MANIPULACION DE PATH PARA SUBIR LAS FOTOGRAFIAS
    directory, _ = os.path.split(kml_file)
    path = directory + '/' + 'FOTOGRAFIAS_'+inpx_file_name
    os.makedirs(path)

    for i in range(min_x,max_x+1):
        for j in range(min_y,max_y+1):
            print(f"Descargando imagenes: {round((count+1)/(max_x+1-min_x)*(max_y+1-min_y),0)}%")
            tile.generateImage(i,j,count=count,path=path)
            count += 1

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

def convert_background(kml_file,inpx_file_name):
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

    ###CONVERSION A FORMATO .tif
    final_route2, _ = os.path.split(kml_file)
    input_png = final_route2 + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.png'
    output_tif = final_route2 + '/FOTOGRAFIAS_'+inpx_file_name+'/FOTO_TOTAL.tif'

    #Coordenadas para transformar a .TIF
    lon1, lat1 = definitive_upper_left[0],definitive_upper_left[1]
    lon2, lat2 = definitive_bottom_right[0],definitive_bottom_right[1]

    comando = f"gdal_translate -of GTiff -a_srs EPSG:4326 -a_ullr {lon1} {lat1} {lon2} {lat2} {input_png} {output_tif}"
    proceso = subprocess.Popen(comando, shell=True)
    proceso.wait()

    #ESCRITURA EXTRA EN ARCHIVO DE INPX
    archivo_inpx = final_route2 +'\\'+ inpx_file_name + '.inpx'
    
    tree = ET.parse(archivo_inpx)
    root = tree.getroot()

    #APLICACION DE DESFASE
    coordBL[0] = str(float(coordBL[0]))
    coordBL[1] = str(float(coordBL[1]))

    coordTR[0] = str(float(coordTR[0]))
    coordTR[1] = str(float(coordTR[1]))

    #INGRESO DE BACKGROUND
    backgroundImages = ET.SubElement(root,'backgroundImages')
    backgroundImage = ET.SubElement(backgroundImages,'backgroundImage')
    backgroundImage.set('anisoFilt','true')
    backgroundImage.set('level','1')
    backgroundImage.set('no','1')
    #AQUÍ TAMBIÉN DEBO COLOCAR LA RUTA DEL .TIF ya creado.
    backgroundImage.set('pathFilename',output_tif)
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
    et.write(final_route2+"\\"+inpx_file_name+"_Background"+".inpx",xml_declaration=True)
    print("FIN DE ESCRITURA DE ARCHIVO .INPX CON BACKGROUND INCLUIDO")

class UI(QMainWindow):
    def __init__(self):
        super(UI,self).__init__()

        #Load the file
        uic.loadUi("shape2vissim.ui",self)

        #Buttons
        self.pushButton     = self.findChild(QPushButton,"pushButton")
        self.pushButton_2   = self.findChild(QPushButton,"pushButton_2")

        #Line Edits
        self.lineEdit       = self.findChild(QLineEdit,"lineEdit")
        self.lineEdit_2     = self.findChild(QLineEdit,"lineEdit_2")

        #Label
        self.label_7        = self.findChild(QLabel,"label_7")

        #Click the dropdown box
        self.pushButton.clicked.connect(self.clicker)
        self.pushButton_2.clicked.connect(self.save)

    def clicker(self):
        #Open File Dialog
        self.kml_file, _ = QFileDialog.getOpenFileName(self,"Busqueda de archivos KML","c:\\","KML Files (*.kml)")

        #Output file name to screen
        if self.kml_file: #It's true
            self.lineEdit.setText(self.kml_file)

    def save(self):
        #Saving file name
        self.kml_name = self.lineEdit_2.text()

        kml_file = self.kml_file
        inpx_file_name = self.kml_name

        self.label_7.setText("Cargando")

        #Creador de la red
        vissimcreator(kml_file,inpx_file_name)

        self.label_7.setText("Rutas creadas")

        #Descargador de la red
        shape2png_function(kml_file,inpx_file_name)

        self.label_7.setText("Foto descargada")

        #Agregador del background a la red
        convert_background(kml_file,inpx_file_name)

        self.label_7.setText("¡LISTO!")

        print("FIN DEL PROGRAMA")

def main():
    app = QApplication([])
    window = UI()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()