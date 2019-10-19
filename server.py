import socket

localIP = input('Введите ip сервера (0 - {}) :>'.format(socket.gethostbyname(socket.getfqdn())))
if localIP == '0':
    localIP = socket.gethostbyname(socket.getfqdn())
localPort = 20001
bufferSize = 2048
msgFromServer = "Received."
bytesToSend = str.encode(msgFromServer)
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
