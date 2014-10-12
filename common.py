import pickle
import struct

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *


class Connection(QObject):
    class Failure(Exception):
        pass

    def __init__(self, tcp_socket):
        super().__init__()

        self._tcp_socket = tcp_socket
        self._tcp_socket.readyRead.connect(self._receive)

        self._receive_buffer = bytearray()

    @property
    def remote_address(self):
        address = self._tcp_socket.peerAddress()
        if address == QHostAddress.Null:
            return None
        return address.toString()

    def send(self, message):
        send_buffer = bytearray()
        data = pickle.dumps(message)
        send_buffer += struct.pack('!I', len(data))
        send_buffer += data
        while len(send_buffer) > 0:
            written = self._tcp_socket.write(send_buffer)
            if written == -1:
                error = self._tcp_socket.errorString()
                self._disconnect(error)
                raise Connection.Failed(error)
            del send_buffer[:written]

    def _receive(self):
        data = self._tcp_socket.read(self._tcp_socket.bytesAvailable())
        if data is None:
            error = self._tcp_socket.errorString()
            self._disconnect(error)
            raise Connection.Failed(error)
        self._receive_buffer += data
        while True:
            if len(self._receive_buffer) < 4:
                break
            size, = struct.unpack('!I', self._receive_buffer[:4])
            if len(self._receive_buffer) < 4 + size:
                break
            message = pickle.loads(self._receive_buffer[4:4 + size])
            del self._receive_buffer[:4 + size]
            self.received.emit(message)

    received = pyqtSignal(object)

    def _disconnect(self, reason):
        self._tcp_socket.close()
        self.disconnected.emit(reason)

    def disconnect(self):
        self._disconnect(None)

    disconnected = pyqtSignal(str)