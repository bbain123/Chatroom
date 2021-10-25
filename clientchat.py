import socket
import selectors
import sys
import argparse
import errno
import signal
import fcntl
import os
from urllib.parse import urlparse

HEADER = 1024

def signal_handler(sig, frame):

    print('Interrupt received, shutting down ...')
    disconnect = ("DISCONNECT " + username.decode("utf-8") + " CHAT/1.0").encode("utf-8") #send server a disconnect message and exit
    disconnectHeader = f'{len(disconnect):<{HEADER}}'.encode('utf-8')
    clientSocket.send(disconnectHeader + disconnect)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) #set up listener to exit
mySelector = selectors.DefaultSelector() #create a selector
#make sys.stdin non-blocking 
file = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, file | os.O_NONBLOCK)

try:
    # Check command line arguments to retrieve a URL.
    parsedArgs = urlparse(sys.argv[2])
    host = parsedArgs.hostname
    port = parsedArgs.port

    username = sys.argv[1].encode('utf-8')

    print('Connecting to server ...')

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((host, port)) #connect to the server
    clientSocket.setblocking(False)
    
    print('Connection to server established. Sending intro message...')
    print('Registration successful. Ready for messaging!')

except argparse.ArgumentError:
    if len(sys.argv) < 2:
        print("Fill in ALL command lines: <username> chat://<IP>:<port>")

    elif len(sys.argv) > 2:
        print("Too many arguments: <username> chat://<IP>:<port>")
    
    else:
        print("Invalid command line arguments")

except Exception as e:
    print('AN ERROR HAS BEEN FOUND!: \n' .format(str(e))) 


usrnameHeader = f'{len(username):<{HEADER}}'.encode('utf-8')
clientSocket.send(usrnameHeader + username) #send the server the username header and username


def sendMessage(arg1, arg2): #called when we receive input from stdin
        message = arg1.read()
        if message:
            message = "@" + username.decode('utf-8') + ": " + message
            message = message.strip('\n').encode('utf-8') #make sure its formatted correctly
            messageHeader = f"{len(message):<{HEADER}}".encode('utf-8') #make message header
            clientSocket.send((messageHeader + message)) #send the server the message header and message


def readMessage(conn, mask): #called when we receive input from server
    try:
        usrnameHeader = clientSocket.recv(HEADER) #get username header

        if not len(usrnameHeader): #if receive no data, server closed
            print("Disconnected from server...exiting!") 
            sys.exit()

        usrnameLength = int(usrnameHeader.decode('utf-8').strip())
        username = clientSocket.recv(usrnameLength).decode('utf-8')

        messageHeader = clientSocket.recv(HEADER)
        messageLength = int(messageHeader.decode('utf-8').strip())
        message = clientSocket.recv(messageLength).decode('utf-8')

        print(f'{message}')

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('Reading error: {}'.format(str(e)))
            sys.exit()

    except Exception as e:
        print('Disconnecting from server ... exiting!'.format(str(e)))
        sys.exit()

mySelector.register(clientSocket, selectors.EVENT_READ, readMessage) #when we receive messages, handle at readMessage
mySelector.register(sys.stdin, selectors.EVENT_READ, sendMessage) #when we get input from stdin, send message through sendMessage


def main():
    while(1):
        sys.stdout.write('> ')
        sys.stdout.flush()
        for k, mask in mySelector.select():
            callback = k.data
            callback(k.fileobj, mask)


if __name__ == '__main__':
    main()

