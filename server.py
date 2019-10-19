import socket

localIP = "127.0.0.1"
localPort = 20001
bufferSize = 1024
msgFromServer = "Received."
bytesToSend = str.encode(msgFromServer)
# Create a datagram socket
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
# Bind to address and ip
UDPServerSocket.bind((localIP, localPort))
print("Сервер запущен.")
# Listen for incoming datagram
# def wait_message(socket):
while True:
    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    address = bytesAddressPair[1]
    clientMsg = "{}: {}".format(address[0], message.decode('utf-8'))
    print(clientMsg)
    # Sending a reply to client
    UDPServerSocket.sendto(bytesToSend, address)
