#!/usr/bin/env python3
import socket
import cmd
import threading

current_connection = None

#TODO so much left to fucking do to make this thing usable by real humans but it technically works
class ClientConnection(threading.Thread):
    def __init__(self):
        global current_connection
        threading.Thread.__init__(self)
        self.clientsocket = socket.socket()
        self.clientsocket.connect(("127.0.0.1", 12345))
        current_connection = self

    def run(self):
        while True:
            data = self.clientsocket.recv(64)
            data = data.decode("utf-8")
            print("\nRECIEVED: {}\n".format(data))

    def send(self, message):
        self.clientsocket.send(message.encode('utf-8'))

    def close_connection(self):
        global current_connection
        current_connection = None

class ClientMan(cmd.Cmd):
    intro = "Hi, I exist I guess.\n"
    prompt = "1000101: "
    
    def do_openconnection(self, arg):
        global current_connection
        if current_connection == None:
            try:
                ClientConnection().start()
            except ConnectionRefusedError:
                print("It looks like the server isn't accepting connections at this time. Take it up with the server admin")
        else:
            print("Looks like you've already got a connection bruv.")

    def do_closeconnection(self, arg):
        pass

    def do_messagehistory(self, arg):
        pass

    def do_send(self, arg):
        global current_connection
        if current_connection:
            current_connection.send("{}\n".format(arg))
        else:
            print("Try opening a connection first with openconnection")

if __name__ == '__main__':
    ClientMan().cmdloop()
