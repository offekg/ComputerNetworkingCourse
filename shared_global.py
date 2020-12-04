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
CLIENT_MESSAGE_SIZE = struct.calcsize(">ii")
SERVER_MESSAGE0_SIZE = struct.calcsize(">i")
SERVER_MESSAGE1_SIZE = struct.calcsize(">iiii")
SERVER_MESSAGE2_SIZE = struct.calcsize(">i")
