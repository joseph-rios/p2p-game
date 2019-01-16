# CSC 565 Networking Final Project

### Authors: Slate Hayes, Joseph Rios, David Williams
### Course: CSC 565
### Instructor: Dr. Katangur
### Date: 12/6/18

# Requirements
* Python 3
* Modules:
 * tkinter

# Usage

### Server
1. Run the server python file:
    * $ python server.py

### Clients
1. Run the client python file:
    * $ python client.py
2. Enter a name alias for yourself
    * names are validated such that they should not contain spaces and should not be too long
3. You may click the refresh button to get an update list of available sessions from the server
4. Either host a session or connect to another player's
5. If hosting a session:
    * Enter a name for your session (this will be how other players distinguish your session from others)
    * Choose whether or not you want to require a password to join your session
    * Select a level from the list to play on
    * Once in the lobby:
        * Wait for the other player to connect to your session
        * When the start button becomes enabled, click it to begin the game
6. If connecting to another session:
    * Select the session you want to play on from the session-list
    * If the session has a password required, enter it
    * Click the connect button to establish your connection to the other player
    * Once in the lobby:
        * Click the ready button to signal to the host that you are ready to proceed with the game
        * Wait for the host to initiate the game

### Editor
1. Run the editor python file:
    * $ python editor.py
2. Place your desired game objects into the level
    * Two players are required for the game to work
3. Connect wires to doors and buttons to establish links between powerable objects and power sources
4. Select objects to move them in the level
5. Erase objects to delete them from the level
6. Use the file menu bar at the top of the window to open, save, or upload your levels

# Gameplay
### Objects
* Blocks
    * Solid objects that the player collides with
* Wires and CWires
    * Non-collidable objects that connect a power source to a powerable object
* Buttons
    * Non-collidable objects that provide power to wires
* Doors
    * Solids objects that the player can traverse only when receiving power from a wire
* Goals
    * Non-collidable objects that players press in order to win the game
    * All goal objects must be pressed in order for the game to be won