#!/usr/bin/env python3
import socket
import cmd
import threading
from time import sleep


# Ben: Globals are the devil. When you use globals, you require your classes
# to be used as a single instance - if you made two instances of ServerMan to
# try to listen on two different ports, they would be using the same global
# data structure and stealing each other's data.
# Get rid of all these globals.

# Ben: Active connections is a just a list of the keys in to_send
# any time you're duplicating data, there are opportunities for
# errors when they get out of sync. For example, if you remove a
# connection from to_send but forget to remove it from active_connections.
# Get rid of one of them.
to_send = {}
broken_connections = set()
active_connections = []
connection_manager = None

#TODO when we recieve nonsense bytes bad things happen and the server errors out.
class MessageManager(threading.Thread):
    def __init__(self):
        # Ben: A better way to call a method on your superclass is to
        # use super().__init__() because you're repeating yourself here
        # which is an opportunity for bugs. If you change the class
        # you're inheriting from, you will be calling the wrong initializer.
        # super() will look up your parent class for you, and it is even
        # more useful when you are using multiple inheritance.
        threading.Thread.__init__(self)

    def run(self):
        while True:
            # time.sleep is bad. You don't actually want the program to 'sleep until 1
            # second has passed' here, you want the program to 'sleep until a message
            # comes in' so write that code instead. What you're trying to do has nothing
            # to do with real world time
            sleep(1)
            for connection_thread, message_list in to_send.items():
                for message in message_list:
                    for target_connection_thread in to_send.keys():
                        if target_connection_thread != connection_thread:
                            try:
                                target_connection_thread.send(message)
                            except (BrokenPipeError, OSError):
                                broken_connections.add(target_connection_thread)
                to_send[connection_thread] = []
            for broken in broken_connections:
                to_send.pop(broken)
            broken_connections.clear()


class ConnectionThread(threading.Thread):
    # Ben: remove unused class variable
    iexist = True
    def __init__(self, clientsocket):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        active_connections.append(self)
        
    def run(self):
        to_send[self] = []
        while True:
            # Ben: frame your data, so that you can receive in a loop until an entire
            # message comes in. This could return anywhere from 1 to 12 bytes from one
            # or multiple messages that the client sends.
            data = self.clientsocket.recv(12)
            # Ben: This can throw an exception. Don't ever trust data that comes in from
            # a socket, assume this data is sometimes random garbage bytes and sometimes
            # carefully crafted malicious payloads.
            data = data.decode("utf-8")
            if not len(data):
                return
            to_send[self].append(data)

    def send(self, message):
        self.clientsocket.send(message.encode("utf-8"))

    def say_goodbye(self):
        to_send.pop(self)
        self.clientsocket.shutdown(socket.SHUT_RDWR)
        self.clientsocket.close()
        
class ConnectionHandler(threading.Thread):
    def __init__(self):
        global connection_manager
        threading.Thread.__init__(self)
        self.serversocket = socket.socket()
        # Don't hardcode addresses and ports. Get them from the user
        # using cmd line parameters, user input, or configuration files.
        # In this case, these parameters are begging to be passed as
        # arguments to your openserver command.
        self.serversocket.bind(('127.0.0.1', 12345))
        self.serversocket.listen(8)
        self.serversocket.settimeout(1)
        connection_manager = self # Ben: This disgusts me.
        
    def run(self):
        MessageManager().start()
        while True:
            try:
                (clientsocket, address) = self.serversocket.accept()
                ConnectionThread(clientsocket).start()
            except socket.timeout:
                pass
            except OSError:
                return

    def close_server(self):
        print("Hi I'm just here to make sure close_server ran")
        self.serversocket.close()

class ServerMan(cmd.Cmd):
    intro = "Hi, I exist I guess.\n"
    prompt = ":D : "

    def do_openserver(self, arg):
        global connection_manager
        if connection_manager == None:
            ConnectionHandler().start()
        else:
            print("You've already got a server running.")

    def do_closeserver(self, arg):
        global connection_manager
        for connection in active_connections:
            if connection.is_alive():
                connection.say_goodbye()
        active_connections.clear()
        print("Connections closed.")
        connection_manager.close_server()
        connection_manager = None
        print("Server shut down.")

    def do_clearconnections(self, arg):
        for connection in active_connections:
            if connection.is_alive():
                connection.say_goodbye()
        active_connections.clear()
        print("Connections closed.")
    
    #TODO make this work
    # Ben: make this work
    def do_messagehistory(self, arg):
        pass

    def do_threadcount(self, arg):
        print(threading.active_count())


if __name__ == '__main__':
    ServerMan().cmdloop()
