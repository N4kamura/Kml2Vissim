# KML2VISSIM & KML2SUMO

KML2VISSIM es una aplicación de escritorio que convierte archivos KML (que contienen polígonos cerrados) en redes viales y fondos georreferenciados compatibles con **PTV VISSIM** (.inpx) y **Eclipse SUMO** (.net.xml, .poly.xml, .sumocfg).

La aplicación extrae la red vial de OpenStreetMap delimitada estrictamente al área del polígono definido y descarga mosaicos satelitales en alta resolución para el fondo.

## Requisitos del Sistema

- Windows 10 o superior (64-bit)
- 500 MB de espacio en disco disponible
- Conexión a Internet (para descargar imágenes satelitales y datos de OSM)
- Para SUMO: Eclipse SUMO instalado en el sistema (opcional, solo si se selecciona el destino SUMO).

> **Nota:** La aplicación ya no requiere GDAL ni variables de entorno adicionales (`PROJ_LIB`). Todo el procesamiento cartográfico y de imágenes se realiza de manera nativa.

## Uso de la Aplicación

1. Ejecute el archivo `Kml2Vissim.exe`
2. En la interfaz gráfica:
   - Haga clic en **"Abrir Archivo"** para seleccionar un archivo KML que contenga un polígono cerrado.
   - Seleccione el destino: **Vissim** o **SUMO**.
   - Ingrese un nombre para los archivos de salida (sin extensión).
   - Haga clic en **"Iniciar"** para comenzar el proceso de conversión.

3. La aplicación generará en la misma carpeta del KML:
   - **Para Vissim:** Archivo de red `.inpx` (con fondo satelital integrado) y subcarpeta `background/` con la imagen satelital (`background/FOTO_TOTAL.jpg`). Si por alguna razón la imagen no se puede descargar, se conserva el `.inpx` solo con la red.
   - **Para SUMO:** Red vial (`<nombre>.net.xml`), configuración (`<nombre>.sumocfg`), script lanzador directo (`run_<nombre>.bat`) y subcarpeta `background/` conteniendo polígonos (`<nombre>.poly.xml`), vista (`<nombre>.view.xml`), datos OSM (`<nombre>_bbox.osm.xml`) y decals satelitales georreferenciados.

## Compilación desde el Código Fuente

Para generar el ejecutable autocontenido (`--onefile`) con consola activa:

1. Instale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Compile con PyInstaller:
   ```bash
   pyinstaller --onefile --console --name Kml2Vissim --icon=images/logo.ico --add-data "images;images" main.py
   ```

## Estructura del Proyecto

```
Kml2Vissim/
├── main.py                   # Punto de entrada de la aplicación
├── Kml2Vissim.spec           # Configuración de PyInstaller
├── requirements.txt          # Dependencias de Python
├── comando_pyinstaller.txt   # Comando de compilación
├── interface/                # Interfaz gráfica PyQt5
│   ├── ui.py
│   └── ui.ui
├── src/
│   ├── background/          # Descarga y georreferenciación de fondos satelitales
│   └── network/             # Generación de redes VISSIM y SUMO
├── images/                  # Ícono y plantilla base XML
└── README.md
```

## Créditos

Desarrollado por Nakamura  
Versión: 4.0.1