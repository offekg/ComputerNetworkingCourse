#!/usr/bin/python3
import sys
import socket
import struct


def nim_game_client(my_host, my_port):
    game_not_over = True

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except socket.error as e:
            print(e.strerror)
        while game_not_over:
            output = soc.recv(1024)
            heaps = struct.unpack(">iii", output)
            print(heaps)
            game_not_over = False



def connection(my_host, my_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except socket.error as e:
            print(e.strerror)

        try:
            soc.send("Hello".encode())
        except socket.error as e:
            print(e.strerror)

        output = ""
        try:
            output = soc.recv(1024)
        except socket.error as err:
            print(err.strerror)

        print(output)


#host = sys.argv[1]
#port = sys.argv[2]
#path = sys.argv[3]

nim_game_client("127.0.0.1", 6644)