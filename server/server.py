"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""

import json, os, signal, socket, threading

# The host address and port number should be constant
# and determined by the machine running the server.
server_levels_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "levels")
HOST, PORT = "127.0.0.1", 56569

"""
    This function waits for a CTRL+C signal and attempts
    to stop all the client threads being run
"""
def sigint_callback(sig, frame, sock, accept_event, threads):
    # Stop accepting new connections
    accept_event.set()

    # Break out of all client threads
    for t in threads:
        t[1].set()

    # Close the socket and exit
    sock.close()
    exit(0)

"""
    This function listens for messages from the client
    and performs certain actions based on what those
    messages are
"""
def handle_client(conn, addr, sessions, event, lock):
    global server_levels_path

    while not event.is_set():
        try:
            # Get the message from the client
            msg = conn.recv(1024).decode()

            # The client sends 'bye' when they want to disconnect
            if msg == "bye":
                with lock:
                    session_index = None
                    # Find the client's session and remove it
                    for s in range(len(sessions)):
                        if sessions[s]["session_id"] == addr[1]:
                            session_index = s

                    if session_index is not None:
                        del sessions[session_index]

                # Stop handling this client
                event.set()

            elif msg == "refresh_sessions":
                # Send the list of all the sessions to the client
                conn.send(json.dumps(sessions).encode())

            elif msg == "get_levels":
                # Find all the levels in the correct directory
                levels = [
                            os.path.splitext(l)[0] for l in \
                            os.listdir(server_levels_path) \
                            if os.path.isfile(os.path.join(server_levels_path, l)) \
                            and l[-4:] == ".lvl"
                        ]

                # Send a list of the levels to the client
                conn.send(json.dumps(levels).encode())

            elif msg == "host_session":
                with lock:
                    # Add the session to the list of sessions
                    sessions.append(json.loads(conn.recv(4096).decode()))
                    sessions[-1]["session_ip"] = addr[0]
                    sessions[-1]["session_id"] = addr[1]

            elif msg == "connect_session":
                # Get the session details
                a = conn.recv(4096).decode().replace("\'", "\"").replace("True", "true").replace("False", "false").replace("None", "null")
                obj = json.loads(a)
                session_id = obj["session_id"]
                with lock:
                    session_index = None
                    # Find the session that the client wants to connect to
                    for s in range(len(sessions)):
                        if sessions[s]["session_id"] == session_id:
                            session_index = s

                    # Delete the session that the client connects to
                    if session_index is not None:
                        del sessions[session_index]

            elif msg[:8] == "download":
                filename = msg[8:]
                with lock:
                    # Read the level contents
                    with open(os.path.join(server_levels_path, filename + ".lvl"), "rb") as f:
                        data = f.read()

                    # Send the level to the client to save a local copy
                    conn.send(str(len(data)).encode())
                    res = conn.recv(len("OK".encode())).decode()
                    if res == "OK":
                        conn.send(data)

            elif msg[:6] == "upload":
                filename = msg[6:]
                conn.send("OK".encode())

                # Get the level contents
                filesize = int(conn.recv(1024).decode())
                conn.send("OK".encode())

                # Save the received level locally on the server
                with open(os.path.join('levels', filename),'wb') as f:
                    while filesize > 0:
                        chunk = conn.recv(1024)
                        f.write(chunk)
                        filesize -= 1024

                conn.send("OK".encode())

        except:
            # If we get an error, ignore it (it probably wasn't important anyway)
            pass

    # Close the connection to the client once we're done handling it
    conn.close()

"""
    This function listens for incoming connection requests
"""
def accept_conns(server, sessions, client_threads, event, lock):
    while not event.is_set():
        try:
            conn, addr = server.accept()
        except:
            break
            
        # Start up a thread to handle interaction with the client
        client_thread_event = threading.Event()
        client_thread = threading.Thread(name="client_{}".format(addr[0]), target=handle_client, args=(conn, addr, sessions, client_thread_event, lock,))
        client_threads.append((client_thread, client_thread_event,))
        client_thread.start()

if __name__ == "__main__":
    lock = threading.Lock()

    sessions = []
    client_threads = []

    # Start the server socket, bind it and listen on it
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))
    server.listen()
    
    # Start a thread to handle accepting incoming connection requests
    accept_conns_event = threading.Event()
    accept_conns_thread = threading.Thread(name="accept_conns", target=accept_conns, args=(server, sessions, client_threads, accept_conns_event, lock,))
    
    # Start listening for CTRL+C signal
    signal.signal(signal.SIGINT, lambda s, f: sigint_callback(s, f, server, accept_conns_event, client_threads))

    accept_conns_thread.start()

    signal.pause()
