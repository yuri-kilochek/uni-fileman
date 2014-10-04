import sys

from PyQt4.QtGui import *


class Client(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.main_window = QMainWindow()
        self.main_window.resize(250, 150)
        self.main_window.move(300, 300)
        self.main_window.setWindowTitle('Sample Text')

    def exec_(self):
        self.main_window.show()

        return super().exec_()

if __name__ == '__main__':
    sys.exit(Client(sys.argv).exec_())
