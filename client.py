import sys

from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

import config
from ServerList import *


class Client(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.announce_receiver = QUdpSocket()
        self.announce_receiver.bind(QHostAddress.Any, config.announce_port)
        self.announce_receiver.readyRead.connect(self.read_announce_receiver)

        self.server_list = ServerList()
        self.server_list.on_pick_server = self.on_pick_server
        self.server_list.show()

    def read_announce_receiver(self):
        while self.announce_receiver.hasPendingDatagrams():
            message, address, _ = self.announce_receiver.readDatagram(self.announce_receiver.pendingDatagramSize())
            if message.decode('UTF-8') == config.announce_message:
                self.on_announce(address.toString())

    def on_announce(self, server_address):
        self.server_list.update_server(server_address)

    def on_pick_server(self, server_address):
        print('Server {} picked'.format(server_address))

if __name__ == '__main__':
    sys.exit(Client(sys.argv).exec_())
