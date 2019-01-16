"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""
from tkinter import *
from tkinter import messagebox as mb
import pickle
import math
import socket, threading
import time
from collections import deque

objs = []

"""
Game Window
 - Where all the game objects are drawn
 - Main Game loop in Game.draw()
 - Requires session object, so it knows where to send/recv data
 Usage:
     load("file.lvl")
     Game(session).mainloop()
"""
class Game(Frame):
    WIDTH = 600
    HEIGHT = 600
    me = None
    def __init__(self, session):
        Frame.__init__(self)
        Game.me = self
        self.gameOver = False
        self.master.title("Game")
        self.session = session
        self.pack()
        self.canvas = Canvas(width=Game.WIDTH, height=Game.HEIGHT, background='white')
        self.canvas.pack()

        # Bind controls to keys
        self.bind("<KeyPress-Up>", self.press)
        self.bind("<KeyRelease-Up>", self.release)
        self.bind("<KeyPress-Down>", self.press)
        self.bind("<KeyRelease-Down>", self.release)
        self.bind("<KeyPress-Right>", self.press)
        self.bind("<KeyRelease-Right>", self.release)
        self.bind("<KeyPress-Left>", self.press)
        self.bind("<KeyRelease-Left>", self.release)

        self.master.protocol("WM_DELETE_WINDOW", self.exit_desktop)
        self.menubar = Menu(self)
        menu = Menu(self.menubar, tearoff=0)
        menu.add_command(label="Exit to browser",command=self.exit_browser)
        menu.add_command(label="Exit to desktop",command=self.exit_desktop)
        self.menubar.add_cascade(label="Options",menu=menu)

        self.master.config(menu=self.menubar)
        
        self.focus_set()

        players = []
        self.objects = []
        self.interactives = []
        self.wires = []

        # Add objects to global list
        for n,obj in enumerate(objs):
            if str(type(obj)) == "<class 'game.Player'>":
                players.append(n)
            elif str(type(obj)) == "<class 'game.CosmeticWire'>":
                self.wires.append(obj)
            else:
                self.objects.append(obj)
                if obj.is_interactive():
                    self.interactives.append(obj)
                            
        player_no = 0 if session.is_host else 1
        self.player = objs[players.pop(player_no)]
        self.networkPlayer = objs[players[0]]

        # Set players as host and client for coloring their names
        if self.session.is_host:
            self.player.set_meta(self.session.host_name, True)
            self.networkPlayer.set_meta(self.session.client_name, False)
        else:
            self.player.set_meta(self.session.client_name, False)
            self.networkPlayer.set_meta(self.session.host_name, True)

        # Bind socket to send and receive P2P UDP messages
        self.deque = deque(maxlen=10)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.session.my_port))

        self.listenEvent = threading.Event()
        self.listenThread = threading.Thread(name="listen", daemon=True, target=self.listen)
        self.listenThread.start()

        self.init_draw()

    """
        Listens for incoming data from the other player
    """
    def listen(self):
        time.sleep(0.5)
        while not self.listenEvent.is_set():
            try:
                data = self.sock.recv(1024).decode().split(":")

                # If the data is a 'win' message, Game Over, otherwise add the positional data to the deque
                if data[0] == "win":
                    self.gameOver = True
                elif data[0] == "quit":
                    self.networkPlayer.erase(self.canvas)
                else:
                    self.deque.appendleft(tuple(data))
            except:
                continue
                
    """
        Destroys the game window and return to the session-browser
    """
    def exit_browser(self):
        self.sock.sendto("quit:now".encode(),
                         Game.me.session.session_ip)
        self.sock.close()
        self.after_cancel(self._after_job)
        self.listenEvent.set()
        self.master.destroy()

    """
        Destroys the game window and end the program
    """
    def exit_desktop(self):
        self.sock.sendto("quit:now".encode(),
                         Game.me.session.session_ip)
        self.sock.close()
        self.after_cancel(self._after_job)
        self.listenEvent.set()
        self.master.destroy()
        exit()
                
    """
        Adds an object to the list of objects
    """
    def add_object(self, obj):
        self.objects.append(obj)

    """
        Key-pressed input control callback
    """
    def press(self, event):
        self.player[event.keysym] = True
        self.player.face(event.keysym)

    """
        Key-released input control callback
    """
    def release(self, event):
        self.player[event.keysym] = False

    """
        Perform initial drawing operations then start the main draw-loop
    """
    def init_draw(self):
        for obj in objs:
            obj.init_draw(self.canvas)

        self._after_job = self.after(10, self.draw)

    """
        Draws and updates each game object
    """
    def draw(self):
        if Game.me.gameOver:
            mb.showinfo("YOU WIN", "(☞ﾟヮﾟ)☞")
            self.exit_browser()
        else:
            # Get the network player's positional data
            if len(self.deque) > 0:
                latest = self.deque.popleft()
                self.deque.clear()

                x = int(latest[0])
                y = int(latest[1])

                old_x, old_y, _, _ = self.networkPlayer.get_pos()
                old_x += Player.radius
                old_y += Player.radius

                if x < old_x:
                    self.networkPlayer.face('Left')
                elif x > old_x:
                    self.networkPlayer.face('Right')
                elif y < old_y:
                    self.networkPlayer.face('Up')
                elif y > old_y:
                    self.networkPlayer.face('Down')

                self.networkPlayer.set_pos((x - Player.radius,
                                            y - Player.radius),
                                           (x + Player.radius,
                                            y + Player.radius))

            if self.networkPlayer._blockID is not None:
                self.networkPlayer.draw(self.canvas)
                
            self.player.update()

            if self.networkPlayer.collide(self.player):
                self.player.shift(*self.networkPlayer.onCollide(self.player))

            # Perform operations for interactable objects
            for obj in self.interactives:
                obj.update()
                if obj.type_id() == 2:
                    self.canvas.lower(obj._wireID)
                if(obj.collide(self.networkPlayer)):
                    obj.onCollide(self.networkPlayer)
                if(obj.collide(self.player)):
                    obj.onCollide(self.player)
                    
            for wire in self.wires:
                wire.update(self.canvas)

            # Calculate player collisions with other objects
            for obj in self.objects:
                if obj.collide(self.player):
                    shiftx, shifty = obj.onCollide(self.player)
                    self.player.shift(shiftx, shifty)
                obj.draw(self.canvas)

            px, py, _, _ = self.player.get_pos()
            self.sock.sendto(("%d:%d" % (px + Player.radius, py + Player.radius)).encode(),
                              self.session.session_ip)

            self.player.draw(self.canvas)

            # Draw players on the correct layer, above other objects
            if self.networkPlayer._blockID is not None:
                self.canvas.lift(self.networkPlayer._blockID)
                self.canvas.lift(self.networkPlayer._arrowID)
                
            self.canvas.lift(self.player._blockID)
            self.canvas.lift(self.player._arrowID)

            if self.networkPlayer._blockID is not None:
                self.canvas.lift(self.networkPlayer._nameID)
            
            self.canvas.lift(self.player._nameID)

            self._after_job = self.after(10, self.draw)
"""
Block
 - Black Rectangle
 - When player collides, the block should stop them
"""
class Block:
    def __init__(self, pos1, pos2, color='black'):
        self.set_pos(pos1, pos2)
        self._color = color
        self._blockID = None

    def type_id(self): #Override
        return 0

    def params(self):
        return ((self._x1, self._y1), (self._x2, self._y2))

    def is_interactive(self):
        return False

    def set_pos(self, pos1, pos2):
        self._x1 = min(pos1[0],pos2[0])
        self._x2 = max(pos1[0],pos2[0])
        self._y1 = min(pos1[1],pos2[1])
        self._y2 = max(pos1[1],pos2[1])

    def get_pos(self):
        return (self._x1, self._y1, self._x2, self._y2)            

    """
        Create the image to be drawn on the canvas
    """
    def init_draw(self, canvas):
        self._blockID = canvas.create_rectangle(self._x1, self._y1,
                                                self._x2, self._y2,
                                                fill=self._color)

    """
        Manipulate the image's position based on its coordinates
    """
    def draw(self, canvas):
        canvas.coords(self._blockID, self._x1, self._y1, self._x2, self._y2)

    def erase(self, canvas):
        canvas.delete(self._blockID)
        self._blockID = None

    def collide(self, obj):
        min_newx, min_newy, max_newx, max_newy = obj.get_pos()
        return not (max_newx < self._x1 or min_newx > self._x2 or
                    max_newy < self._y1 or min_newy > self._y2)

    def inX(self, x):
        return x > self._x1 and x < self._x2

    def inY(self, y):
        return y > self._y1 and y < self._y2

    def onCollide(self, obj): #Return an amount to shift
        new_x1, new_y1, new_x2, new_y2 = obj.get_pos()
        old_x1, old_y1, old_x2, old_y2 = obj.getOldPos()

        if self.inX(old_x1) or self.inX(old_x2):
            if old_y1 < self._y1:
                return (0, self._y1 - new_y2)
            else:
                return (0, self._y2 - new_y1)

        elif self.inY(old_y1) or self.inY(old_y2):
            if old_x1 < self._x1:
                return (self._x1 - new_x2, 0)
            else:
                return (self._x2 - new_x1, 0)

        return (0,0)

"""
Wire
 - Block type wire, green rectangle
 - Powered by buttons and other wires
 - Can power doors
 - Wire blocks need to collide to connect
"""    
class Wire(Block):
    def __init__(self, pos1, pos2, color='green4'):
        Block.__init__(self, pos1, pos2, color)
        self._connections = {}
        self._powered = False
        self._wireID = None
        self._power_sources = [] # Objects that can give this wire power
        self._power_syncs = [] # Objects that this wire gives power

    def type_id(self):
        return 2

    def is_interactive(self):
        return True

    """
        Toggles the wires power, taking all connected wires'
        power states into consideration and applies power to syncs
    """
    def toggle_power(self, on):
        self._powered = on
        self._color = 'green2' if on else 'green4'
        for k, v in self._connections.items():
            if v._powered != on:
                v.toggle_power(on)
        if self._powered:
            for ps in self._power_syncs:
                ps.apply_power(Game.me.canvas)

    """
        Update the power state based on the wire's sources of power
    """
    def update(self):
        self.toggle_power(False)
        for ps in self._power_sources:
            if ps.pressed:
                self.toggle_power(True)
                break

    def init_draw(self, canvas):
        self._wireID = canvas.create_rectangle(self._x1, self._y1,
                                               self._x2,self._y2,
                                               fill=self._color, 
                                               outline=self._color)

        # Connect other wires to this one if they're touching
        for obj in objs:
            if obj.type_id() == 2:
                for o in objs:
                    if o.type_id() == 2 and obj._wireID != o._wireID \
                       and o._wireID not in obj._connections.keys():
                        if obj.collide(o):
                            obj.connect(o)
                        else:
                            obj.disconnect(o)

    def draw(self, canvas):
        canvas.coords(self._wireID, self._x1, self._y1, self._x2, self._y2)
        canvas.itemconfig(self._wireID, fill=self._color, outline=self._color)

    def erase(self, canvas):
        canvas.delete(self._wireID)

        self._wireID = None

    def connect(self, other):
        if other._wireID not in self._connections.keys():
            self._connections[other._wireID] = other
            other.connect(self)

    def disconnect(self, other):
        if other._wireID in self._connections.keys():
            del self._connections[other._wireID]
            other.disconnect(self)

    def onCollide(self, obj):
        return (0, 0)
        #return super().onCollide(obj)
        
"""
Cosmetic Wire
 - Line based wire, red/blue line strip
 - Red: Off  Blue: On
 - Requires an index of an object in the objs
   for the source and destination
   
"""
class CosmeticWire():
    def __init__(self,src,dst=None,points=[]):
        self._points = points
        self._src = src
        self._dst = dst
        self._powered = False
        self._ids = []

    def type_id(self):
        return 4

    def params(self):
        return (self._src,self._dst,self._points)

    def __len__(self):
        return len(self._points)

    def inX(self,x):
        return False

    def inY(self,y):
        return False

    def add_point(self,point):
        self._points.append(point)

    def set_src(self,obj_id):
        self._src = obj_id

    def get_src(self):
        return self._src

    def set_dst(self,obj_id):
        self._dst = obj_id

    def get_dst(self):
        return self._dst

    def set_src_pt(self,pos):
        self._points[0] = pos

    def set_dst_pt(self,pos):
        self._points[-1] = pos

    def init_draw(self,canvas):
        self._ids = []
        previous = self._points[0]
        for i in range(1,len(self._points)):
            self._ids.append(canvas.create_line(*previous,*self._points[i],fill="red"))
            previous = self._points[i]

    def draw(self,canvas):
        if(self._powered):
            color = "blue"
        else:
            color = "red"
        previous = self._points[0]
        for i in range(1,len(self._ids)):
            canvas.coords(self._ids[i], *previous, *self._points[i])
            canvas.itemconfig(self._ids[i],fill=color)
            previous = self._points[i]

    def erase(self,canvas):
        for i in self._ids:
            canvas.delete(i)

    def update(self,canvas):
        if(objs[self._src].is_powered()):
            self.powered = True
            objs[self._dst].apply_power(canvas)

"""
Door
 - Brown Rectangle
 - When powered, it is "open" and lets players pass through
 - When not powered, it is "closed" and blocks players
"""
class Door(Block):
    def __init__(self, pos1, pos2, color="saddlebrown"):
        Block.__init__(self, pos1, pos2, color)
        self._open = False

    def type_id(self):
        return 5

    def is_interactive(self):
        return True
        
    def is_source(self):
        return False

    def is_powerable(self):
        return True

    def update(self):
        self._open = False

    def init_draw(self, canvas):
        super().init_draw(canvas)
        for obj in objs:
            if obj.type_id() == 2 and self.collide(obj):
                obj._power_syncs.append(self)

    def draw(self, canvas):
        canvas.coords(self._blockID, self._x1, self._y1, self._x2, self._y2)
        if self._open:
            canvas.itemconfig(self._blockID, fill="white", outline=self._color)
        else:
            canvas.itemconfig(self._blockID, fill=self._color, outline="black")

    def onCollide(self, obj):
        return (0, 0) if self._open else super().onCollide(obj)
        
    def apply_power(self,canvas):
        self._open = True
        self.draw(canvas)

"""
Butten (to avoid name conflicts)
 - Square with a red circle in the middle
 - When a player collides, it is "pressed" and becomes powered
 - When nothing is colliding with it, it is not powered.
"""
class Butten(Block):
    radius = 15
    def __init__(self, x, y, colors=("#FFFFFF", "#FF0000", "#770000")):
        super().__init__((x - Butten.radius, y - Butten.radius),
                         (x + Butten.radius, y + Butten.radius),
                         color=colors[0])
        self.colors = colors
        self.pressed = False
        self.circleID = None
        
    def type_id(self):
        return 3

    def params(self):
        return (self._x1 + Butten.radius, self._y1 + Butten.radius)

    def is_interactive(self):
        return True
        
    def is_source(self):
        return True
        
    def is_powerable(self):
        return False

    def init_draw(self, canvas):
        super().init_draw(canvas)
        self.circleID = canvas.create_oval(self._x1, self._y1,
                                           self._x2, self._y2,
                                           fill=self.colors[1])

        for obj in objs:
            if obj.type_id() == 2 and self.collide(obj):
                obj._power_sources.append(self)

    def draw(self, canvas):
        super().draw(canvas)
        canvas.coords(self.circleID, self._x1, self._y1, self._x2, self._y2)
        if not self.pressed:
            canvas.itemconfig(self.circleID, fill=self.colors[1])
        else:
            canvas.itemconfig(self.circleID, fill=self.colors[2])

    def erase(self, canvas):
        super().erase(canvas)
        canvas.delete(self.circleID)

    def update(self):
        self.pressed = False

    def onCollide(self, obj):
        self.pressed = True
        return (0,0)
        
    def is_powered(self):
        return self.pressed

"""
Goal
 - Grey Square with a purple circle in the middle
 - When all goals have been collided with, you win the game
"""
class Goal(Butten):
    radius = 15
    total = 0
    progress = 0
    def __init__(self, x, y, colors=("gray", "#F0F", "#707")):
        Goal.total += 1
        super().__init__(x, y,
                         colors=colors)

    def type_id(self):
        return 6

    def is_source(self):
        return False

    def update(self):
        pass

    """
        If the goal is touched, increment the players' progress
        towards winning. If they have all goals pressed, send
        a game-win message to the other player
    """
    def onCollide(self, obj):
        if self.pressed == False:
            Goal.progress += 1
        if Goal.total == Goal.progress:
            Game.me.sock.sendto("win:now".encode(),
                          Game.me.session.session_ip)
            Game.me.gameOver = True
        self.pressed = True
        return (0,0)
"""
Player
 - Black Square with a triangle pointing in the direction it moves
 - Also displays the name entered into the session object
 - Controlled by the user
"""
class Player(Block):
    radius = 10
    speed = 3
    def __init__(self, startx, starty, name="", host=False):
        super().__init__((startx-Player.radius,starty-Player.radius),
                         (startx+Player.radius,starty+Player.radius),
                         color="#808080")

        # Previous position
        self._old = (self._x1, self._y1,
                     self._x2, self._y2)

        # Direction facing
        self._dir = {
                        'Up' : False,
                        'Down' : False,
                        'Left' : False,
                        'Right' : False
                    }

        self._face = 'Up'
        self._arrowID = None
        self._nameID = None
        self._name = name
        self._host = host

    def type_id(self):
        return 1

    """
        Sets meta-data about the player: name and whether or not they are the host
    """
    def set_meta(self, name, host):
        self._name = name
        self._host = host

    def params(self):
        return (self._x1 + Player.radius, self._y1 + Player.radius)

    def __getitem__(self, key):
        return self._dir[key]

    def __setitem__(self, key, value):
        self._dir[key] = value

    def getOldPos(self):
        return self._old

    """
        Move the player
    """
    def update(self):
        self._old = (self._x1, self._y1,
                     self._x2, self._y2)

        if self._dir['Up']:
            self._y1 -= Player.speed
            self._y2 -= Player.speed

        if self._dir['Down']:
            self._y1 += Player.speed
            self._y2 += Player.speed

        if self._dir['Left']:
            self._x1 -= Player.speed
            self._x2 -= Player.speed

        if self._dir['Right']:
            self._x1 += Player.speed
            self._x2 += Player.speed

    def shift(self, shiftx, shifty):
        self._x1 += shiftx
        self._x2 += shiftx
        self._y1 += shifty
        self._y2 += shifty

    def face(self, direction):
        self._face = direction

    def init_draw(self, canvas):
        self._nameID = canvas.create_text(self._x2 - ((self._x2 - self._x1) / 2),
                                          self._y2 - (self._y2 - self._y1) - 12, 
                                          text=self._name, 
                                          fill=('red' if self._host else 'blue'))

        #Assuming Arrow is pointing up initially
        self._arrowID = canvas.create_polygon(self._x1 + Player.radius - 6, self._y1 - 2,
                                              self._x1 + Player.radius, self._y1 - 7,
                                              self._x1 + Player.radius + 6, self._y1 - 2)
        super().init_draw(canvas)

    def draw(self, canvas):
        canvas.coords(self._nameID, self._x2 - ((self._x2 - self._x1) / 2),
                                    self._y2 - (self._y2 - self._y1) - 12)

        rad1 = Player.radius - 6
        rad2 = Player.radius + 6

        # Draw the arrow facing the direction of the player
        if self._face == 'Up':
            canvas.coords(self._arrowID, self._x1 + rad1, self._y1 - 2,
                                         self._x1 + Player.radius, self._y1 - 7,
                                         self._x1 + rad2, self._y1 - 2)

        elif self._face == 'Left':
            canvas.coords(self._arrowID, self._x1 - 2, self._y1 + rad1,
                                         self._x1 - 7, self._y1 + Player.radius,
                                         self._x1 - 2, self._y1 + rad2)

        elif self._face == 'Right':
            canvas.coords(self._arrowID, self._x2 + 2, self._y1 + rad1,
                                         self._x2 + 7, self._y1 + Player.radius,
                                         self._x2 + 2, self._y1 + rad2)

        elif self._face == 'Down':
            canvas.coords(self._arrowID, self._x1 + rad1, self._y2 + 2,
                                         self._x1 + Player.radius, self._y2 + 7,
                                         self._x1 + rad2, self._y2 + 2)

        super().draw(canvas)

    def erase(self, canvas):
        super().erase(canvas)
        canvas.delete(self._arrowID)
        canvas.delete(self._nameID)
        
        self._blockID = None
        self._arrowID = None
        self._nameID = None
        
# List of all game object classes
# Used for loading in the level concisely
obj_set = (
              Block,
              Player,
              Wire,
              Butten,
              CosmeticWire,
              Door,
              Goal
          )

"""
    Load all the game objects from the level into
    the global list of objects
"""
def load(filename):
    global objs
    objs = []
    
    with open(filename,"rb") as f:
        data = pickle.load(f)

    for obj in data:
        objs.append(obj_set[obj[0]](*obj[1]))
