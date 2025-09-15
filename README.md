# KML2VISSIM

KML2VISSIM es una aplicación de escritorio que convierte archivos KML (que contienen datos de polígonos) en archivos de red VISSIM (.inpx) con imágenes de fondo. La aplicación extrae datos de red vial de OpenStreetMap dentro del área del polígono definido y crea una red compatible con VISSIM con imágenes satelitales de fondo.

## Descarga del Ejecutable

Puede descargar el ejecutable compilado más reciente desde el siguiente enlace:
[[dist y GDAL binaries](https://drive.google.com/drive/folders/1hL3qcZVxykCKT0bBuPsH0y7epI_PA7o9?usp=sharing)]

## Requisitos del Sistema

- Windows 7 o superior (64-bit)
- 500 MB de espacio en disco disponible
- Conexión a Internet (para descargar imágenes de mapas y datos de OSM)
- Tener en las variables de entorno para el usuario la carpeta de QGIS\share\proj como variable PROJ_LIB, esto permite la utilización de GDAL.

## Instalación

1. Descargue el archivo ejecutable desde el enlace proporcionado
2. Ejecute el instalador o simplemente extraiga el archivo .exe en una carpeta de su elección
3. ¡Listo! No se requiere instalación adicional ya que todas las dependencias están incluidas

## Uso de la Aplicación

1. Ejecute el archivo `kml2vissim_v3.0.3.exe`
2. En la interfaz gráfica:
   - Haga clic en "Abrir Archivo" para seleccionar un archivo KML que contenga un polígono
   - Ingrese un nombre para los archivos de salida (sin extensión)
   - Haga clic en "Iniciar" para comenzar el proceso de conversión

3. La aplicación generará:
   - Un archivo de red VISSIM (.inpx)
   - Una imagen de fondo (FOTO_TOTAL.jpg) en una subcarpeta
   - Un archivo VISSIM con fondo incluido (_Background.inpx)

## Funcionamiento

1. **Procesamiento KML**: La aplicación lee el archivo KML y extrae las coordenadas del polígono
2. **Imágenes Satelitales**: Descarga mosaicos de imágenes satelitales para el área definida
3. **Extracción de Datos OSM**: Recupera datos de red vial de OpenStreetMap dentro de los límites del polígono
4. **Conversión de Coordenadas**: Convierte coordenadas geográficas a coordenadas UTM para compatibilidad con VISSIM
5. **Generación de Archivo VISSIM**: Crea el archivo .inpx con enlaces de red y coordenadas adecuadas
6. **Integración de Fondo**: Agrega la imagen satelital como fondo al archivo VISSIM

## GDAL Binaries

Esta aplicación incluye los binarios de GDAL necesarios para su funcionamiento. No es necesario instalar GDAL por separado. Los binarios se encuentran en la carpeta `gdalwin` y se incluyen automáticamente en el ejecutable mediante PyInstaller.

Si necesita los binarios de GDAL por separado, puede descargarlos desde el siguiente enlace:
[[dist y GDAL binaries](https://drive.google.com/drive/folders/1hL3qcZVxykCKT0bBuPsH0y7epI_PA7o9?usp=sharing)]

## Compilación desde el Código Fuente (Opcional)

Si desea compilar la aplicación desde el código fuente:

1. Clone el repositorio:
   ```
   git clone https://github.com/yourusername/Kml2Vissim.git
   cd Kml2Vissim
   ```

2. Instale los paquetes de Python requeridos:
   ```
   pip install -r requirements.txt
   ```

3. Compile el ejecutable usando PyInstaller:
   ```
   pyinstaller main.spec
   ```
   
   O use el comando directamente:
   ```
   pyinstaller --onefile --icon=./images/logo.ico --add-binary "gdalwin/bin/gdal.dll;." --add-binary "gdalwin/bin/gdal/apps/gdal_translate.exe;." ./main.py
   ```

## Estructura del Proyecto

```
Kml2Vissim/
├── kml2vissim_v3.0.3.exe      # Ejecutable compilado (después de la compilación)
├── main.py                   # Punto de entrada de la aplicación
├── main.spec                 # Configuración de PyInstaller
├── requirements.txt          # Dependencias de Python
├── comando_pyinstaller.txt   # Comando de compilación de PyInstaller
├── interface/                # Archivos de interfaz gráfica
│   ├── ui.py                # Código de UI generado
│   └── ui.ui                # Diseño de UI
├── src/
│   ├── background/          # Procesamiento de imágenes de fondo
│   │   └── get_background.py
│   ├── network/             # Creación de red
│   │   └── create_network.py
│   └── utils/               # Funciones de utilidad
├── gdalwin/                 # Binarios de GDAL
├── images/                  # Archivos de plantilla e íconos
└── README.md
```

## Créditos

Desarrollado por Nakamura
Versión: 3.0.3

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo LICENSE para más detalles.