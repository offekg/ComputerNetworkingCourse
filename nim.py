#!/usr/bin/python3
import sys
import socket
import struct
from shared_global import *

#a function to print the heaps status in the format
def print_heaps(n_a,n_b,n_c):
    print("Heap A: " + n_a + '\n')
    print("Heap B: " + n_b + '\n')
    print("Heap C: " + n_c + '\n')


def get_enum_to_send(inp):  # list of 2 strings - heap and num - unless illegal
    if len(inp) == 1 and inp[0] == "Q":
        return QUIT
    if len(inp) == 2 and inp[1].isdigit():
        if inp[0] == "A":
            return HEAP_A
        if inp[0] == "B":
            return HEAP_B
        if inp[0] == "C":
            return HEAP_C

    return ILLEGAL_HEAP_INPUT


def nim_game_client(my_host, my_port):
    game_active = True
    output = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except socket.error as e:
            print(e.strerror)
        while game_active:

        #  1) receive heaps from server
        #  2) receive game status from server (turn/win/lose)
            try:
                output = soc.recv(struct.calcsize(">iiii"))
            except socket.error as err:
                print(err.strerror)
                continue

            n_a,n_b,n_c,game_status = struct.unpack(">iiii", output)
            print_heaps(n_a,n_b,n_c)

            if game_status == PLAYERS_TURN:
                print("Your turn:")

            #   3) send players action
                raw_play = ""
                try:
                    raw_play = input()
                except socket.error as err:
                    print(err.strerror)
                    continue #TODO - what to do if reach here
                play = raw_play.split()
                heap_enum = get_enum_to_send(play)

                if heap_enum == ILLEGAL_HEAP_INPUT or heap_enum == QUIT:
                    num_to_send = 0
                else:
                    num_to_send = int(play[0])
                data = struct.pack(">ii", heap_enum, num_to_send)
                try:
                    soc.send(data)  # TODO - create sendAll
                except socket.error as err:
                    print(err.strerror)

                if heap_enum == QUIT:
                    game_active = False
                    break

            else:
                if game_status == SERVER_WINS:
                    print("Server win!")
                if game_status == PLAYER_WINS:
                    print("You win!")
                game_active = False
                break

        #   4) Server response to move
            try:
                output = soc.recv(struct.calcsize(">i"))
            except socket.error as err:
                print(err.strerror)
                continue
            server_response = struct.unpack(">i", output)
            if server_response == PLAYER_ILLEAGL_MOVE:
                print("Illegal move")
            elif server_response == PLAYER_MOVE_ACCEPTED:
                print("Move accepted")
            else:
                # TODO - what if we get something else
                print("got some error from server")


######
# gets the stdin argument and starts the game from the client's side.
if len(sys.argv)==3:
    host = sys.argv[1]
    port = int(sys.argv[2])
    nim_game_client(host, port)

elif len(sys.argv)==1:
    host="localhost"
    port=6444
    nim_game_client(host, port)

else:
    print("Illegal number of arguments!")

