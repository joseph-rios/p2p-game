"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""

import tkinter as tk
import threading, json

"""
    The browser is the screen where the user will find available
    sessions to join and play against another player. Once a
    session has been selected and connected to, the browser should
    be destroyed and the game should be started.
"""
class Browser():
    
    def __init__(self, server_sock, client_session):
        self.WIDTH, self.HEIGHT = 300, 400
        self.root = tk.Tk()

        self.server_sock = server_sock
        self.sessions = []
        self.selected_session = None
        self.client_session = client_session
        self.ready_for_lobby = False

        self.username = tk.StringVar()
        self.username_is_valid = False
        self.username.trace("w", lambda n, i, m, v=self.username: self.on_name_change(v))
        self.password = tk.StringVar()

        self.setup_root()
        self.setup_session_info()
        self.setup_session_list()

        self.should_poll_session_list = threading.Event()
        self.poll_session_list_thread = threading.Thread(name="poll_session_list", target=self.poll_session_list)

    """
        Start the thread for polling the session list for changes
        as well as initiate the tkinter mainloop
    """
    def start(self):
        self.poll_session_list_thread.start()
        self.on_refresh_sessions_clicked()
        self.root.mainloop()

    """
        Stop the thread for polling the session list for changes
        as well as destroy the window
    """
    def destroy(self):
        self.should_poll_session_list.set()
        self.root.destroy()
        
    """
        Sets the root window's:
        title, resizability, width, height, and screen position
    """
    def setup_root(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate where to place the window such that
        # it is centered within the user's screen
        xpos = (screen_width / 2) - (self.WIDTH / 2)
        ypos = (screen_height / 2) - (self.HEIGHT / 2)
        
        self.root.title("Session Browser")
        #self.root.resizable(False, False)
        self.root.geometry("{}x{}+{}+{}".format(self.WIDTH,
                                                  self.HEIGHT,
                                                  int(xpos),
                                                  int(ypos)))

        for i in range(8):
            self.root.grid_rowconfigure(i, weight=1)

        self.root.grid_columnconfigure(1, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)

    """
        Creates the widgets for the user's name, session details box,
        session password entry, as well as the buttons for hosting a
        session or connecting to one
    """
    def setup_session_info(self):
        self.session_info_name_label = tk.Label(self.root, text="Name:")
        self.session_info_name_label.grid(row=0, column=0, sticky="sw", padx=(10, 5), pady=(5, 0))

        self.session_info_name_entry = tk.Entry(self.root, textvariable=self.username, width=15)
        self.session_info_name_entry.grid(row=1, column=0, sticky="ew", padx=(10, 5))

        self.session_info_host_button = tk.Button(self.root, text="Host Session", command=self.on_host_session_clicked)
        self.session_info_host_button.grid(row=2, column=0, sticky="new", padx=(10, 5), pady=(5, 5))
        self.session_info_host_button.config(state="disabled")

        self.session_info_details_label = tk.Label(self.root, text="Session Details:")
        self.session_info_details_label.grid(row=3, column=0, sticky="sew", padx=(10, 5), pady=(50, 0))

        self.session_info_details_text = tk.Text(self.root, width=10, height=5)
        self.session_info_details_text.tag_config('info', foreground="blue")
        self.session_info_details_text.tag_config('warning', foreground="white", background="red")
        self.session_info_details_text.tag_config('has_pass', foreground="red")
        self.session_info_details_text.tag_config('no_pass', foreground="green")
        self.session_info_details_text.grid(row=4, column=0, sticky="nsew", padx=(10, 5), pady=(5, 0))
        self.session_info_details_text.insert(tk.END, " None selected\n", "warning")
        self.session_info_details_text.config(state="disabled")

        self.session_info_password_label = tk.Label(self.root, text="Session Password:")
        self.session_info_password_label.grid(row=5, column=0, sticky="sew", padx=(10, 5), pady=(5, 0))

        self.session_info_password_entry = tk.Entry(self.root, textvariable=self.password)
        self.session_info_password_entry.grid(row=6, column=0, sticky="new", padx=(10, 5))
        self.session_info_password_entry.config(state="disabled")

        self.session_info_connect_button = tk.Button(self.root, text="Connect", command=self.on_connect_session_clicked)
        self.session_info_connect_button.grid(row=7, column=0, sticky="new", padx=(10, 5))
        self.session_info_connect_button.config(state="disabled")
    
    """
        Creates the label for the session list, as well as the session
        list itself (which will end up displaying available sessions)
    """
    def setup_session_list(self):
        self.session_list_label = tk.Label(self.root, text="Available Sessions:")
        self.session_list_label.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(5, 0))
        
        self.session_list = tk.Listbox(self.root, selectmode="single")
        self.session_list.grid(row=1, column=1, rowspan=6, sticky="nsew", padx=(5, 10), pady=(0, 5))

        self.session_list_refresh_button = tk.Button(self.root, text="Refresh", command=self.on_refresh_sessions_clicked)
        self.session_list_refresh_button.grid(row=7, column=1, sticky="new", padx=(5, 10), pady=(0, 10))

    """
        Requests the list of available sessions from the server and inserts them into the
        local list of sessions
    """
    def on_refresh_sessions_clicked(self):
        self.server_sock.send("refresh_sessions".encode())
        self.sessions = json.loads(self.server_sock.recv(4096).decode())
        self.session_list.delete(0, tk.END)
        for session in self.sessions:
            self.session_list.insert(tk.END, session["session_name"])

    """
        Creates a separate window for configuring a session to be hosted. Disable buttons
        in the main session browser window
    """
    def on_host_session_clicked(self):
        self.session_info_name_entry.config(state="disabled")
        self.session_info_host_button.config(state="disabled")
        self.session_list.config(state="disabled")
        self.session_info_password_entry.config(state="disabled")
        self.session_info_connect_button.config(state="disabled")

        self.setup_host_session_window()
        self.fill_host_session_window()
        self.setup_host_session_level_select()

    """
        Sends a request to the server for the available levels to be selected from and
        populates the level selection widgets
    """
    def setup_host_session_level_select(self):
        self.server_sock.send("get_levels".encode())
        self.host_session_level_list = json.loads(self.server_sock.recv(4096).decode())

        self.host_session_level_names = tk.StringVar(value=self.host_session_level_list)

        self.host_session_level_label = tk.Label(self.host_session_window, text="Select Level:")
        self.host_session_level_label.grid(row=4, column=0, columnspan=3)

        self.host_session_level_listbox = tk.Listbox(master=self.host_session_window, listvariable=self.host_session_level_names)
        self.host_session_level_listbox.grid(row=5, column=0, columnspan=3)

    """
        Validates the password entered by the client trying to connect to the selected session
        if the session does have a password. If the password is correct or the session has no
        password, the lobby is launched
    """
    def on_connect_session_clicked(self):
        if self.sessions[self.selected_session]["password"] is not None and self.sessions[self.selected_session]["password"] != self.password.get():
            self.session_info_password_label.config(fg="red", text="*Session Password:")

        else:
            self.session_info_password_label.config(fg="black", text="Session Password:")

            self.client_session.set_from_dict(self.sessions[self.selected_session])
            self.client_session.client_name = self.username.get()

            self.server_sock.send("connect_session".encode())
            self.server_sock.send(str(self.client_session).encode())

            self.ready_for_lobby = True
            self.destroy()

    """
        Sets up the window that pops up when the user decides to host a session
    """
    def setup_host_session_window(self):
        self.host_session_window = tk.Toplevel()

        window_width, window_height = 240, 320
        screen_width = self.host_session_window.winfo_screenwidth()
        screen_height = self.host_session_window.winfo_screenheight()
        
        # Calculate where to place the window such that
        # it is centered within the user's screen
        xpos = (screen_width / 2) - (window_width / 2)
        ypos = (screen_height / 2) - (window_height / 2)

        self.host_session_window.title("Host Session")
        #self.host_session_window.resizable(False, False)
        self.host_session_window.geometry("{}x{}+{}+{}".format(window_width,
                                                               window_height,
                                                               int(xpos),
                                                               int(ypos)))

        for row in range(7):
            self.host_session_window.grid_rowconfigure(row, weight=1)

        self.host_session_window.grid_columnconfigure(0, weight=1)
        self.host_session_window.grid_columnconfigure(1, weight=1)
        self.host_session_window.grid_columnconfigure(2, weight=1)
        self.host_session_window.protocol("WM_DELETE_WINDOW", self.on_host_session_closed)

    """
        Limits the number of characters the session's name can be to 40 characters
    """
    def on_host_session_name_changed(self, name):
        value = name.get()

        if len(value) > 40:
            name.set(value[:40])

    """
        Validates the password the user wants to assign to the session
    """
    def on_host_session_pass_changed(self, password):
        value = password.get().replace(' ', '')

        if len(value) > 15:
            password.set(value[:15])
        else:
            password.set(value)

    """
        If the host wants to require a password, the password entry box becomes
        enabled, otherwise the box is disabled
    """
    def on_host_session_pass_req_changed(self):
        enabled = self.host_session_pass_entry.cget("state")

        if enabled == "normal":
            self.host_session_pass_entry.delete(0, tk.END)
            self.host_session_pass_entry.config(state="disabled")
        else:
            self.host_session_pass_entry.config(state="normal")
            
    """
        Gets the required data to set up the session to be sent to the server
        and validates that a level to play on has been selected and readies
        itself to take the user to the lobby
    """
    def on_host_session_confirm_clicked(self, session_name, session_pass_req, session_pass):
        self.client_session.session_name = session_name.get()
        self.client_session.host_name = self.username.get()
        self.client_session.client_name = self.username.get()
        self.client_session.pass_req = session_pass_req.get()
        self.client_session.password = None if session_pass.get() == "" else session_pass.get()
        self.client_session.session_ip = ""
        self.client_session.session_id = ""

        no_level_selected = False
        try:
            self.client_session.session_level = self.host_session_level_list[self.host_session_level_listbox.curselection()[0]]
        except:
            no_level_selected = True

        if not no_level_selected:
            self.server_sock.send("host_session".encode())
            self.server_sock.send(str(self.client_session).encode())

            self.on_host_session_closed()
            self.destroy()
            
            self.client_session.is_host = True
            self.ready_for_lobby = True

        else:
            self.host_session_level_label.config(fg="red", text="*Select Level:")
            
    """
        When cancel is clicked, destroy the host-session window
    """
    def on_host_session_cancel_clicked(self):
        self.on_host_session_closed()

    """
        Add all the widgets to the host-session window and place them accordingly
    """
    def fill_host_session_window(self):
        session_name = tk.StringVar(self.host_session_window, value="{}s session".format(self.username.get()))
        session_name.trace("w", lambda n, i, m, v=session_name: self.on_host_session_name_changed(v))

        session_pass_req = tk.BooleanVar(self.host_session_window)

        session_pass = tk.StringVar(self.host_session_window)
        session_pass.trace("w", lambda n, i, m, v=session_pass: self.on_host_session_pass_changed(v))

        self.host_session_name_label = tk.Label(self.host_session_window, text="Session Name:")
        self.host_session_name_label.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        self.host_session_name_entry = tk.Entry(self.host_session_window, textvariable=session_name, width=20)
        self.host_session_name_entry.grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=5)

        self.host_session_pass_label = tk.Label(self.host_session_window, text="Password:")
        self.host_session_pass_label.grid(row=2, column=0, sticky="ew", padx=(10, 0), pady=5)

        self.host_session_pass_entry = tk.Entry(self.host_session_window, textvariable=session_pass)
        self.host_session_pass_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.host_session_pass_entry.config(state="disabled")

        self.host_session_pass_req_checkbox = tk.Checkbutton(self.host_session_window, text="require", variable=session_pass_req, command=self.on_host_session_pass_req_changed)
        self.host_session_pass_req_checkbox.grid(row=2, column=2, sticky="e", padx=(0, 10))
        
        self.host_session_confirm_button = tk.Button(self.host_session_window, text="Confirm", width=15, command=lambda x=session_name, y=session_pass_req, z=session_pass: self.on_host_session_confirm_clicked(x, y, z))
        self.host_session_confirm_button.grid(row=6, column=0, padx=10, pady=10)
        
        self.host_session_cancel_button = tk.Button(self.host_session_window, text="Cancel", width=15, command=self.on_host_session_cancel_clicked)
        self.host_session_cancel_button.grid(row=6, column=2, padx=10, pady=10)
        
    """
        Destroy the host session window and re-enable buttons
    """
    def on_host_session_closed(self):
        self.session_info_name_entry.config(state="normal")
        self.session_info_host_button.config(state="normal")
        self.session_list.config(state="normal")
        self.session_info_password_entry.config(state="normal")
        self.session_info_connect_button.config(state="normal")

        self.host_session_window.destroy()
        
    """
        Performs validation on the user entered name
    """
    def on_name_change(self, name):
        value = name.get()

        # If the name field is empty or contains a space, invalidate it and disable buttons
        if len(value) < 1 or ' ' in value:
            self.username_is_valid = False
            self.session_info_name_label.config(fg="red", text="*Name:")
            self.session_info_host_button.config(state="disabled")
            self.session_info_password_entry.config(state="disabled")
            self.session_info_connect_button.config(state="disabled")

        else:
            self.username_is_valid = True
            self.session_info_name_label.config(fg="black", text="Name:")
            self.session_info_host_button.config(state="normal")
            if self.selected_session is not None:
                self.session_info_password_entry.config(state="normal")
                self.session_info_connect_button.config(state="normal")

        # Limit the number of characters a name can be to 15
        if len(value) > 15:
            name.set(value[:15])

    """
        When a different session has been selected from the
        list, update the session details text box with the
        appropriate information
    """
    def on_session_list_change(self, selected):
        session = self.sessions[selected]
        self.session_info_details_text.config(state="normal")
        self.session_info_details_text.delete(1.0, tk.END)

        self.session_info_details_text.insert(tk.END, "Host:\n", 'info')
        self.session_info_details_text.insert(tk.END, session["host_name"], 'norm')

        self.session_info_details_text.insert(tk.END, "\nLevel:\n", 'info')
        self.session_info_details_text.insert(tk.END, session["session_level"], 'norm')

        pass_req_msg = "\nPassword set" if session["pass_req"] else "\nNo password set"
        pass_req_tag = "has_pass" if session["pass_req"] else "no_pass"
        self.session_info_details_text.insert(tk.END, pass_req_msg, pass_req_tag)
        
        self.session_info_details_text.config(state="disabled")

        if session["pass_req"] and not (len(self.username.get()) < 1 or ' ' in self.username.get()):
            self.session_info_password_entry.config(state="normal")
            self.session_info_connect_button.config(state="normal")

        else:
            self.session_info_password_entry.config(state="disable")
            self.session_info_connect_button.config(state="disable")

    """
        Every 0.1 seconds, check if a different session
        is selected from the listbox
    """
    def poll_session_list(self):
        while not self.should_poll_session_list.is_set():
            if self.selected_session is not None and self.username_is_valid:
                self.session_info_password_entry.config(state="normal")
                self.session_info_connect_button.config(state="normal")

            try:
                curr = self.session_list.curselection()[0]
                if curr != self.selected_session:
                    self.on_session_list_change(curr)
                    self.selected_session = curr

            except:
                continue
                
            finally:
                self.should_poll_session_list.wait(0.1)
