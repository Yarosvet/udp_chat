#!/usr/bin/env python
import socket
import sys
from pickle import loads, dumps
import rsa
# Qt
# from PyQt5 import uic
from ui import Ui_Window
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import Qt, QTimer


def prepare_bytes_encrypt(bytes_list, public_key, piece=117):
    l = len(bytes_list)
    k = l // piece
    last = bytes_list[k * piece:]
    return [rsa.encrypt(bytes_list[piece * i:piece * (i + 1)], public_key) for i in range(k)] + [
        rsa.encrypt(last, public_key)]


def prepare_bytes_decrypt(crypted_list, privkey):
    res = bytes()
    for el in crypted_list:
        res += rsa.decrypt(el, privkey)
    return res


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.ui = self
        # uic.loadUi('client.ui', self)
        self.ui = Ui_Window()
        self.ui.setupUi(self)
        # Инициализация окна

        timer = QTimer(self)
        timer.setInterval(50)
        timer.timeout.connect(self.main)
        timer.start()

        self.message_id = 0
        self.temporary = {}

        self.localIP = socket.gethostbyname(socket.getfqdn())
        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.change_socket)
        self.ui.reciever_ip.textChanged.connect(self.reconnect)
        self.ui.local_ip.setText(self.localIP)
        self.ui.send_file.clicked.connect(self.file_sender)

        host = self.ui.reciever_ip.text()
        port = int(self.ui.port.text())

        (self.pubkey, self.privkey) = rsa.newkeys(1024)
        self.pubkeys = {}

        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(self.send_address)  # Binding port

    def file_sender(self):
        fname = QFileDialog.getOpenFileName(self, 'Выбрать файл', '')[0]
        self.send_address = (self.ui.reciever_ip.text(), int(self.ui.port.text()))
        if fname != '' and self.ui.reciever_ip.text().count('.') == 3:
            request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
            self.s.sendto(dumps(request), (self.ui.reciever_ip.text(), int(self.ui.port.text())))
            f = open(fname, 'rb')
            data = f.read()
            f.close()
            encrypted = prepare_bytes_encrypt(dumps({'file': data, 'file_name': fname}),
                                              self.pubkeys[self.send_address[0]])
            request = {'type': 'file', 'data': encrypted}
            self.sender_message(request)
            self.ui.plainText.appendPlainText('Me >  [File ' + fname + ']')
            self.message_id += 1

    def change_socket(self):
        host = self.ui.reciever_ip.text()
        port = int(self.ui.port.text())
        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create Socket
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Make Socket Reusable
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow incoming broadcasts
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind((self.ui.local_ip.text(), port))

    def sender_message(self, request):
        pieces = 5
        request['ip'] = self.send_address[0]
        request['request_id'] = self.message_id
        data = request['data']
        cnt = len(data) // pieces
        if len(data) % pieces != 0:
            cnt += 1
        request['count_of_packets'] = cnt
        for i in range(cnt):
            packet = request
            packet['packet_number'] = i + 1
            packet['data'] = data[pieces * i: pieces * (i + 1)]
            self.s.sendto(dumps(packet), self.send_address)

    def reconnect(self):
        if self.ui.reciever_ip.text().count('.') == 3:
            try:
                send_address = (self.ui.reciever_ip.text(), int(self.ui.port.text()))
                request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
                self.s.sendto(dumps(request), send_address)
            except socket.gaierror:
                pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter - 1 and self.ui.reciever_ip.text().count('.') == 3:
            self.send_message()

    def main(self):
        try:
            message, address = self.s.recvfrom(1024)  # Buffer size
            request = loads(message)
            if request['type'] == 'message':
                request_id = request['request_id']
                if address[0] not in self.temporary.keys():
                    self.temporary[address[0]] = {}
                if request['request_id'] not in self.temporary[address[0]]:
                    self.temporary[address[0]][request_id] = {}
                try:
                    maximum = max(self.temporary[address[0]][request_id].keys()) + 1
                except ValueError:
                    maximum = 0
                self.temporary[address[0]][request_id][maximum] = request['data']
                if len(self.temporary[address[0]][request_id].keys()) == request['count_of_packets']:
                    data = []
                    for el in self.temporary[address[0]][request_id].values():
                        data += el
                    del self.temporary[address[0]][request_id]
                    data = loads(prepare_bytes_decrypt(data, self.privkey))
                    self.temporary[address[0]][request['request_id']] = []
                    text = data['text']
                    self.ui.plainText.appendPlainText(address[0] + ':' + str(address[1]) + ' >  ' + text)

            elif request['type'] == 'connect':
                if address[0] == '127.0.0.1':
                    self.pubkeys['127.0.1.1'] = request['data']['pubkey']
                self.pubkeys[address[0]] = request['data']['pubkey']
                if request['data']['need_for_answer'] == 'True':
                    request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'False'}}
                    self.s.sendto(dumps(request), address)

            elif request['type'] == 'file':
                request_id = request['request_id']
                if address[0] not in self.temporary.keys():
                    self.temporary[address[0]] = {}
                if request['request_id'] not in self.temporary[address[0]]:
                    self.temporary[address[0]][request_id] = {}
                try:
                    maximum = max(self.temporary[address[0]][request_id].keys()) + 1
                except ValueError:
                    maximum = 0
                self.temporary[address[0]][request_id][maximum] = request['data']
                if len(self.temporary[address[0]][request_id].keys()) == request['count_of_packets']:
                    data = []
                    for el in self.temporary[address[0]][request_id].values():
                        data += el
                    del self.temporary[address[0]][request_id]
                    decrypted = loads(prepare_bytes_decrypt(data, self.privkey))
                    fname = QFileDialog.getSaveFileName(self, 'Сохранить файл ' + decrypted['file_name'])[0]
                    if fname != '':
                        f = open(fname, 'wb')
                        f.write(decrypted['file'])
                        f.close()
                        self.ui.plainText.appendPlainText(address[0] + ':' + address[1] + ' >  [File ' + fname + ']')
        except BlockingIOError:
            pass

    def send_message(self):
        self.send_address = (self.ui.reciever_ip.text(), int(self.ui.port.text()))
        text = str(self.ui.lineEdit.text())
        request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
        self.s.sendto(dumps(request), self.send_address)
        if text != '' and self.ui.reciever_ip.text().count('.') == 3:
            encrypted = prepare_bytes_encrypt(dumps({'text': text}), self.pubkeys[self.send_address[0]])
            request = {'type': 'message', 'data': encrypted}
            self.sender_message(request)  # sending text
            self.ui.plainText.appendPlainText('Me >  ' + text)  # Show this message
            self.ui.lineEdit.setText('')
            self.message_id += 1


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec_())
