#!/bin/env python

# This program is free software. It comes without any warranty, to
# the extent permitted by applicable law. You can redistribute it
# and/or modify it under the terms of the Do What The Fuck You Want
# To Public License, Version 2, as published by Sam Hocevar. See
# http://sam.zoy.org/wtfpl/COPYING for more details.

import asyncore
import asynchat
import socket
import re
from struct import pack, unpack

# Virtual host definitions
HOSTS = {
    "localhost": {"host": "localhost", "port": 25566},
    "127.0.0.1": {"port": 25567},   # host defaults to 'localhost'
    None: {"port": 25568}           # default / fallback
}

# Since the host is not sent in the server list query, this is static.
# This might (hopefully) change in the near future.
MOTD = "Minecraft VirtualHost Proxy"
MAX_PLAYERS = 10
CUR_PLAYERS = 3


def pack_string(string):
    '''
    Packs a string into UCS-2 and prefixes it with its length as a short int.

    This function can't actually handle UCS-2, therefore kick messages and
    the MOTD can't contain special characters.
    '''
    return (pack(">h", len(string)) +
            "".join([pack(">bc", 0, c) for c in string]))


def unpack_string(data):
    '''
    Extracts a string from a data stream.

    Like in the pack method, UCS-2 isn't handled correctly. Since usernames
    and hosts can't contain special characters this isn't an issue.
    '''
    (l,) = unpack(">h", data[:2])
    assert len(data) >= 2 + 2 * l
    return data[3:l * 2:2]


class Router:
    '''
    The router finds the target server from the string sent in the handshake.
    '''
    PATTERN = re.compile("^([^;]+);([^;]+):(\d{1,5})$")

    @staticmethod
    def route(name):
        '''
        Finds the target host and port based on the handshake string.
        '''
        host = Router.find_host(name)
        target = HOSTS.get(host)
        return (target.get("host", "localhost"), target.get("port", 25565))

    @staticmethod
    def find_host(name):
        '''
        Extracts the host from the handshake string.
        '''
        match = re.match(Router.PATTERN, name)
        if match is None:
            return
        host = match.group(2)
        if host not in HOSTS:
            return
        return host


class Listener(asyncore.dispatcher):
    '''
    Listens for connecting clients.
    '''
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        print "Listening for connections to %s:%s" % (host, port)

    def handle_accept(self):
        '''
        Accepts a new connections and assigns it to a new ClientTunnel.
        '''
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            handler = ClientTunnel(sock, addr)

    @staticmethod
    def loop():
        '''
        Starts the main I/O loop.
        '''
        asyncore.loop()


class ClientTunnel(asynchat.async_chat):
    '''
    Handles a connecting client and assigns it to a server
    '''
    DELIMITER = chr(0xa7)

    def __init__(self, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator(None)
        self.ibuffer = ""
        self.bound = False
        self.addr = "%s:%s" % addr
        self.log("Incomming connection")

    def log(self, message):
        '''
        Feedback to user
        '''
        print "%s - %s" % (self.addr, message)

    def collect_incoming_data(self, data):
        '''
        Listens for data and forwards it to the server.

        If the client is not yet connected to a server this method waits
        for a handshake packet to read the host from. If the client sends
        a server list query (0xfe) the connection is closed after sending
        the static server list data to the client.
        '''
        if self.bound:
            self.server.push(data)
        else:
            self.ibuffer += data
            if len(self.ibuffer) >= 1:
                (packetId,) = unpack(">B", self.ibuffer[0])
                if packetId == 0xfe:        # Handle server list query
                    self.log("Received server list query")
                    self.kick(("%s" * 5) % (MOTD, self.DELIMITER,
                                          CUR_PLAYERS, self.DELIMITER,
                                          MAX_PLAYERS))
                elif packetId == 0x02:      # Handle handshake
                    if len(self.ibuffer) >= 3:
                        (l,) = unpack(">h", self.ibuffer[1:3])
                        if len(self.ibuffer) >= 3 + l * 2:
                            self.bind_server(unpack_string(self.ibuffer[1:]))
                else:
                    self.kick("Unexpected packet")

    def bind_server(self, name):
        '''
        Finds the target server and creates a ServerTunnel to it.
        '''
        (host, port) = Router.route(name)
        self.log("Forwarding to %s:%s" % (host, port))
        self.server = ServerTunnel(host, port, self, name)
        self.bound = True

    def kick(self, reason):
        '''
        Kicks the client.
        '''
        self.log("Kicking (%s)" % reason)
        self.push(pack(">B", 0xff) + pack_string(reason))
        self.close()

    def handle_close(self):
        '''
        Terminates the ServerTunnel if the client closes the connection.
        '''
        self.log("Client closed connection")
        self.server.close()
        self.close()


class ServerTunnel(asynchat.async_chat):
    '''
    Represents the server side of a connection.

    Data from the server is forwarded to the client.
    '''
    def __init__(self, host, port, client, handshake):
        asynchat.async_chat.__init__(self)
        self.set_terminator(None)
        self.client = client
        self.handshake_msg = handshake
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))

    def log(self, message):
        '''
        Feedback to user
        '''
        self.client.log(message)

    def handle_error(self):
        '''
        Handles socket errors
        '''
        err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err == 61:
            self.client.kick("Server unreachable")
        else:
            self.client.kick("Unexpected error")

    def handle_connect(self):
        '''
        Repeats the handshake packet for the actual server
        '''
        self.push(pack(">B", 0x02) + pack_string(self.handshake_msg))

    def handle_close(self):
        '''
        Terminates the ClientTunnel if the server closes the connection.
        '''
        self.log("Server closed connection")
        self.client.close()
        self.close()

    def collect_incoming_data(self, data):
        '''
        Forwards incoming data to the client
        '''
        self.client.push(data)

if __name__ == "__main__":
    server = Listener('0.0.0.0', 25565)
    Listener.loop()
