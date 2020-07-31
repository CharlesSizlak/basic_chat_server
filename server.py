#!/usr/bin/env python3
import socket
import cmd
import threading
from time import sleep

#first we need to open up a server that will accept incoming connections and bind them to a socket
#information shared in that socket needs to be turned into strings if possible and sent as outbound packets to every other existing socket
#so we somehow need to understand where messages came from and where other conversations exist

to_send = {}
broken_connections = set()
active_connections = []
connection_manager = None

#TODO check to see if the connection exists before we send anything along it.
#TODO finish up the rest of the commands and find more bugs
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
        #first we will populate to_send with a unique identifier as the key associated with this connection
        #that is just going to have an empty list
        #if we recieve information over our actual connection we'll add to everyone elses list
        #the message we got
        #then as part of the while loop we check our list for anything in the list to send, then we clear
        #out our list
        to_send[self] = []
        while True:
            data = self.clientsocket.recv(12)
            data = data.decode("utf-8")
            if not len(data):
                return
            to_send[self].append(data)
        #who is running
        #we have our class of ServerMan running
        #we have a thread of ConnectionHandler who is going to be blocked
        #we have our thread of ConnectionThread going which is blocked on recv
        #we have our client running who doesnt know what messages he is supposed to be getting
        

        # We can spin up a new thread where all he does is check to see if there are messages
        # that need to be sent to people. Then because the clientsocket is a property of self
        # in the class of ConnectionThread we could have another method exist in the class
        # to send the messages we need to send, since we can run that while the actual thread
        # himself is busy being sleepy.
    def send(self, message):
        #send the message along the clientsocket
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
        #open the server and start accepting incoming connections.
        global connection_manager
        if connection_manager == None:
            ConnectionHandler().start()
        else:
            print("You've already got a server running.")

    def do_closeserver(self, arg):
        #close the server nicely by saying goodbye, close the program
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
        #tell all the current sockets goodbye
        for connection in active_connections:
            if connection.is_alive():
                connection.say_goodbye()
        active_connections.clear()
        print("Connections closed.")
            
    def do_messagehistory(self, arg):
        #print the message history
        pass

    def do_threadcount(self, arg):
        print(threading.active_count())


if __name__ == '__main__':
    ServerMan().cmdloop()
