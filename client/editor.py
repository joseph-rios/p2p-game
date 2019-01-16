"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""

from tkinter import *
import tkinter.filedialog as filedialog
from functools import partial
import client, game, pickle, socket

modes = [ "Select", "Erase", "Block",
          "Player", "Wire", "Button", 
          "CWire", "Door", "Goal" ]

"""
Editor
 - Window for the level editor
 - Based on the current selected mode, you can place objects
     Select: Click and Drag to move an existing object
     Erase: Click an object to delete it. For CWires, delete an object attached to it
     Block: Click and Drag to determine the size of the block
     Player: Click to place and optionally drag to a more precise location
     Wire: (Same as block)
     Button: (Same as player)
     CWire: First click a source object. Then, place 0 or more intermediate points
            Lastly, click the destination object.
     Door: (Same as block)
     Goal: (Same as player/button)
"""
class Editor(Frame):
    WIDTH = 600
    HEIGHT = 600
    def __init__(self):
        Frame.__init__(self)
        self.master.title("Level Editor")
        self.grid()
        self.file = None
        self.objects = []
        self.clickInfo = None # Temp Value for persisting click info between events
        self.placingWire = False

        # Menu Bar Creation
        self.menubar = Menu(self)
        menu = Menu(self.menubar, tearoff=0)
        menu.add_command(label="Open", command=self.open_file)
        menu.add_command(label="Save", command=self.save_file)
        menu.add_command(label="Save As", command=self.saveas_file)
        menu.add_command(label="Upload", command=self.upload_file)
        menu.add_command(label="Exit", command=self.exit_editor)
        self.menubar.add_cascade(label="File", menu=menu)

        self.master.config(menu=self.menubar)

        # Control Buttons
        self.curr = 0 # Default Selection
        self.buttons = []
        for n,obj in enumerate(modes):
            callback = partial(self.select, n)
            self.buttons.append(Button(text=obj, command=callback))
            self.buttons[-1].grid(row=0, column=n)

        self.buttons[self.curr].config(state=DISABLED)

        # Canvas Creation
        self.canvas = Canvas(width=Editor.WIDTH, height=Editor.HEIGHT, background='white')
        self.canvas.bind("<Button-1>", self.mousePress)
        self.canvas.bind("<B1-Motion>", self.mouseMove)
        self.canvas.bind("<ButtonRelease-1>", self.mouseRelease)
        self.canvas.grid(row=1, column=0, columnspan=len(self.buttons))

    def select(self, selection):
        self.buttons[self.curr].config(state=NORMAL)
        self.curr = selection
        self.clickInfo = None
        if self.placingWire:
            self.objects.pop(len(self.objects) - 1)
            self.placingWire = False

        self.buttons[self.curr].config(state=DISABLED)

    def open_file(self):
        dialog =  filedialog.askopenfilename(initialdir="./levels/",
                                             title="Select file",
                                             filetypes=(("Level files","*.lvl"),
                                                        ("all files","*.*")))
        if dialog != None:
            self.file = dialog
            self.load()

    def save_file(self):
        if self.file == None:
            self.saveas_file()
        else:
            self.store()

    def saveas_file(self):
        dialog = filedialog.asksaveasfile(initialdir="./levels/",
                                          title="Save As",
                                          filetypes=(("Level Files","*.lvl"),
                                                     ("All Files","*.*")))
        if dialog != '':
            self.file = dialog.name
            self.store()

    def store(self):
        store_list = []
        for obj in self.objects:
            store_list.append(( obj.type_id(), obj.params() ))

        with open(self.file, "wb") as f:
            pickle.dump(store_list, f)

    def load(self):
        with open(self.file, "rb") as f:
            data = pickle.load(f)

        for obj in data:
            self.objects.append(game.obj_set[obj[0]](*obj[1]))

        for obj in self.objects:
            obj.init_draw(self.canvas)

    def upload_file(self):
        if self.file != None:
            with open(self.file, "rb") as f:
                data = f.read()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((client.SERVER_HOST, client.SERVER_PORT))

            # Gets just the name of the file out of the full directory name
            name = self.file[self.file.rfind('/') + 1:]            
            sock.send(("upload" + name).encode())

            msg = sock.recv(10).decode()
            if msg != "OK":
                print("An error occured in uploading")
                return

            sock.send(str(len(data)).encode())
            msg = sock.recv(10).decode()
            if msg != "OK":
                print("An error occured in uploading")
                return

            sock.send(data)
            msg = sock.recv(10).decode()
            if msg != "OK":
                print("An error occured in uploading")
                return

            sock.send("bye".encode())
            sock.close()

    def exit_editor(self):
        self.master.destroy()
        exit()

    def get_object(self, x, y):
        for n, obj in enumerate(self.objects):
            if obj.inX(x) and obj.inY(y):
                return n

    def mousePress(self, event):
        x = event.x
        y = event.y
        mode = modes[self.curr]

        if mode == "Select":
            i = self.get_object(x,y)
            if i != None:
                x1, y1, x2, y2 = self.objects[i].get_pos()
                self.clickInfo = (i, x - x1, y - y1,
                                     x2 - x, y2 - y)

        elif mode == "Erase":
            i = self.get_object(x, y)
            if i != None:
                toDelete = [i]
                for n,obj in enumerate(self.objects):
                    if(str(type(obj))=="<class 'game.CosmeticWire'>"):
                        src = obj.get_src()
                        dst = obj.get_dst()
                        if(src == i):
                            toDelete.append(n)
                        if(dst == i):
                            toDelete.append(n)
                for j in sorted(toDelete):
                    self.objects[j].erase(self.canvas)
                    for obj in self.objects:
                        if(str(type(obj))=="<class 'game.CosmeticWire'>"):
                            src = obj.get_src()
                            dst = obj.get_dst()
                            if(src > j):
                                obj.set_src(src-1)
                            if(dst > j):
                                obj.set_dst(dst-1)
                for j in sorted(toDelete,reverse=True):
                    self.objects.pop(j)
                    
                

        elif mode == "Block":
            self.clickInfo = (x, y)
            self.objects.append(game.Block((x, y), (x, y)))
            self.objects[-1].init_draw(self.canvas)

        elif mode == "Player":
            self.objects.append(game.Player(x, y))
            self.objects[-1].init_draw(self.canvas)

        elif mode == "Wire":
            self.clickInfo = (x, y)
            self.objects.append(game.Wire((x, y), (x, y)))
            self.objects[-1].init_draw(self.canvas)

        elif mode == "Button":
            self.objects.append(game.Butten(x, y))
            self.objects[-1].init_draw(self.canvas)

        elif mode == "Goal":
            self.objects.append(game.Goal(x, y))
            self.objects[-1].init_draw(self.canvas)

        elif mode == "Door":
            self.clickInfo = (x, y)
            self.objects.append(game.Door((x, y), (x, y)))
            self.objects[-1].init_draw(self.canvas)

        elif mode == "CWire":
            i = self.get_object(x, y)

            if i is not None: # Object was clicked
                if not self.placingWire and self.objects[i].is_source():
                    # Checking if first click & if is a source
                    self.objects.append(game.CosmeticWire(i, points=[]))
                    self.objects[-1].add_point(self.objects[i].get_pos()[:2])
                    self.objects[-1].init_draw(self.canvas)
                    self.placingWire = True
                    
                elif self.placingWire and self.objects[i].is_powerable():
                    # Check if currently placing wire & if is powerable
                    self.objects[-1].set_dst(i)
                    self.objects[-1].add_point(self.objects[i].get_pos()[:2])
                    self.objects[-1].erase(self.canvas)
                    self.objects[-1].init_draw(self.canvas)
                    self.placingWire = False

            else: # No object was clicked
                if self.placingWire: #Already selected a source
                    self.objects[-1].add_point((x, y))
                    self.objects[-1].erase(self.canvas)
                    self.objects[-1].init_draw(self.canvas)
        
    def mouseMove(self,event):
        x = event.x
        y = event.y
        mode = modes[self.curr]

        if mode == "Select":
            if self.clickInfo != None:
                i, x1, y1, x2, y2 = self.clickInfo
                self.objects[i].set_pos((x - x1, y - y1),
                                        (x + x2, y + y2))
                self.objects[i].draw(self.canvas)

        elif mode == "Erase":
            pass

        elif mode == "Block":
            self.objects[-1].set_pos((x, y), self.clickInfo)
            self.objects[-1].draw(self.canvas)

        elif mode == "Player":
            self.objects[-1].set_pos((x - game.Player.radius, y - game.Player.radius),
                                     (x + game.Player.radius, y + game.Player.radius))
            self.objects[-1].draw(self.canvas)

        elif mode == "Wire":
            self.objects[-1].set_pos((x, y), self.clickInfo)
            self.objects[-1].draw(self.canvas)

        elif mode == "Button":
            self.objects[-1].set_pos((x - game.Butten.radius,y - game.Butten.radius),
                                     (x + game.Butten.radius,y + game.Butten.radius))
            self.objects[-1].draw(self.canvas)

        elif mode == "Goal":
            self.objects[-1].set_pos((x - game.Goal.radius,y - game.Goal.radius),
                                     (x + game.Goal.radius,y + game.Goal.radius))
            self.objects[-1].draw(self.canvas)

        elif mode == "Door":
            self.objects[-1].set_pos((x, y), self.clickInfo)
            self.objects[-1].draw(self.canvas)

    def mouseRelease(self,event):
        self.clickInfo = None

if __name__=='__main__':
    Editor().mainloop()
