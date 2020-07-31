#!/usr/bin/env python3
import socket
import cmd
import threading
from time import sleep


to_send = {}
broken_connections = set()
active_connections = []
connection_manager = None

#TODO when we recieve nonsense bytes bad things happen and the server errors out.
class MessageManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
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
    iexist = True
    def __init__(self, clientsocket):
        threading.Thread.__init__(self)
        self.clientsocket = clientsocket
        active_connections.append(self)
        
    def run(self):
        to_send[self] = []
        while True:
            data = self.clientsocket.recv(12)
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
        self.serversocket.bind(('127.0.0.1', 12345))
        self.serversocket.listen(8)
        self.serversocket.settimeout(1)
        connection_manager = self
        
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
    def do_messagehistory(self, arg):
        pass

    def do_threadcount(self, arg):
        print(threading.active_count())


if __name__ == '__main__':
    ServerMan().cmdloop()
