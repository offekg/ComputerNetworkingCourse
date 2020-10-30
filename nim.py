#!/usr/bin/python3
import sys
import socket
import struct
from shared_global import *


def print_heaps(heap):   # TODO - complete by format
    print(heap)


def is_input_valid(inp):  # list of 2 strings - heap and num - unless illegal
    if len(inp) != 2:
        return False
    if inp[0] not in ["A", "B", "C"]:
        return False
    if not inp[1].isdigit():
        return False
    return True


def return_heap_enum(heap_char):
    if heap_char == "A":
        return HEAP_A
    if heap_char == "B":
        return HEAP_B
    else: # heap_char == "C"
        return  HEAP_C


def nim_game_client(my_host, my_port):
    game_not_over = True
    output = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except socket.error as e:
            print(e.strerror)
        while game_not_over:

            #  1) receive heaps from server
            try:
                output = soc.recv(struct.calcsize(">iii"))
            except socket.error as err:
                print(err.strerror)
                continue

            heaps = struct.unpack(">iii", output)   #  TODO - what if output is still None?
            print_heaps(heaps)

            #  2) receive game status from server (turn/win/lose)
            try:
                output = soc.recv(struct.calcsize(">i"))
            except socket.error as err:
                print(err.strerror)
                continue
            game_status = struct.unpack(">i", output)

            if game_status == PLAYERS_TURN:
                print("Your turn:")
                raw_play = ""
                try:
                    raw_play = input()
                except socket.error as err:
                    print(err.strerror)
                    continue #TODO - what to do if reach here
                play = raw_play.split()
                if is_input_valid(play):
                    heap_enum = return_heap_enum(play[0])
                    data = struct.pack(">ii", heap_enum, play[1])
                else:
                    data = struct.pack(">ii", ILLEGAL_HEAP_INPUT, 0)
                soc.send(data)  # TODO - create sendAll




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