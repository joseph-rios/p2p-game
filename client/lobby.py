"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""

import tkinter as tk
import os, socket
import threading

class Lobby:

    def __init__(self, server_sock, session):
        self.WIDTH, self.HEIGHT = 320, 240
        self.root = tk.Tk()

        self.server_sock = server_sock
        self.session = session
        self.ready_for_game = False

        self.setup_root()
        self.download_level()
        if self.session.is_host :
            self.waitThread = threading.Thread(name="waiter", daemon=True, target=self.waiter)
            self.waitThread.start()

    """
        This function starts the window mainloop
    """
    def start(self):
        self.root.mainloop()

    """
        This function destroys the window
    """
    def destroy(self):
        self.root.destroy()
        
    """
        This function sets up the root window settings and
        adds the other necessary widgets
    """
    def setup_root(self):
   
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate where to place the window such that
        # it is centered within the user's screen
        xpos = (screen_width / 2) - (self.WIDTH / 2)
        ypos = (screen_height / 2) - (self.HEIGHT / 2)
        
        self.root.title("Session Lobby")
        self.root.resizable(False, False)
        self.root.geometry("{}x{}+{}+{}".format(self.WIDTH,
                                                self.HEIGHT,
                                                int(xpos),
                                                int(ypos)))

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)

        if self.session.is_host:
            self.button = tk.Button(self.root, text="Start Game",
                                    command=self.start_game, state=tk.DISABLED)

            self.button.grid(row=0, column=0)

        else:
            self.button = tk.Button(self.root, text="Ready", command=self.ready_up)
            self.button.grid(row=0, column=0)

    """
        This function receives the level file from the server
    """
    def download_level(self):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "levels")
        levels = [
                    os.path.splitext(l)[0] for l in \
                    os.listdir(path) \
                    if os.path.isfile(os.path.join(path, l)) \
                    and l[-4:] == ".lvl"
                 ]
        if self.session.session_level not in levels:
            self.server_sock.send("download{}".format(self.session.session_level).encode())
            filesize = int(self.server_sock.recv(1024).decode())
            self.server_sock.send("OK".encode())

            with open(os.path.join(path, self.session.session_level+".lvl"), "wb") as f:
                while (filesize > 0):
                    chunk = self.server_sock.recv(1024)
                    f.write(chunk)
                    filesize -= 1024

    """
        This function sends an OK message to the other player
        and then destroys the window and becomes ready to
        start the game
    """
    def start_game(self):
        self.conn.send("OK".encode())
        self.conn.close()
        self.ready_for_game = True
        self.destroy()

    """
        This function starts a thread to wait for the
        other player to be ready
    """
    def ready_up(self):
        self.waitThread = threading.Thread(name="waiter", daemon=True, target=self.readyWaiter)
        self.waitThread.start()
        self.button['state'] = 'disabled'
        self.readyChecker()

    """
        This function checks if we're ready to start the game,
        if not, check again in half a second
    """
    def readyChecker(self):
        if(self.ready_for_game):
            self.destroy()
            return
        self.root.after(500,self.readyChecker)

    """
        This function initiates a TCP connection to the other
        player and waits for them to become ready
    """
    def readyWaiter(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.session.session_ip = (self.session.session_ip, 25565)
        sock.connect(self.session.session_ip)
        self.session.my_port = 25566

        sock.send("ready{}".format(self.session.client_name).encode())
        while True:
            data = sock.recv(1024)
            if data.decode() == "OK":
                break

        sock.close()
        self.ready_for_game = True

    """
        This function waits for the other player to become ready
        and receives their name to be used in the game
    """
    def waiter(self):
        host_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host_sock.bind(('', 25565))
        self.session.my_port = 25565

        host_sock.listen(1)
        self.conn, addr = host_sock.accept()
        self.session.session_ip = (addr[0], 25566)

        while True:
            data = self.conn.recv(1024)
            if data.decode()[:5] == "ready":
                self.session.client_name = data.decode()[5:]
                break
                
        self.button['state'] = 'normal'
