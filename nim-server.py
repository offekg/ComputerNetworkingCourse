#!/usr/bin/python3
import socket
import sys
import struct


def nim_game_server(my_port):
    heaps = [3,4,6]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', my_port))
        except socket.error as e:
            print(e.strerror)

        try:
            s.listen(5)
        except socket.error as e:
            print(e.strerror)

        conn_sock = None
        try:
            conn_sock, address = s.accept()
        except socket.error as e:
            print(e.strerror)

        with conn_sock:
            data = struct.pack(">iii", heaps[0], heaps[1], heaps[2])
            try:
                conn_sock.send(data)
            except socket.error as e:
                print(e.strerror)

def accept_connection(my_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', my_port))
        except socket.error as e:
            print(e.strerror)

        try:
            s.listen(5)
        except socket.error as e:
            print(e.strerror)

        conn_sock = None
        try:
            conn_sock, address = s.accept()
        except socket.error as e:
            print(e.strerror)

        with conn_sock:
            msg = ""
            try:
                msg = conn_sock.recv(1024).decode()
            except socket.error as e:
                print(e.strerror)

            print("Message from client is:",msg)

            data = "Goodbye"
            try:
                conn_sock.send(data.encode())
            except socket.error as e:
                print(e.strerror)


#port = sys.argv[1]

nim_game_server(6644)