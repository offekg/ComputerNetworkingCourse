#!/usr/bin/python3
import socket
import struct


# Player moves
HEAP_A = 0
HEAP_B = 1
HEAP_C = 2
ILLEGAL_HEAP_INPUT = 4
QUIT = 5

# Server Responses
PLAYER_ILLEAGL_MOVE = 20
PLAYER_MOVE_ACCEPTED = 21

# Game status
PLAYERS_TURN = 10
SERVER_WINS = 11
PLAYER_WINS = 12


# this function will make sure all bytes are sent
def send_all(soc, data):
    while len(data) != 0:
        try:
            sent = soc.send(data)
        except OSError as err:  # TODO - handle right exception
            print(err.strerror)
            return False
        if sent != 0 and sent < len(data):
            data = data[sent:]
        if sent == len(data):
            data = b''
    return True


# this function will make sure all bytes are received
def recv_all(soc, st):
    size = struct.calcsize(st)
    final_msg = b'' #empty bytes object
    while size > 0:
        try:
            msg = soc.recv(size)   # TODO - check if returns 0
        except OSError as err:   # TODO - handle right exception
            print(err.strerror)
            return None
        if msg is None:
            return None
        final_msg += msg
        size -= len(msg)
    return final_msg
