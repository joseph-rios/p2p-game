"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""

from session import Session
from browser import Browser
from lobby import Lobby
import game, socket, threading, time
import tkinter as tk

# The server's host address and port number should be constant
# and determined by the machine running the server.
# -   127.0.0.1, just for testing at the moment
# -   56569, random port I made up; could change
SERVER_HOST, SERVER_PORT = "127.0.0.1", 56569

# Make sure we're the main thread
if __name__ == "__main__":
    
    # Loop until the user closes any of the windows
    while True:
        # Create a new Session object to hold the information
        #   necessary for multiplayer
        client_session = Session()

        # Connect to the matchmaking server
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.connect((SERVER_HOST, SERVER_PORT))

        # Launch a level-browser instance to handle the specifics
        #   of the multiplayer process
        browser_gui = Browser(server_sock, client_session)
        browser_gui.start()

        # If we return from the browser but a specific flag hasn't
        #   been set, go ahead and close the program
        if not browser_gui.ready_for_lobby:
            server_sock.send("bye".encode())
            server_sock.close()
            exit()
        
        # Launch a lobby instance so that the host knows when the
        #   other player is ready to begin
        lobby_gui = Lobby(server_sock, client_session)
        lobby_gui.start()

        # Once we're out of the lobby, we should no longer need
        #   to communicate with the matchmaking server
        server_sock.send("bye".encode())
        server_sock.close()

        # If we return from the lobby but a specific flag hasn't
        #   been set, go ahead and close the program
        if not lobby_gui.ready_for_game:
            exit()
            
        # Load the selected level for the match and start the 
        #   game's mainloop
        game.load("levels/" + client_session.session_level + ".lvl")
        game_gui = game.Game(client_session)
        game_gui.mainloop()