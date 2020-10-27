import socket


def open_connection():
    with socket.socket() as soc:
        soc.bind(6644)
        soc.listen()