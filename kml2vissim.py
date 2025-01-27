from PyQt5.QtWidgets import QMainWindow, QLineEdit, QApplication, QPushButton,QLabel,QFileDialog
from PyQt5 import uic
import warnings
from network import vissimcreator
from get_background import shape2png_function,convert_background

warnings.filterwarnings("ignore", category=DeprecationWarning)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("images/shape2vissim.ui", self)

        self.pushButton.clicked.connect(self.openfile)
        self.pushButton_2.clicked.connect(self.name)

    def openfile(self):
        self.path_file,_ = QFileDialog.getOpenFileName(self,"Seleccionar carpeta","c:\\","KML Files (*.kml)")
        if self.path_file:
            self.lineEdit.setText(self.path_file)
    
    def name(self):
        name_file = self.lineEdit_2.text()
        if name_file == '':
            return self.lineEdit_2.setText('Ingresar nombre acá')
        vissimcreator(self.path_file,name_file)
        shape2png_function(self.path_file,name_file)
        convert_background(self.path_file,name_file)

def main():
    app = QApplication([])
    window = Window()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()