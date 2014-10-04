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

    def announce(self):
        print('announce')
        self.announce_emitter.writeDatagram(config.announce_message, QHostAddress.Broadcast, config.announce_port)


if __name__ == '__main__':
    sys.exit(Server(sys.argv).exec_())