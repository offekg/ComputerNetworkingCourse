import socket
# Player moves
HEAP_A = 0
HEAP_B = 1
HEAP_C = 2
ILLEGAL_HEAP_INPUT = 4
QUIT = 5

# Server Responses
PLAYER_ILLEAGL_MOVE = 20
PLAYER_MOVE_ACCEPTED = 21

# Game status
PLAYERS_TURN = 10
SERVER_WINS = 11
PLAYER_WINS = 12


def send_all(soc, data):
    while len(data)!=0:
        try:
            sent=soc.send(data)
        except OSError as err:
            print(err.strerror)
            return False
        if sent is not None and sent<len(data):
            data=data[sent:]
    return True
