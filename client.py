import socket
import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QErrorMessage
from Crypto.Cipher import DES


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main1.ui', self)
        self.pushButton.clicked.connect(self.run)

    def run(self):
        self.label.setText("OK")


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
localIP = socket.gethostbyname(socket.getfqdn())
localPort = 20001
bufferSize = 1024
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((localIP, localPort))
print("Сервер запущен. IP - {}".format(localIP))
while True:
    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    clientMsg = "{}: {}".format(address[0], message.decode('utf-8'))
    print(clientMsg)
    UDPServerSocket.sendto(bytesToSend, address)


def pad(text):
    while len(text) % 8 != 0:
        text += b' '
    return text


def encrypt(text, key):
    des = DES.new(key, DES.MODE_ECB)
    return des.encrypt(pad(text).encode('utf-8'))


def decrypt(text, key):
    try:
        des = DES.new(key, DES.MODE_ECB)
        return des.decrypt(text).decode('utf-8')
    except Exception:
        return 'PYTHON EXCEPTION!!!'


def send(text, ip, port):
    global UDPClientSocket
    UDPClientSocket.sendto(encrypt(text), [ip, port])


def show_messsage(text, key):
    pass  # доделать


class Example(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('client.ui', self)
        self.pushButton.clicked.connect(self.sender)

    def sender(self):
        try:
            text = encrypt(self.lineEdit.text(), self.lineEdit_7)
            ip = self.lineEdit_4.text()
            port = self.lineEdit_6.text()
            send(text, ip, port)
        except Exception:
            error_dialog = QErrorMessage()
            error_dialog.showMessage('Error. Check the fields.')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec())
sys.exit(app.exec_())
