#!/usr/bin/python3
import sys
import socket
import struct
import errno
from shared_global import *


# Clinet game stages:
RECV0 = 60
RECV1 = 61
SEND = 62
RECV2 = 63

# client msg
recv_msg = b''
sent_msg_size = 0


# This function print's the heaps status in the format
def print_heaps(n_a, n_b, n_c):
    print("Heap A: {}".format(n_a))
    print("Heap B: {}".format(n_b))
    print("Heap C: {}".format(n_c))


# This function checks the user input "play" is in the correct format,
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


# Sends message that is saved in writing_dict[client], to client
# returns 1 if succeeded in sending complete message
# returns 2 if sent part of message, returns 0 for errors
def send(soc, msg):
    # connected client is readable, we will read it
    global sent_msg_size
    if len(msg) - sent_msg_size > 0:
        try:
            sent = soc.send(msg[sent_msg_size:])
        except OSError as err:
            if err == errno.EPIPE or err == errno.ECONNRESET:
                print("Disconnected from server")
                return 0
            else:
                print("Send Error:", err.strerror)
                return 0
        if sent != 0 and sent < len(msg) - sent_msg_size:
            sent_msg_size += sent
            return 2
        if sent == len(msg) - sent_msg_size:
            #sent all
            sent_msg_size = 0
            return 1


# Receives message from server into recv_msg
# returns 1 if succeeded in receiving complete message
# returns 2 if received part of message
# returns 0 for errors
def recv(soc, msg_size):
    # connected client is readable, we will read it
    global recv_msg
    try:
        msg = soc.recv(msg_size - len(recv_msg))
    except OSError as err:
        if err == errno.ECONNREFUSED:
            print("Disconnected from server")
            return 0
        else:
            print("Error:", err.strerror)
            return 0
    if not msg:
        print("Disconnected from server")
        return 0

    recv_msg += msg
    if len(recv_msg) < msg_size:
        return 2  #recv but not all
    else:
        #len(recv_msg) == msg_size:
        return 1  # recv all


# This function is responsible for the client socket connection and the client work.
# it starts a socket connection to the server.
# when connection accepted, prints connection status message from server.
# If the server accepted into playing list, then the game begins.
# If server accepted int waiting list, the client waits for new message.
# If rejected by server, functions returns.
# While playing game, it print's the heaps status and game status it gets from the server.
# it gets the player's input, checks its in the right format and sends it to the server.
# in case of an error, the connection is closed and the function returns.
def nim_game_client(my_host, my_port):
    global recv_msg, sent_msg
    game_active = False
    output = None
    client_phase = RECV0
    first_send_itter = True

    # creating a socket and connecting to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
        try:
            soc.connect((my_host, my_port))
        except OSError as e:
            print(e.strerror)
            soc.close()
            return

        first_rec0_itter = True
        while(True):
            # establish connection with server
            readable, writable, _ = select([soc, sys.stdin], [soc], [], 10)

            if client_phase == RECV0:
                if first_rec0_itter:
                    first_rec0_itter = False
                # client is waiting to see if his connection was accepted or rejected
                if sys.stdin in readable:
                    # user input while not need to be
                    break
                if soc in readable:
                    res = recv(soc, SERVER_MESSAGE0_SIZE)
                    if res == 1:
                        # all wall received
                        connection_status = struct.unpack(">i", recv_msg)[0]

                        if connection_status == REJECTED:
                            print("You are rejected by the server.")
                            break

                        if connection_status == PLAYING:
                            print("Now you are playing against the server!")
                            client_phase = RECV1

                        if connection_status == WAITING:
                            print("Waiting to play against the server.")

                        recv_msg = b''
                        continue

                    if res == 2:
                        # not all was recieved, need to continue reading
                        continue

                    else: # res==0
                        # there was an error
                        break

            if client_phase == RECV1:
                # client will recv the game and heaps status and print it to the user
                if sys.stdin in readable:
                    # user input while not need to be
                    break
                res = recv(soc, SERVER_MESSAGE1_SIZE)
                if res == 1:
                    # all was recieved
                    n_a, n_b, n_c, game_status = struct.unpack(">iiii", recv_msg)
                    print_heaps(n_a, n_b, n_c)
                    recv_msg = b''
                    if game_status == PLAYERS_TURN:
                        print("Your turn:")
                        client_phase = SEND
                        first_send_itter = True
                        continue
                    elif game_status == SERVER_WINS:
                        print("Server win!")
                        break
                    elif game_status == PLAYER_WINS:
                        print("You win!")
                        break

                if res == 2:
                    # not all was received, need to continue reading
                    continue

                else:  # res==0
                    # there was an error
                    break

            if client_phase == SEND:
                if first_send_itter:
                    first_send_itter = False
                if soc in readable:
                    # server sent message when not suppose to, means it disconnected
                    print("Disconnected from server")
                    break

                if sys.stdin in readable and soc in writable:
                    user_input = sys.stdin.readline()
                    play = user_input.split()
                    heap_enum, num_to_send = create_turn_to_send(play)
                    msg = struct.pack(">ii", heap_enum, num_to_send)
                    res = send(soc, msg)
                    if res == 1:
                        # all was sent
                        client_phase = RECV2
                        if heap_enum == QUIT:
                            break
                        continue
                    if res == 2:
                        # not all was sent, need to continue sending
                        continue
                    if res == 0:
                        break

            if client_phase == RECV2:
                if sys.stdin in readable:
                    # user input while not need to be
                    break

                res = recv(soc, SERVER_MESSAGE2_SIZE)
                if res == 1:
                    # all was received
                    server_response = struct.unpack(">i", recv_msg)[0]

                    if server_response == PLAYER_ILLEAGL_MOVE:
                        print("Illegal move")
                    elif server_response == PLAYER_MOVE_ACCEPTED:
                        print("Move accepted")
                    else:
                        print("got some error from server response: ", server_response)
                        break
                    client_phase = RECV1
                    recv_msg = b''
                    continue

                elif res == 2:
                    # not all was received, need to continue reading
                    continue

                else:  # res==0
                    # there was an error
                    break


# This function starts client
# Gets the arguments for the client's program and sends them to the nim_game_client function.
# Wraps the nim_game_server function in case of an error.
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
