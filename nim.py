#!/usr/bin/python3
import sys
import socket
import struct
import errno
from shared_global import *


# this function print's the heaps status in the format
def print_heaps(n_a, n_b, n_c):
    print("Heap A: {}".format(n_a))
    print("Heap B: {}".format(n_b))
    print("Heap C: {}".format(n_c))


# this function checks the user input "play" is in the correct format,
# and creates the data to be sent to the server accordingly
def create_turn_to_send(play):
    if len(play) == 2 and play[1].isdigit():
        num_to_send = int(play[1])
        if play[0] == "A":
            heap_enum = HEAP_A
        elif play[0] == "B":
            heap_enum = HEAP_B
        elif play[0] == "C":
            heap_enum = HEAP_C
        else:  # heap letter is not A or B or C
            heap_enum = ILLEGAL_HEAP_INPUT
            num_to_send = 0
    elif len(play) == 1 and play[0] == "Q":  # the user input is Q for quit
        heap_enum = QUIT
        num_to_send = 0
    else:
        heap_enum = ILLEGAL_HEAP_INPUT
        num_to_send = 0

    return heap_enum, num_to_send

# this function is responsible for the client socket connection and the client work.
# it starts a socket connection to the server.
# it print's the heaps status and game status it gets from the server.
# it gets the player's input, checks its in the right format and sends it to the server.
# in case of an error, the connection is closed and the function returns.
def nim_game_client(my_host, my_port):
    game_active = True
    output = None

    # creating a socket and connecting to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except OSError as e:
            print(e.strerror)
            soc.close()
            return

        while game_active:
            #  1) receive heaps from server
            #  2) receive game status from server (turn/win/lose)
            output = recv_all(soc, ">iiii")
            if output == 2:
                # there was a connection error from server, we print a specific message and end the game.
                print("Disconnected from server")
                break
            if output == 0:
                # there was an error while receiving the data from the server. the game ends with this client.
                break

            n_a, n_b, n_c, game_status = struct.unpack(">iiii", output)
            print_heaps(n_a, n_b, n_c)

            if game_status == PLAYERS_TURN:
                # 3) it is the player's turn, the client gets the player's input and send it to server
                print("Your turn:")
                play = input()
                play = play.split()
                heap_enum, num_to_send = create_turn_to_send(play)
                data = struct.pack(">ii", heap_enum, num_to_send)

                result = send_all(soc, data)
                if result == 2:
                    # there was a connection error from server, we print a specific message and end the game.
                    print("Disconnected from server")
                elif result == 0:
                    # there was an error while sending the data to the server. the game ends.
                    break

                if heap_enum == QUIT:
                    game_active = False
                    continue

            else:
                if game_status == SERVER_WINS:
                    print("Server win!")
                if game_status == PLAYER_WINS:
                    print("You win!")
                game_active = False
                continue

            #   4) Server response to move
            output = recv_all(soc, ">i")
            if output == 2:
                # there was a connection error from server, we print a specific message and end the game.
                print("Disconnected from server")
                break
            if output == 0:
                # there was an error while receiving the data from the server. the game ends with this client.
                break

            server_response = struct.unpack(">i", output)[0]
            if server_response == PLAYER_ILLEAGL_MOVE:
                print("Illegal move")
            elif server_response == PLAYER_MOVE_ACCEPTED:
                print("Move accepted")
            else:
                print("got some error from server response: ", server_response)
                break


# this function starts client
# gets the arguments for the client's program and send them to the nim_game_client function.
# wraps the nim_game_server function in case of an error.
def start_client():
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        host = sys.argv[1]
        port = 6444
    elif len(sys.argv) == 1:
        host = "localhost"
        port = 6444
    else:
        print("Illegal number of arguments!")
        return
    try:
        nim_game_client(host, port)
    except OSError as err:
        if err.errno == errno.ECONNREFUSED:
            print("connection refused by server")
        else:
            print(err.strerror)


start_client()
