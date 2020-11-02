#!/usr/bin/python3
import sys
import socket
import struct
import errno
from shared_global import *


# a function to print the heaps status in the format
def print_heaps(n_a, n_b, n_c):
    print("Heap A: {}".format(n_a))
    print("Heap B: {}".format(n_b))
    print("Heap C: {}".format(n_c))


# this function creates the data of the player's move to be sent to the server
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


def nim_game_client(my_host, my_port):
    game_active = True
    output = None

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
                # If recv_all failed, close connection and stop the client side
                print("Disconnected from server")
                break
            if output == 0:
                break

            n_a, n_b, n_c, game_status = struct.unpack(">iiii", output)
            print_heaps(n_a, n_b, n_c)

            if game_status == PLAYERS_TURN:
                #   3) send players action
                print("Your turn:")
                play = input()
                play = play.split()
                heap_enum, num_to_send = create_turn_to_send(play)
                data = struct.pack(">ii", heap_enum, num_to_send)

                result = send_all(soc, data)
                if result == 2:
                    print("Disconnected from server")
                elif result == 0:
                    # If send_all failed, close connection and stop the client side
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
                # If recv_all failed, close connection and stop the client side
                print("Disconnected from server")
                break
            if output == 0:
                break

            server_response = struct.unpack(">i", output)[0]
            if server_response == PLAYER_ILLEAGL_MOVE:
                print("Illegal move")
            elif server_response == PLAYER_MOVE_ACCEPTED:
                print("Move accepted")
            else:
                print("got some error from server response: ", server_response)
                break


######
# gets the stdin argument and starts the game from the client's side.
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
