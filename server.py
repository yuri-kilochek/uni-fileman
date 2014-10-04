import sys

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

import config


class Server(QCoreApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.announce_emitter = QUdpSocket()

        self.announce_repeater = QTimer()
        self.announce_repeater.timeout.connect(self.announce)
        self.announce_repeater.start(int(config.announce_interval * 1000))

        # self.client_awaiter = QTcpServer()
        # self.client_awaiter.newConnection.connect(self.on_new_connection)
        # self.client_awaiter.listen(QHostAddress.Any, config.commands_port)

    def announce(self):
        self.announce_emitter.writeDatagram(config.announce_message, QHostAddress.Broadcast, config.announce_port)

    # def on_new_connection(self):
    #     while self.client_awaiter.hasPendingConnections():
    #         client_socket = self.client_awaiter.newConnection()
    #         self.on_client_connected(client_socket)
    #
    # def on_client_connected(self, client_socket):
    #     print('Client connected')

if __name__ == '__main__':
    sys.exit(Server(sys.argv).exec_())