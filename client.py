#!/usr/bin/env python
import socket
import sys, select
import time
import threading
from pickle import loads, dumps
import rsa
# Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt


def encrypt(message, public):
    return rsa.encrypt(message, public)


def decrypt(message, private):
    return rsa.decrypt(message, private)


class MyWidget(QMainWindow):
    def __init__(self):
        self.was_visible = False
        super().__init__()
        # Инициализация окна
        uic.loadUi('client.ui', self)
        self.localIP = socket.gethostbyname(socket.getfqdn())
        self.pushButton.clicked.connect(self.send_message)
        self.pushButton_2.clicked.connect(self.change_socket)
        self.reciever_ip.textChanged.connect(self.reconnect)
        self.local_ip.setText(self.localIP)

        host = self.reciever_ip.text()
        port = int(self.port.text())

        (self.pubkey, self.privkey) = rsa.newkeys(512)
        self.pubkeys = {}

        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port
        thr = threading.Thread(target=self.main)
        thr.start()

    def change_socket(self):
        host = self.reciever_ip.text()
        port = int(self.port.text())
        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind((self.local_ip.text(), port))

    def reconnect(self):
        try:
            send_address = (self.reciever_ip.text(), int(self.port.text()))
            request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
            self.s.sendto(dumps(request), send_address)
        except socket.gaierror:
            pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter - 1:
            self.send_message()

    def main(self):
        while True:
            if not self.isVisible() and self.was_visible:
                break
            else:
                self.was_visible = True
            try:
                time.sleep(0.1)
                message, address = self.s.recvfrom(1024)  # Buffer size
                request = loads(message)
                if request['type'] == 'message':
                    data = loads(decrypt(request['data'], self.privkey))
                    text = data['text']
                    self.plainText.appendPlainText(f'{address[0]}:{address[1]} >  {text}')  # printing message
                elif request['type'] == 'connect':
                    if address[0] == '127.0.0.1':
                        self.pubkeys['127.0.1.1'] = request['data']['pubkey']
                    self.pubkeys[address[0]] = request['data']['pubkey']
                    if request['data']['need_for_answer'] == 'True':
                        request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'False'}}
                        self.s.sendto(dumps(request), address)
            except BlockingIOError:
                pass

    def send_message(self):
        self.send_address = (self.reciever_ip.text(), int(self.port.text()))
        text = str(self.lineEdit.text())
        request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
        self.s.sendto(dumps(request), self.send_address)
        if text != '':
            crypted = encrypt(dumps({'text': text}), self.pubkeys[self.send_address[0]])
            request = {'type': 'message', 'data': crypted}
            self.s.sendto(dumps(request), self.send_address)  # sending text
            self.plainText.appendPlainText('Me >  ' + text)  # Show this message


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec_())
