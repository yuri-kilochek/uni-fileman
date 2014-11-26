import PyQt4.QtCore as _QtCore
import PyQt4.QtNetwork as _QtNetwork

from config import config as _config

# оповеститель мониторов
class Announcer(_QtCore.QObject):
    # конструктор
    def __init__(self):
        super().__init__()

        self.__udp_socket = _QtNetwork.QUdpSocket()

        self.__timer = _QtCore.QTimer()
        self.__timer.timeout.connect(self.__announce)
        self.__timer.start(int(_config['heartbeat-interval'] * 1000))

    # оповестить потенциальных клиентов о существовании сервера
    def __announce(self):
        self.__udp_socket.writeDatagram(
            _config['announcement-token'].encode(),
            _QtNetwork.QHostAddress.Broadcast,
            _config['announcement-port']
        )

# монитор оповестителей
class Monitor(_QtCore.QObject):
    # конструктор
    def __init__(self):
        super().__init__()

        self.__servers = {}

        self.__udp_socket = _QtNetwork.QUdpSocket()
        self.__udp_socket.bind(_QtNetwork.QHostAddress.Any, _config['announcement-port'])
        self.__udp_socket.readyRead.connect(self.__ready_read)

        self.__timer = _QtCore.QTimer()
        self.__timer.timeout.connect(self.__remove_dead_servers)
        self.__timer.start(int(2 * _config['heartbeat-interval'] * 1000))

    # обработчик собыйтия "датаграмма получена"
    def __ready_read(self):
        while self.__udp_socket.hasPendingDatagrams():
            token, address, _ = self.__udp_socket.readDatagram(self.__udp_socket.pendingDatagramSize())
            if token.decode() == _config['announcement-token']:
                self.__vitalize_server(address.toString())

    # собыйтие "сервер найден"
    server_found = _QtCore.pyqtSignal(str)

    # сбросить таймер сервера
    def __vitalize_server(self, server_address):
        if server_address in self.__servers:
            server_elapsed_timer = self.__servers[server_address]
            server_elapsed_timer.restart()
            return
        server_elapsed_timer = _QtCore.QElapsedTimer()
        server_elapsed_timer.start()
        self.__servers[server_address] = server_elapsed_timer
        self.server_found.emit(server_address)

    # событие "сервер потерян"
    server_lost = _QtCore.pyqtSignal(str)

    # удалить неактивные сервера из списка активных
    def __remove_dead_servers(self):
        for address in list(self.__servers.keys()):
            elapsed_timer = self.__servers[address]
            if elapsed_timer.elapsed() >= self.__timer.interval():
                self.__servers.pop(address)
                self.server_lost.emit(address)
