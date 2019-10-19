import socket
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget

serverAddressPort = (input('Введите ip сервера :>'), int(input('Введите порт приема сообщений сервера :>')))
print('Отправляйте сообщения.')
bufferSize = 2048
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)


def send(msgFromClient):
    global UDPClientSocket
    UDPClientSocket.sendto(str.encode(msgFromClient), serverAddressPort)
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)
    msg = "{}: {}".format(serverAddressPort[0], msgFromServer[0].decode('utf-8'))
    print(msg)


class Example(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('client.ui', self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
