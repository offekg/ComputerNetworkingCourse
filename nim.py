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

#this function creates the data of the player's move to be sent to the server
def create_turn_to_send(play):
    if len(play) == 2 and play[1].isdigit():
        num_to_send= int(play[1])
        if play[0] == "A":
            heap_enum= HEAP_A
        elif play[0] == "B":
            heap_enum= HEAP_B
        elif play[0] == "C":
            heap_enum= HEAP_C
        else:  # heap letter is not A or B or C
            heap_enum = ILLEGAL_HEAP_INPUT
            num_to_send = 0
    elif len(play) == 1 and play[0] == "Q": #the user input is Q for quit
        heap_enum= QUIT
        num_to_send=0
    else:
        heap_enum=ILLEGAL_HEAP_INPUT
        num_to_send=0

    return heap_enum,num_to_send


def nim_game_client(my_host, my_port):
    game_active = True
    output = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except socket.error as e: # todo- why not OSError???
            print(e.strerror)

        while game_active:


        #  1) receive heaps from server
        #  2) receive game status from server (turn/win/lose)
            output= recv_all(soc,">iiii")
            if output in None:
                print ("error with recv")
                continue  # todo- why continue? if there was an error with recv shouldnt we stop the game?

            n_a,n_b,n_c,game_status = struct.unpack(">iiii", output)
            print_heaps(n_a,n_b,n_c)

            if game_status == PLAYERS_TURN:

            #   3) send players action
                print("Your turn:\n")
                play = input()

                play = play.split()
                heap_enum, num_to_send = create_turn_to_send(play)
                data = struct.pack(">ii", heap_enum, num_to_send)

                if not send_all(soc,data):
                    print("error with send")
                    continue # Todo- break? continue? need to stop the game if the send didnt work

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
            output= recv_all(soc, ">i")
            if output is None:
                print ("error with recv")
                continue  # Todo- break? continue? need to stop the game if the send didnt work

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
def start_client():
    if len(sys.argv)==3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    elif len(sys.argv)==1:
        host="localhost"
        port=6444
    else:
        print("Illegal number of arguments!")
        return
    nim_game_client(host, port)

start_client()

