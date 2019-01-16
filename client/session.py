"""
    Authors: Slate Hayes, Joseph Rios, David Williams
    Course: CSC 565
    Instructor: Dr. Katangur
    Date: 12/6/18
"""

import json

class Session:
    def __init__(self, session_name="", host_name="", client_name="",
                 pass_req=False, password=None, session_ip="",
                 session_id="", session_level="", my_port="", is_host=False):

        self.session_name = session_name
        self.host_name = host_name
        self.client_name = client_name
        self.pass_req = pass_req
        self.password = password
        self.session_ip = session_ip
        self.session_id = session_id
        self.session_level = session_level
        self.my_port = my_port
        self.is_host = is_host

    """
        Set all the session attributes from the provided dictionary
    """
    def set_from_dict(self, d):
        self.session_name = d["session_name"]
        self.host_name = d["host_name"]
        self.client_name = d["client_name"]
        self.pass_req = d["pass_req"]
        self.password = d["password"]
        self.session_ip = d["session_ip"]
        self.session_id = d["session_id"]
        self.is_host = d["is_host"]
        self.session_level = d["session_level"]
        self.my_port = d["my_port"]
        
    """
        Return the session object in a JSON format
    """
    def __str__(self):
        return json.dumps({ "session_name": self.session_name,
                            "host_name": self.host_name,
                            "client_name": self.client_name,
                            "pass_req": self.pass_req,
                            "password": self.password,
                            "session_ip": self.session_ip,
                            "session_id": self.session_id,
                            "session_level": self.session_level,
                            "my_port": self.my_port,
                            "is_host": self.is_host })
