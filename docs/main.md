# Documentación de main.py

## Descripción
Este archivo es el punto de entrada principal de la aplicación. Contiene la clase `Window` que define la interfaz gráfica de usuario (GUI) utilizando PyQt5, y la función `main()` que inicia la aplicación.

## Clases

### Window(QMainWindow)
Clase principal que hereda de `QMainWindow` y define la ventana de la aplicación.

#### Métodos

- `__init__(self)`: Constructor de la clase. Inicializa la interfaz de usuario y conecta los eventos de los botones.
- `openfile(self)`: Abre un diálogo para seleccionar un archivo KML y muestra la ruta en un campo de texto.
- `name(self)`: Obtiene el nombre ingresado por el usuario y ejecuta las funciones de creación de red, conversión de KML a PNG y conversión del fondo.

## Funciones

### main()
Función principal que inicia la aplicación PyQt5, crea una instancia de la ventana y la muestra.

## Uso
Para ejecutar la aplicación, simplemente ejecute este archivo:

```bash
python main.py
```

## Dependencias
- PyQt5
- src.network.create_network
- src.background.get_background
- interface.ui