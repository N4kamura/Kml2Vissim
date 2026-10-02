from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from PyQt5 import uic
import warnings
from src.network.create_network import vissim_creator, sumo_creator
from src.background.get_background import kml2png_function, convert_background, kml2sumo_decal
from interface.ui import Ui_MainWindow

warnings.filterwarnings("ignore", category=DeprecationWarning)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.path_file = ""

        self.ui.pushButton.clicked.connect(self.openfile)
        self.ui.pushButton_2.clicked.connect(self.name)

    def openfile(self):
        self.path_file, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo KML", "c:\\", "KML Files (*.kml)")
        if self.path_file:
            self.ui.lineEdit.setText(self.path_file)
    
    def name(self):
        name_file = self.ui.lineEdit_2.text().strip()
        if name_file == '' or name_file == 'Ingresar nombre acá':
            return self.ui.lineEdit_2.setText('Ingresar nombre acá')
        if not self.path_file:
            return self.ui.lineEdit.setText('Seleccione un archivo KML primero')

        self.ui.label_7.setText("Procesando...")
        QApplication.processEvents()

        reused_bg = False
        if self.ui.radioButton_vissim.isChecked():
            vissim_creator(self.path_file, name_file)
            reused_bg = kml2png_function(self.path_file, name_file)
            convert_background(self.path_file, name_file)
            self.ui.label_7.setText("¡Listo (Vissim)!")
        else:
            sumo_creator(self.path_file, name_file)
            reused_bg = kml2sumo_decal(self.path_file, name_file)
            self.ui.label_7.setText("¡Listo (SUMO)!")

        if reused_bg:
            QMessageBox.information(
                self,
                "Imagen de fondo reutilizada",
                "La imagen 'background.jpg' ya existía en la carpeta 'background' y se ha reutilizado para la red.\n\n"
                "En caso desee descargarla nuevamente, debe borrar el archivo 'background.jpg'."
            )

def main():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()