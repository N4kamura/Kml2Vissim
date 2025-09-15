from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5 import uic
import warnings
from src.network.create_network import vissim_creator
from src.background.get_background import kml2png_function, convert_background
from interface.ui import Ui_MainWindow

warnings.filterwarnings("ignore", category=DeprecationWarning)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.pushButton.clicked.connect(self.openfile)
        self.ui.pushButton_2.clicked.connect(self.name)

    def openfile(self):
        self.path_file,_ = QFileDialog.getOpenFileName(self,"Seleccionar carpeta","c:\\","KML Files (*.kml)")
        if self.path_file:
            self.ui.lineEdit.setText(self.path_file)
    
    def name(self):
        name_file = self.ui.lineEdit_2.text()
        if name_file == '':
            return self.ui.lineEdit_2.setText('Ingresar nombre acá')
        vissim_creator(self.path_file,name_file)
        kml2png_function(self.path_file,name_file)
        convert_background(self.path_file,name_file)

def main():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()