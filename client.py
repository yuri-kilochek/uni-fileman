import sys

from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

import config


class Client(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.announce_receiver = QUdpSocket()
        self.announce_receiver.bind(QHostAddress.Any, config.announce_port)
        self.announce_receiver.readyRead.connect(self.read_announce_receiver)

        # self.main_window = QMainWindow()
        # self.main_window.resize(250, 150)
        # self.main_window.move(300, 300)
        # self.main_window.setWindowTitle('Sample Text')
        # self.main_window.show()

    def read_announce_receiver(self):
        print('read_announce_receiver')
        while self.announce_receiver.hasPendingDatagrams():
            message, address, _ = self.announce_receiver.readDatagram(self.announce_receiver.pendingDatagramSize())
            if message.decode('UTF-8') == config.announce_message:
                self.on_announce(address.toString())

    def on_announce(self, server_address):
        print('Server {} announced itself'.format(server_address))

if __name__ == '__main__':
    sys.exit(Client(sys.argv).exec_())
