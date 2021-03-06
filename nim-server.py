#!/usr/bin/python3
import socket
import sys
import struct
import errno
from shared_global import *

play_list = []
wait_list = []
players_status = {}
reading_dict = {}
writing_dict = {}
num_players = 0
wait_list_size = 0
heap_nums = []
new_clients = []
new_client_status_dict = {}

# Server game stages:
SEND1 = 50
RECV = 51
SEND2 = 52


# Checks if given move is legal, against given clients heaps.
def is_legal_move(client, move):
    if move[1] <= 0 or players_status[client][move[0]] - move[1] < 0:
        return False
    return True


# Checks if the given client's heaps are all 0, hence someone won.
def is_win(client):
    for i in range(0, 3):
        if players_status[client][i] != 0:
            return False
    return True


# Executes a server move against given client.
# Removes 1 from largest heap. if more then one - then from lowest index
def exec_server_move(client):
    max_index = 0
    max_heap = 0

    for i in range(0, 3):
        if players_status[client][i] > max_heap:
            max_heap = players_status[client][i]
            max_index = i
    players_status[client][max_index] -= 1

    if is_win(client):
        players_status[client][3] = SERVER_WINS


#  Removes the given client from all lists and dictionaries he is in.
#  If he is not from the waiting list, and that list is not empty, then the next
#  client from the waiting list starts playing.
def remove_playing_client(client):
    waiting_client = False
    if client in play_list:
        play_list.remove(client)
    players_status.pop(client, None)
    reading_dict.pop(client, None)
    writing_dict.pop(client, None)
    if client in wait_list:
        wait_list.remove(client)
        waiting_client = True
    if client in new_clients:
        new_clients.remove(client)

    if len(wait_list) != 0 and not waiting_client:
        new_playing_client = wait_list.pop(0)
        play_list.append(new_playing_client)
        new_clients.append(new_playing_client)
        players_status[new_playing_client] = \
            [heap_nums[0], heap_nums[1], heap_nums[2], PLAYERS_TURN, SEND1]
            # [heapA, heapB, heapC, Game status, game stage]
        reading_dict[new_playing_client] = b''
        connection_msg = PLAYING
        writing_dict[new_playing_client] = struct.pack(">i", connection_msg)


#  Removes the given waiting client from all lists and dictionaries he is in.
def remove_waiting_client(client):
    writing_dict.pop(client, None)
    wait_list.remove(client)
    if client in new_clients:
        new_clients.remove(client)


#  executes the given players move, saved in reading_dict[client]
#  returns 0 if player asked to quit, 1 otherwise
def exec_client_move(client):
    move = struct.unpack(">ii", reading_dict[client])
    server_response = None
    if move[0] == QUIT:
        # Client ended the game.
        return 0

    elif move[0] == ILLEGAL_HEAP_INPUT:
        # the move received from the player was illegal.
        server_response = PLAYER_ILLEAGL_MOVE
    else:
        if is_legal_move(client, move):
            # the player's move is legal so we update the heaps accordingly.
            players_status[client][move[0]] -= move[1]  # heaps[move[0]] -= move[1]
            server_response = PLAYER_MOVE_ACCEPTED
            if is_win(client):
                players_status[client][3] = PLAYER_WINS
        else:
            # Illegal player move
            server_response = PLAYER_ILLEAGL_MOVE
    writing_dict[client] = struct.pack(">i", server_response)
    return 1


# Gets the listening socket and tries to accept a new client.
# If succeeds, prepares the relevant connection_msg according to available room,
# and enters the new client to the relevant list (playing or waiting) if there is room.
# returns 0 on failure to accept new client, 1 on success
def handle_new_client(listen_soc):
    try:
        conn_sock, address = listen_soc.accept()
    except socket.error as e:
        # Failed specific "accept". continue to try again next iteration
        print(e.strerror)
        return 0

    connection_msg = None
    if len(play_list) < num_players:
        play_list.append(conn_sock)
        players_status[conn_sock] = \
            [heap_nums[0], heap_nums[1], heap_nums[2], PLAYERS_TURN, SEND1]
            # [heapA, heapB, heapC, Game status, game stage]
        reading_dict[conn_sock] = b''
        connection_msg = PLAYING
    elif len(wait_list) < wait_list_size:
        wait_list.append(conn_sock)
        connection_msg = WAITING
    else:
        connection_msg = REJECTED

    #  Add client to list of new clients that need to get message
    new_clients.append(conn_sock)
    writing_dict[conn_sock] = struct.pack(">i", connection_msg)
    return 1


# Sends message that is saved in writing_dict[client], to client
# returns 1 if succeeded in sending complete message
# returns 2 if sent part of message, returns 0 for errors
def send(client):
    # connected client is readable, we will read it
    if len(writing_dict[client]) > 0:
        try:
            sent = client.send(writing_dict[client])
        except OSError as err:
            if err == errno.EPIPE or err == errno.ECONNRESET:
                print("Disconnected from client")
                return 0
            else:
                print("Error:", err.strerror)
                return 0
        if sent != 0 and sent < len(writing_dict[client]):
            writing_dict[client] = writing_dict[client][sent:]
            return 2
        if sent == len(writing_dict[client]):
            writing_dict[client] = b''
            return 1


# Receives message from client into reading_dict[client]
# returns 0 on error, 1 if finished receiving all, 2 if received part of message
def recv(client):
    # connected client is readable, we will read it
    try:
        msg = client.recv(CLIENT_MESSAGE_SIZE - len(reading_dict[client]))
    except OSError as err:
        if err == errno.ECONNREFUSED:
            print("Disconnected from client")
            return 0
        else:
            print(err.strerror)
            return 0
    if not msg:
        print("Disconnected from client")
        return 0
    reading_dict[client] += msg

    if len(reading_dict[client]) < CLIENT_MESSAGE_SIZE:
        return 2
    return 1


# This function is responsible for the server socket connection and the server game logic.
# It starts a socket, with socket, bind and listen commands.
# It constantly listens to new client connections, and plays the game against all playing clients.
# When a connection is closed, continues with the other clients.
# In case of an error, the server closes the connection and the function returns.
def nim_game_server(my_port):
    # creating a socket with socket, bind and listen commands.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listen_soc:
        try:
            listen_soc.bind(('', my_port))
        except OSError as e:
            print(e.strerror)
            listen_soc.close()
            return

        try:
            listen_soc.listen(1)
        except socket.error as e:
            print(e.strerror)
            listen_soc.close()
            return

        while True:
            readable, _, _ = select([listen_soc], [], [], 10)
            if listen_soc not in readable:
                # selected got timeout
                continue

            # there is a new client
            if handle_new_client(listen_soc) == 0:
                # there was an error during accept, continue to listen
                continue

            while len(play_list) != 0:
                readable, writeable, _ = select(play_list + wait_list + [listen_soc], play_list + new_clients, [], 10)
                for readable_sock in readable:

                    if readable_sock in wait_list:
                        print("Client from Waiting list disconnected")
                        remove_waiting_client(readable_sock)

                    elif readable_sock == listen_soc:
                        # there is a new client trying to connect
                        if handle_new_client(readable_sock) == 0:
                            # there was an error during accept, continue to listen
                            continue

                    elif readable_sock in play_list and players_status[readable_sock][-1] == RECV:
                        recv_stat = recv(readable_sock)
                        if recv_stat == 0:
                            remove_playing_client(readable_sock)
                        if recv_stat == 1:
                            # the client finished sending his msg
                            if exec_client_move(readable_sock) == 0:
                                # client ended the game and to be removed
                                remove_playing_client(readable_sock)
                                continue
                            reading_dict[readable_sock] = b''
                            players_status[readable_sock][-1] = SEND2

                    else:
                        print("Client sent unexpected message, removing him.")
                        remove_playing_client(readable_sock)

                for writable_sock in writeable:
                    if writable_sock in new_clients:
                        # we need to send him if he is now on playing list, wait list or rejected
                        send_stat = send(writable_sock)  # Return 1 if completed, 2 if not completed, 0 on error
                        if send_stat == 1:
                            # all was sent
                            new_clients.remove(writable_sock)
                            if writable_sock in play_list:
                                writing_dict[writable_sock] = struct.pack(">iiii", heap_nums[0], heap_nums[1],
                                                                          heap_nums[2], PLAYERS_TURN)
                            else:  # socket not in playing list
                                writing_dict.pop(writable_sock)
                        elif send_stat == 0:
                            new_clients.remove(writable_sock)
                            remove_playing_client(writable_sock)
                        continue

                    if writable_sock not in players_status:
                        continue
                    player = players_status[writable_sock]

                    if player[-1] == SEND1:  # SEND1 means we are sending the client his game status.
                        send_stat = send(writable_sock)
                        if send_stat == 1:
                            players_status[writable_sock][-1] = RECV
                        elif send_stat == 0:  # error
                            remove_playing_client(writable_sock)

                    if player[-1] == SEND2:  # SEND2 means we are sending the client if his move was iilegal or accepted
                        send_stat = send(writable_sock)
                        if send_stat == 1:
                            if player[3] != PLAYER_WINS:
                                exec_server_move(writable_sock)
                            writing_dict[writable_sock] = struct.pack(">iiii", player[0], player[1], player[2],
                                                                      player[3])
                            players_status[writable_sock][-1] = SEND1
                        elif send_stat == 0:  # error
                            remove_playing_client(writable_sock)


# This function starts the server
# Gets the arguments for the server program and saves them in the global variables.
# Wraps the nim_game_server function in case of an error.
def start_server():
    global num_players, wait_list_size, heap_nums
    if len(sys.argv) == 7:
        port = int(sys.argv[6])
    elif len(sys.argv) == 6:
        port = 6444
    else:
        print("Illegal number of arguments!")
        return
    try:
        heap_nums = [int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])]
        num_players = int(sys.argv[4])
        wait_list_size = int(sys.argv[5])
        nim_game_server(port)
    except OSError as err:
        if err.errno == errno.ECONNREFUSED:
            print("connection failed")
        else:
            print(err.strerror)


start_server()
