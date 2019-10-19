import socket, sys

serverAddressPort = (input('Введите ip сервера'), int(input('Введите порт приема сообщений сервера')))

bufferSize = 1024
for line in sys.stdin:
    msgFromClient = line
    bytesToSend = str.encode(msgFromClient)
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Send to server using created UDP socket
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)
    msg = "{}: {}".format(serverAddressPort[0], msgFromServer[0].decode('utf-8'))
    print(msg)
