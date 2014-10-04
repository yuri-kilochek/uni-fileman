import time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import config


class ServerList(QMainWindow):
    _dead_interval = 2 * config.announce_interval

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._servers = QListWidget(self)
        self._servers.itemDoubleClicked.connect(self._pick_server)
        self.setCentralWidget(self._servers)
        self.on_pick_server = None

        self._server_dropper = QTimer()
        self._server_dropper.timeout.connect(self._drop_dead_servers)
        self._server_dropper.start(int(ServerList._dead_interval * 1000))

    def update_server(self, server_address):
        for item in map(self._servers.item, range(self._servers.count())):
            if item.text() == server_address:
                timer = item.data(Qt.UserRole)
                timer.restart()
                return
        item = QListWidgetItem(server_address)
        timer = QElapsedTimer()
        timer.start()
        item.setData(Qt.UserRole, timer)
        self._servers.addItem(item)

    def _pick_server(self, item):
        if self.on_pick_server:
            address = item.text()
            self.on_pick_server(address)

    def _drop_dead_servers(self):
        for i in range(self._servers.count()):
            item = self._servers.item(i)
            timer = item.data(Qt.UserRole)
            if timer.elapsed() / 1000.0 > ServerList._dead_interval:
                self._servers.takeItem(i)
