#!/usr/bin/python3
import socket
import struct
import errno
import sys
from select import select

#####
#the game binary protocol
#####

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

# Connection Status
PLAYING = 100
WAITING = 101
REJECTED = 102

# messages sizes
CLIENT_MESSAGE_SIZE = struct.calcsize('>ii')
SERVER_MESSAGE0_SIZE = struct.calcsize(">i")
SERVER_MESSAGE1_SIZE = struct.calcsize(">iiii")
SERVER_MESSAGE2_SIZE = struct.calcsize(">i")

# this function will make sure all bytes are sent
# Returns 1 on success, 2 if connection closed, 0 for any other OSError.
def send_all(soc, data):
    while len(data) != 0:
        try:
            sent = soc.send(data)
        except OSError as err:
            if err == errno.EPIPE or err == errno.ECONNRESET:
                return 2
            else:
                print("Error:", err.strerror)
                return 0
        if sent != 0 and sent < len(data):
            data = data[sent:]
        if sent == len(data):
            data = b''
    return 1


# this function will make sure all bytes are received
# Returns byte message on success, 2 if connection closed, 0 for any other OSError.
def recv_all(soc, st):
    size = struct.calcsize(st)
    final_msg = b''  # empty bytes object
    while size > 0:
        try:
            msg = soc.recv(size)
        except OSError as err:
            if err == errno.ECONNREFUSED:
                return 2
            else:
                print(err.strerror)
                return 0
        if not msg:
            return 2
        final_msg += msg
        size -= len(msg)
    return final_msg

"""flag = 0 is soc, flag == 1 is input
def client_recv_all(soc, msg_format, flag):
    size = struct.calcsize(msg_format)
    final_msg = b''  # empty bytes object
    while(True):
        Readable, _, _ = select(rlist=[soc, sys.stdin], wlist=[], xlist=[], timeout=10)
        for sock in Readable:
            if sock == sys.stdin and flag == 0: # excpected server, got input
                # TODO - means we got Q, finish program
            elif sock == soc and flag == 1:# excpected input, got server
                # TODO - means we got unwanted messege from server, need to close
            else:  # got wanted connection
                try:
                    msg = soc.recv(size)
                except OSError as err:
                    if err == errno.ECONNREFUSED:
                        return 2
                    else:
                        print(err.strerror)
                        return 0
                if not msg:
                    return 2
                final_msg += msg
                size -= len(msg)
                if size <= 0:
                    return final_msg
"""
