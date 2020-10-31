#!/usr/bin/python3
import socket
import sys
import struct
from shared_global import *

heaps = [3, 4, 5]   # TODO - save initial heap values for new games


def is_legal_move(move):
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
    global heaps
    output = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.bind(('', my_port))
        except socket.error as e:
            print(e.strerror)

        try:
            soc.listen(1)
        except socket.error as e:
            print(e.strerror)

        conn_sock = None

        while True:
            try:
                conn_sock, address = soc.accept()
            except socket.error as e:
                print(e.strerror)

            with conn_sock:
                heaps=[n_a,n_b,n_c]
                status = PLAYERS_TURN    # 0=no one, 1=player, 2=server
                while True:  # While client is still playing / connection is alive
                #   1) Send heap values and game status
                    data = struct.pack(">iiii", heaps[0], heaps[1], heaps[2],status)

                    if not send_all(conn_sock,data):
                        # there was an error while sending the data to the client
                        break  # Todo - break? not sure if this is the way

                    if status != PLAYERS_TURN:
                        break  # game is over # Todo - break? not sure if this is the way


                #   3) accept players move and return response
                    try:
                        output = soc.recv(struct.calcsize(">ii"))
                    except socket.error as err:
                        print(err.strerror)
                    move = struct.unpack(">ii", output)
                    if move[0] == QUIT:  # Client closed the game
                        break
                    if move[0] == ILLEGAL_HEAP_INPUT:
                        server_response = PLAYER_ILLEAGL_MOVE
                    else:
                        if is_legal_move(move):
                            heaps[move[0]] -= move[1]
                            server_response = PLAYER_MOVE_ACCEPTED
                            if is_win():
                                status = PLAYER_WINS
                                continue  # TODO - make sure no other moves to do first
                        else:  # Ilegal player move
                            server_response = PLAYER_ILLEAGL_MOVE

                    data = struct.pack(">i", server_response)
                    try:
                        conn_sock.send(data)  # TODO - create sendAll and deal with problems
                    except socket.error as e:
                        print(e.strerror)

                #   4) make servers move
                    server_move()
                    if is_win():
                        status = SERVER_WINS



if len(sys.argv)==5:
    port = sys.argv[4]
    nim_game_server(port,sys.argv[1],sys.argv[2],sys.argv[3])
elif len(sys.argv) == 4:
    port = 6444
    nim_game_server(port, sys.argv[1], sys.argv[2], sys.argv[3])
else:
    print("Illegal number of arguments!")


