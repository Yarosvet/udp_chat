#!/usr/bin/env python
import socket
import sys
from pickle import loads, dumps
import rsa
# Qt
# from PyQt5 import uic
from ui import Ui_Window
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QTimer


def encrypt(bytes_list, public_key, piece=117):
    l = len(bytes_list)
    k = l // piece
    last = bytes_list[k * piece:]
    return [rsa.encrypt(bytes_list[piece * i:piece * (i + 1)], public_key) for i in range(k)] + [
        rsa.encrypt(last, public_key)]


def decrypt(crypted_list, privkey):
    res = bytes()
    for el in crypted_list:
        res += rsa.decrypt(el, privkey)
    return res


class MyWidget(QMainWindow):
    def __init__(self):
        # Инициализация
        super().__init__()
        self.ui = Ui_Window()
        self.ui.setupUi(self)

        timer = QTimer(self)
        timer.setInterval(50)
        timer.timeout.connect(self.main)
        timer.start()

        self.message_id = 0
        self.temporary = {}
        self.connected = False

        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.change_socket)
        self.ui.pushButton_3.clicked.connect(self.connector)
        self.ui.send_file.clicked.connect(self.file_sender)
        self.ui.label_2.setText('Now your IP seems to be  ' + socket.gethostbyname(socket.getfqdn()))

        host = self.ui.reciever_ip.text()
        port = int(self.ui.port.text())

        (self.pubkey, self.privkey) = rsa.newkeys(1024)
        self.pubkeys = {}

        self.connect_address = ('', 20001)
        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port
        self.s.listen(1)
        self.conn = 0

    def lock_ui(self):
        self.ui.port.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.send_file.setEnabled(True)
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_3.setText('DISCONNECT')

    def unlock_ui(self):
        self.ui.port.setEnabled(True)
        self.ui.pushButton_2.setEnabled(True)
        self.ui.send_file.setEnabled(False)
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_3.setText('CONNECT')

    def file_sender(self):
        fname = QFileDialog.getOpenFileName(self, 'Выбрать файл', '')[0]
        self.send_address = (self.ui.reciever_ip.text(), int(self.ui.port.text()))
        if fname != '' and self.ui.reciever_ip.text().count('.') == 3:
            request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
            self.s.sendto(dumps(request), (self.ui.reciever_ip.text(), int(self.ui.port.text())))
            f = open(fname, 'rb')
            data = f.read()
            f.close()
            encrypted = encrypt(dumps({'file': data, 'file_name': fname}),
                                self.pubkeys[self.send_address[0]])
            request = {'type': 'file', 'data': encrypted}
            self.send_request(request)
            self.ui.plainText.appendPlainText('Me >  [File ' + fname + ']')
            self.message_id += 1

    def change_socket(self):
        host = self.ui.reciever_ip.text()
        port = int(self.ui.port.text())
        self.send_address = (host, port)  # Set the address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(False)  # Socket non-block
        self.s.bind(('', port))  # Binding port
        self.s.listen(1)

    def send_request(self, request):
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
            self.s.send(dumps(packet))

    def connector(self):
        if not self.connected:
            try:
                self.s.connect((self.ui.reciever_ip.text(), int(self.ui.port.text())))
                send_address = (self.ui.reciever_ip.text(), int(self.ui.port.text()))
                request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'True'}}
                self.s.sendto(dumps(request), send_address)
                self.lock_ui()
                self.connected = True
            except Exception as exc:
                QMessageBox.critical(self, str(type(exc))[8:-2], 'Connection failed\n\n' + str(exc), QMessageBox.Ok)
                self.unlock_ui()
                self.connected = False
        else:
            self.s.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter - 1 and self.ui.reciever_ip.text().count(
                '.') == 3 and self.ui.pushButton.isEnabled():
            self.send_message()

    def message_handler(self, request, address):
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
                data = loads(decrypt(data, self.privkey))
                self.temporary[address[0]][request['request_id']] = []
                text = data['text']
                self.ui.plainText.appendPlainText(address[0] + ':' + str(address[1]) + ' >  ' + text)

        elif request['type'] == 'connect':
            if address[0] == '127.0.0.1':
                self.pubkeys['127.0.1.1'] = request['data']['pubkey']
            self.pubkeys[address[0]] = request['data']['pubkey']
            if request['data']['need_for_answer'] == 'True':
                request = {'type': 'connect', 'data': {'pubkey': self.pubkey, 'need_for_answer': 'False'}}
                self.s.send(dumps(request))

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
                decrypted = loads(decrypt(data, self.privkey))

                fname = QFileDialog.getSaveFileName(self, 'Сохранить файл ' + decrypted['file_name'])[0]
                if fname != '':
                    f = open(fname, 'wb')
                    f.write(decrypted['file'])
                    f.close()
                    self.ui.plainText.appendPlainText(address[0] + ':' + address[1] + ' >  [File ' + fname + ']')

    def main(self):
        try:
            if not self.connected:
                self.conn, self.connect_address = self.s.accept()
            else:
                message = self.conn.recv(1024)
                self.message_handler(loads(message), self.connect_address)
        except BlockingIOError:
            print('no clients')
            pass

    def send_message(self):
        self.send_address = (self.ui.reciever_ip.text(), int(self.ui.port.text()))
        text = str(self.ui.lineEdit.text())
        if text != '' and self.ui.reciever_ip.text().count('.') == 3:
            encrypted = encrypt(dumps({'text': text}), self.pubkeys[self.send_address[0]])
            request = {'type': 'message', 'data': encrypted}
            self.send_request(request)  # sending text
            self.ui.plainText.appendPlainText('Me >  ' + text)  # Show this message
            self.ui.lineEdit.setText('')
            self.message_id += 1


app = QApplication(sys.argv)
ex = MyWidget()
ex.show()
sys.exit(app.exec_())
