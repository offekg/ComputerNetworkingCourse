from socket import *




def open_connection():

    ListeningSocket = socket(AF_INET, SOCK_STREAM)
    ListeningSocket.bind(("", 80))
    ListeningSocket.listen(5)  # Socket becomes listening
    (conn_sock, address) = ListeningSocket.accept()
    byt_obj = conn_sock.recv(1024)
