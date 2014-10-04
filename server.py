import sys

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

import config


class Server(QCoreApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.announce_socket = QUdpSocket()

        self.announce_timer = QTimer()
        self.announce_timer.setInterval(int(config.announce_interval * 1000))
        self.announce_timer.timeout.connect(self.announce)

    def announce(self):
        print('announce')
        self.announce_socket.writeDatagram(config.announce_message, QHostAddress.Broadcast, config.announce_port)

    def exec_(self):
        self.announce_timer.start()

        return super().exec_()

if __name__ == '__main__':
    sys.exit(Server(sys.argv).exec_())