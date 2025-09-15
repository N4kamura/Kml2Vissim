# Documentación de interface/ui.py

## Descripción
Este archivo contiene la implementación de la interfaz de usuario generada automáticamente a partir del archivo `interface/ui.ui` utilizando PyQt5 UI code generator. Define la clase `Ui_MainWindow` que configura todos los elementos visuales de la ventana principal de la aplicación.

## Advertencia Importante
Este archivo fue generado automáticamente. Cualquier cambio manual realizado en este archivo se perderá cuando se ejecute `pyuic5` nuevamente. No edite este archivo a menos que sepa lo que está haciendo.

## Clases

### Ui_MainWindow(object)
Clase que define la estructura y elementos de la interfaz de usuario de la ventana principal.

#### Métodos

- `setupUi(self, MainWindow)`: Configura todos los elementos visuales de la ventana principal, incluyendo:
  - Botones (`pushButton`, `pushButton_2`)
  - Campos de texto (`lineEdit`, `lineEdit_2`)
  - Etiquetas (`label`, `label_2`, `label_3`, `label_5`, `label_7`)
  - Área de texto enriquecido (`textBrowser`)
  - Configuración de tamaño y propiedades de la ventana

- `retranslateUi(self, MainWindow)`: Establece el texto traducido para todos los elementos de la interfaz, incluyendo:
  - Título de la ventana
  - Textos de los botones
  - Etiquetas descriptivas
  - Instrucciones en el área de texto

## Elementos de la Interfaz

1. **Campo de selección de archivo**:
   - `lineEdit`: Muestra la ruta del archivo KML seleccionado
   - `pushButton`: Botón para abrir el diálogo de selección de archivos
   - `label`: Etiqueta "Ruta:"

2. **Campo de nombre de archivo**:
   - `lineEdit_2`: Campo para ingresar el nombre del archivo de salida
   - `label_2`: Etiqueta "Nombre del archivo:"
   - `pushButton_2`: Botón "Iniciar" para comenzar el procesamiento

3. **Información adicional**:
   - `label_3`: Etiqueta con información sobre tipos de archivos válidos
   - `label_5`: Créditos y versión del software
   - `textBrowser`: Área con instrucciones de uso

## Generación
Este archivo se genera automáticamente a partir de `interface/ui.ui` usando:
```bash
pyuic5 interface/ui.ui -o interface/ui.py
```

## Dependencias
- PyQt5