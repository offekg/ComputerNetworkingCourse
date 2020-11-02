#!/usr/bin/python3
import socket
import sys
import struct
from shared_global import *

heaps = [1, 1, 1]
#global heaps

def is_legal_move(move):  # TODO - what about playing 0
    if heaps[move[0]] - move[1] < 0:
        return False
    return True

def is_win():
    for heap in heaps:
        if heap != 0:
            return False
    return True

def server_move():
# removes 1 from largest heap. if more then one - then from lowest index
    global heaps
    max_index = 0
    max_heap = 0

    for i in range(len(heaps)):
        if heaps[i] > max_heap:
            max_heap = heaps[i]
            max_index = i
    heaps[max_index] -= 1



def nim_game_server(my_port,n_a,n_b,n_c):
    output = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.bind(('', my_port))
        except socket.error as e:  # todo- why not OSError??
            print(e.strerror)      # todo - we should end the server? we cant continue to the rest of the code

        try:
            soc.listen(1)
        except socket.error as e:
            print(e.strerror)     # todo - we should end the server? we cant continue to the rest of the code

        conn_sock = None

        while True:
            try:
                conn_sock, address = soc.accept()
            except socket.error as e:
                print(e.strerror)      # todo - we should end the server? we cant continue to the rest of the code

            with conn_sock:
                heaps[0] = n_a
                heaps[1] = n_b
                heaps[2] = n_c     # for each new connection we will restart the heaps sizes
                status = PLAYERS_TURN    # 0=no one, 1=player, 2=server

                while True:  # While client is still playing / connection is alive

                #   1) Send heap values and game status
                    data = struct.pack(">iiii", heaps[0], heaps[1], heaps[2], status)
                    if not send_all(conn_sock, data):
                        # there was an error while sending the data to the client
                        break  # Todo - break? not sure if this is the way

                    if status != PLAYERS_TURN:
                        break  # game is over # Todo - break? not sure if this is the way


                #   3) accept players move and return response
                    move = recv_all(conn_sock, ">ii")
                    if move is None:  # there was an error during recv
                        print("error with recv")
                        break  # todo - break? continue? we should stop the game....
                    move = struct.unpack(">ii", move)
                    #print("move received: {}".format(move))

                    if move[0] == QUIT:  # Client closed the game
                        break
                    elif move[0] == ILLEGAL_HEAP_INPUT:
                        server_response = PLAYER_ILLEAGL_MOVE
                    else:
                        if is_legal_move(move):
                            heaps[move[0]] -= move[1]
                            server_response = PLAYER_MOVE_ACCEPTED
                            if is_win():
                                status = PLAYER_WINS
                        else:  # Ilegal player move
                            server_response = PLAYER_ILLEAGL_MOVE

                    #print("sending server response: {}".format(server_response))
                    data = struct.pack(">i", server_response)
                    if not send_all(conn_sock, data):
                        print("error with send")
                        break   #Todo - break? not sure if this is the way

                #   4) make servers move
                    if status != PLAYER_WINS:
                        server_move()
                        if is_win():
                            status = SERVER_WINS

def start_server():
    if len(sys.argv) == 5:
        port = sys.argv[4]
    elif len(sys.argv) == 4:
        port = 6444
    else:
        print("Illegal number of arguments!")
        return
    nim_game_server(port, int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

start_server()