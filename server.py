from datetime import datetime
from hashlib import sha256
from json import dumps, loads
from random import choice
from select import select
from socket import *
from sys import exit
from threading import Thread
from urllib.request import unquote

"""/*
    
    Class: Server
    A custom server written in Python3.4 for use as the backend for this game.
    Uses a simple protocol when receiving messages from the players.
    Multithreaded for increased speed, especially during the actual game.
*/"""
class ArenaServer:

    # Group: Constructors

    """/*
        Constructor: __init__
        Initialises the server and binds it to the host and port specified

        Parameters:
            string host - The host ip of the server. Is usually the local machine
            int port - The port number of the server. Default is 44444
    */"""
    def __init__(self, host, port):
        # Group: Variables

        # string: host
        # The address of the host. Generated by this program
        self.host = host

        # int: port
        # The port number the socket will bind to. Default 44444.
        self.port = port

        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        # obj: sock
        # The <Socket> the server listens on        
        self.sock = sock

        # Game var setup

        # boolean: started
        # False while the server is still in the lobby, True once game starts
        self.started = False

        # boolean: host_start
        # False until the host clicks the Start Game button.
        self.host_start = False

        # array: players
        # <List> of player JSON objects in the lobby
        self.players = [None for _ in range(4)]

        # int: lobby_size
        # The amount of players currently in the lobby
        self.lobby_size = 0

        # hash: tokens
        # Dict of usernames against their tokens
        self.tokens = {}

        width = height = 650

        # array: coords
        # <List> of <Coordinates> objects players can spawn in
        self.coords = [
            (width / 4, height / 4),
            ((3 * width) / 4, height / 4),
            (width / 4, (3 * height) / 4),
            ((3 * width) / 4, (3 * height) / 4)
        ]

        """/* 
            array: player_objects
            <List> of the <Player> objects created in Javascript for all
            players in the game

            Note:
                They are <Player> objects in JavaScript, but Python stores them
                as dicts
        */"""
        self.player_objects = []

    # Group: Public Methods

    """/*
        Function: close
        Closes the server and releases the socket
    */"""
    def close(self):
        print('Server Closing')
        self.sock.close()

    """/*
        Function: listen
        Listen for incoming connections and pass them off to the handler methods
        in a new thread
    */"""
    def listen(self):
        self.sock.listen(10)
        print('Lobby Open')
        # Lobby loop
        while not self.started:
            connections, wlist, xlist = select([self.sock], [], [], 0.05)

            for connection in connections:
                client, address = connection.accept()
                client.settimeout(5)
                Thread(
                    target=self._handleLobbyConnection,
                    args=(client, address)).start()
        print('Game Starting')
        while True:  # TODO - Change to end loop when game is over
            connections, wlist, xlist = select([self.sock], [], [], 0.05)

            for connection in connections:
                client, address = connection.accept()
                client.settimeout(10)
                Thread(
                    target=self._handleGameConnection,
                    args=(client, address)).start()

    """/*
        Group: Private Methods
        Note:
            Being developer docs, there are private methods that have been
            documented here.

            Any method prefixed with _ is considered private in Python by
            convention, and should not be called outside of the containing
            class
    */"""

    """/*
        Function: _handleLobbyConnection
        Method run in a separate thread to handle requests while the game is still
        in the lobby state
        
        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client

        Returns:
            The results of <_lobbyJoin>, <_lobbyQuery>, or <_lobbyStart>,
            depending on the message from the client
    */"""
    def _handleLobbyConnection(self, client, address):
        # Callback on client connection, pass off to correct function
        msg = client.recv(256).decode()
        callback = None
        if 'join' in msg:
            callback = self._lobbyJoin
        elif 'query' in msg:
            callback = self._lobbyQuery
        elif 'start' in msg:
            callback = self._lobbyStart
        elif 'token' in msg:
            callback = self._lobbyGetToken

        if callback:
            callback(client, address, msg)
        client.close()
        return

    """/*
        Function: _lobbyJoin
        Handler for player joining the lobby

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            string msg - The msg that was sent by the client
                         Includes the username that the player has chosen

        Returns:
            string response - Either 'lobby full' if the lobby is full, or
                              'joined=' + the index of the player in the array
                              <players>
    */"""
    def _lobbyJoin(self, client, address, msg):
        # Handles players joining the lobby
        if self.lobby_size < 4 and not self.started:
            username = msg.split('=')[1]
            # Find the index for the player
            player_index = -1
            index_assigned = False
            username_count = 0
            for i in range(len(self.players)):
                player = self.players[i]
                if player == None and not index_assigned:
                    player_index = i
                    index_assigned = True
                elif player != None and player['userName'] == username:
                    username_count += 1
            if username_count > 0:
                username += ' (%i)' %(username_count)
            print(username, 'has joined the lobby!')
            # Get the player coords
            player_coords_index = choice(range(len(self.coords)))
            player_coords = self.coords[player_coords_index]
            self.coords.remove(player_coords)
            # Create the player lobby object
            player = {
                'x': player_coords[0],
                'y': player_coords[1],
                'userName': username,
                'colour': '#%s' % (self._generateColour()),
                'local': False,
                'queryTimeout': 20,
                'ready': False
            }
            self.lobby_size += 1
            self.players[player_index] = player
            # Generate the token
            token = sha256(
                str(datetime.now()).encode()).hexdigest()
            self.tokens[username] = token
            msg = 'joined=' + str(player_index) + ';' + token
            client.sendall(msg.encode())
        else:
            client.sendall('lobby full'.encode())

    """/*
        Function: _lobbyQuery
        Handler for AJAX querying the players in the lobby

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            string msg - The msg that was sent by the client
                         Includes the index of the player in the list of
                         players

        Returns:
            List players - <List> of player objects currently in the lobby

            boolean started - False if the game hasn't started, True otherwise
    */"""
    def _lobbyQuery(self, client, address, msg):
        # Handles queries against lobby
        player_num = int(msg.split('=')[1])
        self.players[player_num]['queryTimeout'] = 21
        for i in range(len(self.players)):
            player = self.players[i]
            if player != None:
                player['queryTimeout'] -= 1
                if player['queryTimeout'] <= 0:
                    self.coords.append((player['x'], player['y']))
                    self.players[i] = None
                    self.lobby_size -= 1
                    self.tokens.pop(player['userName'], None)
        client.sendall(dumps(
            {'players':
             [player for player in self.players if player is not None],
             'started': self.host_start}).encode())

    """/*
        Function: _lobbyStart
        Handler for the host starting the game

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            string msg - The msg that was sent by the client
                         Includes the index of the player in the list of players

        Returns:
            boolean ready - True if all players in the lobby are ready to
                            start, else False
    */"""
    def _lobbyStart(self, client, address, msg):
        player_num = int(msg.split('=')[1])
        self.players[player_num]['ready'] = True
        # If the server says the host has started, we need to move
        self.host_start = True
        self.started = True
        for player in self.players:
            if player is not None:
                self.started = self.started and player['ready']
        client.sendall(dumps(
            {'ready': self.players[player_num]['ready']}).encode())

    """/*
        Function: _lobbyGetToken
        If the <Join Game> script detects a pre-existing cookie on the browser,
        it will query the server to check its token to tell if this player
        already left the lobby and want to rejoin if the lobby has space

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            string msg - The msg that was sent by the client
                         Includes the index of the player in the list of players

        Returns:
            string token - The token of the player who sent the request
    */"""
    def _lobbyGetToken(self, client, address, msg):
        player_num = int(msg.split('=')[1])
        player = self.players[player_num]
        if player:
            username = player['userName']
            token = self.tokens[username]
            print(username, token)
            client.sendall(token.encode())
        else:
            client.sendall('rejoin'.encode())

    """/*
        Function: _handleGameConnection
        Method run in a separate thread to handle requests while the game is
        running

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            boolean repeat - Due to issues with http sockets, allow one re-run
                             of this handler to ensure message is received

        Returns:
            The results of <_gameStartUp> or <_gameUpdate>, depending on the
            message from the client
    */"""
    def _handleGameConnection(self, client, address, repeat=True):
        msg = client.recv(4096).decode()
        callback = None
        if 'start_up' in msg:
            callback = self._gameStartUp
        elif 'update' in msg:
            callback = self._gameUpdate

        if callback:
            callback(client, address, msg)
        elif repeat:
            self._handleGameConnection(client, address, False)
        client.close()
        return

    """/*
        Function: _gameStartUp
        Handler for players arriving at the game.html page for syncing up
        player data

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            string msg - The message that was sent by the client
                         Includes the index of the player in the list of players

        Returns:
            array players - Starting data for all players, to be turned
                            into <Player> objects in the JavaScript
            boolean ready - True if all players have run this method, else
                            False
    */"""
    def _gameStartUp(self, client, address, msg):
        # Handles players arriving at the game screen
        # Loop through the list of players, setting flags
        player_num = int(unquote(msg.split('start_up=')[1]))
        payload = []
        ready = True
        for i in range(len(self.players)):
            player = self.players[i]
            if player is not None:
                if i == player_num:
                    player['local'] = True
                    player['ready'] = True
                else:
                    player['local'] = False
                ready = ready and player['ready']
                payload.append(player)
        # Send the payload containing only the active players
        data = {'players': payload, 'ready': ready}
        response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: http://cs1.ucc.ie\r\n\r\n"
        response += dumps(data) + '\r\n'
        client.sendall(response.encode())

    """/*
        Function: _gameUpdate
        Handler for the AJAX updating player data for all players connected

        Parameters:
            Socket client - The <Socket> to send response through
            Tuple[string, int] address - <Tuple> containing address and port
                                         of the client
            string msg - The msg that was sent by the client
                         Includes a JSON string of the local players data

        Returns:
            array players - The current status of all players in the game
    */"""
    def _gameUpdate(self, client, address, msg):
        # Handles game updates on the server
        # MUST BE AS EFFICIENT AS POSSIBLE
        player = loads(unquote(msg.split('update=')[1]))
        try:
            self.player_objects[player['id']] = player
        except IndexError:
            self.player_objects.append(player)
        data = {'players': self.player_objects}
        response = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: http://cs1.ucc.ie\r\n\r\n"
        response += dumps(data)
        client.sendall(response.encode())

    """/*
        Function: _generateColour
        Generate a random colour for a player

        Returns:
            string colour - Random 6-digit hexadecimal string representing a
                            colour value
    */"""
    def _generateColour(self):
        return ''.join([choice('0123456789ABCDEF') for x in range(6)])

if __name__ == '__main__':
    # Set values for localhost
    hostname = gethostname()
    hostip = gethostbyname(hostname)
    port = 44444 # Do not change port if you want to make the server public
                 # (Password support coming soon)
    server_address = (hostip, port)
    print('SERVER ADDRESS DETAILS')
    print('PASS THE FOLLOWING TO YOUR FRIENDS')
    print('Address:', hostip)
    print('Port:', port)
    server = ArenaServer(hostip, port)
    try:
        server.listen()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    finally:
        server.close()
