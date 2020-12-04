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


def is_legal_move(client, move):
    if move[1] <= 0 or players_status[client][move[0]] - move[1] < 0:
        return False
    return True


def is_win(client):
    for i in range(0, 3):
        if players_status[client][i] != 0:
            return False
    return True


def exec_server_move(client):
    # removes 1 from largest heap. if more then one - then from lowest index
    max_index = 0
    max_heap = 0

    for i in range(0, 3):
        if players_status[client][i] > max_heap:
            max_heap = players_status[client][i]
            max_index = i
    players_status[client][max_index] -= 1

    if is_win(client):
        players_status[client][3] = SERVER_WINS


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
        new_playing_client = wait_list.pop()
        play_list.append(new_playing_client)
        new_clients.append(new_playing_client)
        players_status[new_playing_client] = \
            [heap_nums[0], heap_nums[1], heap_nums[2], PLAYERS_TURN,
             SEND1]  # [heapA, heapB, heapC, Game status, game stage]
        #  TODO - need to send this client "now playing" message (add to new_client list?)
        reading_dict[new_playing_client] = b''
        connection_msg = PLAYING
        writing_dict[new_playing_client] = struct.pack(">i", connection_msg)
        print("%% new client in play list:")
        print("Connection msg:", connection_msg)


#  executes the given players move, saved in reading_dict[client]
# returns 0 if player asked to quit, 1 otherwise
def exec_client_move(client):
    move = struct.unpack(">ii", reading_dict[client])
    print("Client move accepted is:", move)
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
    print("server response to client move:", server_response)
    return 1


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
        print("Added new client to play_list. {} Places left.".format(num_players - len(play_list)))
        players_status[conn_sock] = \
            [heap_nums[0], heap_nums[1], heap_nums[2], PLAYERS_TURN,
             SEND1]  # [heapA, heapB, heapC, Game status, game stage]
        reading_dict[conn_sock] = b''
        connection_msg = PLAYING
    elif len(wait_list) < wait_list_size:
        wait_list.append(conn_sock)
        print("Added new client to wait_list. {} Places left.".format(wait_list_size - len(wait_list)))
        connection_msg = WAITING
    else:
        print("No more slots left for new client. Rejected.")
        connection_msg = REJECTED

    #  Add client to list of new clients that need to get message
    new_clients.append(conn_sock)
    writing_dict[conn_sock] = struct.pack(">i", connection_msg)
    print("***new client in dict:")
    print("connection message:", connection_msg)
    return 1


# sends message that is saved in writing_dict[client], to client
# returns 1 if succeeded in sending complete messgae
# returns 2 if sent part of message, returns 0 for errors
def send(client):
    # connected client is readable, we will read it
    print("trying to send: ", writing_dict[client])
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


#  ToDo - recognise if client in wait_list has disconnencted, and remove from wait list
# this function is responsible for the server socket connection and the server game logic.
# it starts a socket, with socket, bind and listen commands.
# when a client tries to connect, it accepts a single connection and the game begins.
# when the connection is closed, returns to listening until a new client connect.
# in case of an error, the server closes the connection and the function returns.
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
                # there was an error during accept
                continue
                # todo- there was an error during accept. continue? end game?

            while len(play_list) != 0:
                readable, writeable, _ = select(play_list + [listen_soc], play_list + new_clients, [], 10)
                for readable_sock in readable:

                    if readable_sock == listen_soc:
                        # there is a new client trying to connect
                        print("Server trying to accept new client")
                        if handle_new_client(readable_sock) == 0:  # there was an error during accept
                            # todo - end game? continue with others?
                            continue

                    elif readable_sock in play_list and players_status[readable_sock][-1] == RECV:
                        print("Server in phase RECV, trying to receive from client")
                        recv_stat = recv(readable_sock)
                        if recv_stat == 0:
                            print("Error with receiving from client")
                            remove_playing_client(readable_sock)
                        if recv_stat == 1:
                            print("Client message received successfully: ", reading_dict[readable_sock])
                            # the client finished sending his msg
                            if exec_client_move(readable_sock) == 0:
                                # client ended the game and to be removed
                                remove_playing_client(readable_sock)
                                continue
                            reading_dict[readable_sock] = b''
                            players_status[readable_sock][-1] = SEND2

                    else:
                        # TODO - handle socket that sent not when supposed to - probably closed
                        print("Client sent unexpected message. Removing from list.")
                        remove_playing_client(readable_sock)

                # # checks what client messages have been fully received, and executes the move
                # for client, msg in reading_dict.items():
                #     if len(msg) == CLIENT_MESSAGE_SIZE:
                #         print("Client message received succesfully: ", msg)
                #         # the client finished sending his msg
                #         if exec_client_move(client) == 0:
                #             # client ended the game and to be removed
                #             remove_playing_client(client)
                #             continue
                #         reading_dict[client] = b''
                #         players_status[client][-1] = SEND2

                for writable_sock in writeable:
                    if writable_sock in new_clients:
                        # we need to send him if he is now on playing list, wait list or rejected
                        print("Server trying to send init message to new client")
                        send_stat = send(writable_sock)  # Return 1 if completed, 2 if not completed, 0 on error
                        if send_stat == 1:
                            # all was sent
                            print("Server succeeded sending init message to new client")
                            new_clients.remove(writable_sock)
                            if writable_sock in play_list:
                                writing_dict[writable_sock] = struct.pack(">iiii", heap_nums[0], heap_nums[1],
                                                                          heap_nums[2], PLAYERS_TURN)
                            else:  # socket not in playing list
                                writing_dict.pop(writable_sock)
                        elif send_stat == 0:
                            print("Error in sending client init message")
                            new_clients.remove(writable_sock)
                            remove_playing_client(writable_sock)
                        continue

                    #  TODO - handle dict lookups when client already disconnected and not in them
                    if writable_sock not in players_status:
                        continue
                    player = players_status[writable_sock]

                    if player[-1] == SEND1:  # SEND1 means we are sending the client his game status.
                        print("Server in phase SEND1")
                        send_stat = send(writable_sock)
                        if send_stat == 1:
                            players_status[writable_sock][-1] = RECV
                            print("Server Succeeded with SEND1")
                        elif send_stat == 0:  # error
                            print("Error with send1 to client")  # TODO - decide what to do with error in specific socket
                            remove_playing_client(writable_sock)

                    if player[-1] == SEND2:  # SEND2 means we are sending the client if his move was iilegal or accepted
                        print("Server in phase SEND2")
                        send_stat = send(writable_sock)
                        if send_stat == 1:
                            print("Server Succeeded with SEND2")
                            if player[3] != PLAYER_WINS:
                                exec_server_move(writable_sock)
                            writing_dict[writable_sock] = struct.pack(">iiii", player[0], player[1], player[2],
                                                                      player[3])
                            players_status[writable_sock][-1] = SEND1
                        elif send_stat == 0:  # error
                            print("Error with send2 to client")  # TODO - decide what to do with error
                            remove_playing_client(writable_sock)


"""
def old_way():
                    # created a connection with a client. the games starts with full heaps.
                    # for each new connection we will restart the heaps sizes
                    #the game starts with the player's turn
                    status = PLAYERS_TURN

                    while True:
                        # While client is still playing / connection is alive
                        # 1) Send to the client the current heap values and game status
                        data = struct.pack(">iiii", heaps[0], heaps[1], heaps[2], status)
                        send_status = send_all(conn_sock)
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
                                """


# this function starts the server
# gets the arguments for the server program and sends them to the nim_game_server function.
# wraps the nim_game_server function in case of an error.
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
