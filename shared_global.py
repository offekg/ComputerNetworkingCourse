#!/usr/bin/python3
import socket
import struct
import errno

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


# this function will make sure all bytes are sent
# Returns 1 on success, 2 if connection closed, 0 for any other OSError.
def send_all(soc, data):
    while len(data) != 0:
        try:
            sent = soc.send(data)
            print("in send, sent-", sent)
        except OSError as err:
            if err == errno.EPIPE or err == errno.ECONNRESET:
                return 2
            else:
                print("Error:", err, err.strerror)
                return 0
        except Exception as err:
            print("General Error in send_all:", err)

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
        print("Doing recv_all. size-", size)
        try:
            msg = soc.recv(size)
            print("Received msg-",msg)
        except OSError as err:
            if err == errno.ECONNREFUSED:
                return 2
            else:
                print(err.strerror)
                return 0
        except Exception as err:
            print("General Error in recv_all:", err)
        if msg == 0:
            return 2
        final_msg += msg
        size -= len(msg)
    return final_msg
