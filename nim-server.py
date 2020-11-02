#!/usr/bin/python3
import socket
import sys
import struct
import errno
from shared_global import *

heaps = [1, 1, 1]



def is_legal_move(move):
    if move[1] <= 0 or heaps[move[0]] - move[1] < 0:
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
        except OSError as e:
            print(e.strerror)
            soc.close()
            return

        try:
            soc.listen(1)
        except socket.error as e:
            print(e.strerror)
            soc.close()
            return

        conn_sock = None

        while True:
            try:
                conn_sock, address = soc.accept()
            except socket.error as e:
                print(e.strerror)
                continue  # Failed specific "accept". continue to try again next iteration

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
                        break

                    if status != PLAYERS_TURN:
                        break  # game is over - close connection

                #   2) accept players move and return response
                    move = recv_all(conn_sock, ">ii")
                    if move is None:  # there was an error during recv
                        # If recv_all failed, close connection
                        break
                    move = struct.unpack(">ii", move)

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
                        else:  # Illegal player move
                            server_response = PLAYER_ILLEAGL_MOVE

                    data = struct.pack(">i", server_response)
                    if not send_all(conn_sock, data):
                        # If send_all failed, close connection
                        break

                #   3) make servers move
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
    try:
        nim_game_server(port, int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
    except OSError as err:
        if err.errno == errno.ECONNREFUSED:
            print("connection failed")
        else:
            print(err.strerror)


start_server()
