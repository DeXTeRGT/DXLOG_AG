from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtNetwork import QTcpSocket

from LoggerHelper import getLoggerHandle
from configparser import ConfigParser

ReadConfiguration = ConfigParser()
ReadConfiguration.read('config/Configuration.conf')

class TcpClient(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    dataReceived = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)

    def __init__(self, host=ReadConfiguration['TCP_AG_CLINET']['ag_tcp_address'], port=int(ReadConfiguration['TCP_AG_CLINET']['ag_tcp_port']), retry_interval=5000):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = QTcpSocket()
        self.retry_interval = retry_interval  # Time in milliseconds
        self.retry_timer = QTimer(self)
        self.retry_timer.setSingleShot(True)
        self.retry_timer.timeout.connect(self.connect)

        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_ready_read)
        self.socket.errorOccurred.connect(self.on_error_occurred)

    def connect(self):
        self.socket.connectToHost(self.host, self.port)

    def send_data(self, data):
        if self.socket.state() == QTcpSocket.ConnectedState:
            data_with_newline = data + '\n'  # Append newline character
            self.socket.write(data_with_newline.encode())
        else:
            self.errorOccurred.emit("Not connected to server")

    def close(self):
        self.retry_timer.stop()  # Stop the retry timer if it's running
        self.socket.disconnectFromHost()

    @pyqtSlot()
    def on_connected(self):
        self.retry_timer.stop()  # Stop retrying once connected
        self.connected.emit()

    @pyqtSlot()
    def on_disconnected(self):
        self.disconnected.emit()

    @pyqtSlot()
    def on_ready_read(self):
        data = self.socket.readAll().data().decode()
        self.dataReceived.emit(data)

    @pyqtSlot()
    def on_error_occurred(self):
        error_message = self.socket.errorString()  # Get the error message string
        self.errorOccurred.emit(error_message)
        self.retry_timer.start(self.retry_interval)  # Retry connection after a delay
