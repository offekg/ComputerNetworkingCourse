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

# this function is responsible for the server socket connection and the server game logic.
# it starts a socket, with socket, bind and listen commands.
# when a client tries to connect, it accepts a single connection and the game begins.
# when the connection is closed, returns to listening until a new client connect.
# in case of an error, the server closes the connection and the function returns.
def nim_game_server(my_port,n_a,n_b,n_c):

    # creating a socket with socket, bind and listen commands.
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
        output = None

        # while the server is up, it is waiting fo a client to connect to him.
        while True:
            try:
                conn_sock, address = soc.accept()
            except socket.error as e:
                # Failed specific "accept". continue to try again next iteration
                print(e.strerror)
                continue

            with conn_sock:
                # created a connection with a client. the games starts with full heaps.
                # for each new connection we will restart the heaps sizes
                heaps[0] = n_a
                heaps[1] = n_b
                heaps[2] = n_c

                #the game starts with the player's turn
                status = PLAYERS_TURN

                while True:
                    # While client is still playing / connection is alive
                    # 1) Send to the client the current heap values and game status
                    data = struct.pack(">iiii", heaps[0], heaps[1], heaps[2], status)
                    send_status = send_all(conn_sock, data)
                    if send_status == 0:
                        # there was an error while sending the data to the client. the game ends with this client.
                        break
                    elif send_status == 2:
                        # there was a connection error from client, we print a specific message and end the game.
                        print("Disconnected from client")
                        break

                    if status != PLAYERS_TURN:
                        # the game is over - close connection with the current client.
                        break

                    # 2) accept players move and return response
                    move = recv_all(conn_sock, ">ii")
                    if move == 2:
                        # there was a connection error from client, we print a specific message and end the game.
                        print("Disconnected from client")
                        break
                    elif move == 0:
                        # there was an error while receiving the data from the client. the game ends with this client.
                        break

                    move = struct.unpack(">ii", move)

                    if move[0] == QUIT:
                        # Client ended the game.
                        break
                    elif move[0] == ILLEGAL_HEAP_INPUT:
                        # the move received from the player was illegal.
                        server_response = PLAYER_ILLEAGL_MOVE
                    else:
                        if is_legal_move(move):
                            # the player's move is legal so we update the heaps accordingly.
                            heaps[move[0]] -= move[1]
                            server_response = PLAYER_MOVE_ACCEPTED
                            if is_win():
                                status = PLAYER_WINS
                        else:
                            # Illegal player move
                            server_response = PLAYER_ILLEAGL_MOVE

                    # send the client if the player's move was accepted or not.
                    data = struct.pack(">i", server_response)
                    send_status = send_all(conn_sock, data)
                    if send_status == 0:
                        # there was an error while sending the data to the client. the game ends with this client
                        break
                    elif send_status == 2:
                        # there was a connection error from client, we print a specific message and end the game.
                        print("Disconnected from client")
                        break

                #   3) play the server's move if the player didn't win yet.
                    if status != PLAYER_WINS:
                        server_move()
                        if is_win():
                            status = SERVER_WINS

# this function starts the server
# gets the arguments for the server program and wraps send them to the nim_game_server function.
# wraps the nim_game_server function in case of an error.
def start_server():
    if len(sys.argv) == 5:
        port = int(sys.argv[4])
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
