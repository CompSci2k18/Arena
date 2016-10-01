#!/usr/bin/env python3
from cgitb import enable
enable()
from shelve import open as shelf
from os import environ
from http.cookies import SimpleCookie
from cgi import FieldStorage
from json import dumps, loads
from threading import Lock

# Get the version of this file that is required, and return the necessary
# json
form_data = FieldStorage()
start_up = form_data.getfirst('start_up', False)
# try:
cookie = SimpleCookie()
cookie.load(environ['HTTP_COOKIE'])
filename = cookie['filename'].value
player_num = int(cookie['player_num'].value)

# Open the shelf and send the json, using mutexes
mutex = Lock()
mutex.acquire(False)
gamefile = shelf('../games/' + filename, writeback = True)
if start_up:
    # Send out the json for all the players with the local key
    # Once the game starts, prevent it from being joined
    gamefile['joinable'] = False
    gamefile['started'] = True
    i = 0
    ready = True
    players = gamefile['players']
    for player in players:
        if i == player_num:
            player['local'] = True
            player['ready'] = True
        else:
            player['local'] = False
        ready = ready and player['ready']
        i += 1
    gamefile['players'] = players
    data = {'players': players, 'ready': ready}

else:
    # Update the player that is sent and send back all players
    # Receive player data in two pieces
    player = form_data.getfirst('player')
    player2 = form_data.getfirst('player2')
    if player and player2:
        player = loads(player + player2)
        players = gamefile['players']
        players[player['id']] = player
        gamefile['players'] = players
        data = {'players': players}


# except Exception as e:
#     data = {'error': e}

gamefile.close()
mutex.release()
print('Content-Type: application/json; charset=utf-8')
print()
print(dumps(data))
