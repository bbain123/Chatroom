import socket
import select
import selectors
import sys
import signal

BUFFER = 1024
HEADER = 1024


def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    #let everyone know they are gonna be kicked out
    sys.exit(0)

def receiveMessage(clientSocket):
    try:
        textHeader = clientSocket.recv(HEADER) #read the message header
        if len(textHeader) == 0:     #if connection closed, no header, exit
            return False 
        
        textLength = int(textHeader.decode('utf-8').strip()) #get length of message
        return {'header': textHeader, 'data': clientSocket.recv(textLength)} #return the header and the message
        
    except:

        return False

def main():
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #allow people to reconnect to server
    serverSocket.bind(('', 0))  
    serverSocket.listen(20)
    signal.signal(signal.SIGINT, signal_handler) #set up listener to exit

    print('Will wait for client connections at port ' + str(serverSocket.getsockname()[1]))
    print('Waiting for incoming client connections ...')

    socketList = [serverSocket]
    clients = {} #dictionary of clients

#whoever connects first and closes will boot everyone after off

    while(1):   #continue to listen for messages
            #get sockets that have data in them and store in readSocket
            readSocket, writeSocket, errorSocket = select.select(socketList, [], socketList)
            
            
            #go through the sockets with data in them
            for dataSocket in readSocket:
                if dataSocket == serverSocket: #if the socket is from server, new connection
                    clientSocket, clientAddress = serverSocket.accept() #get their socket number and username
                    user = receiveMessage(clientSocket)
                    
                    if user is False: 
                        print("um what?")
                        continue
                
                    socketList.append(clientSocket) #add their socket to the list of connections
                    clients[clientSocket] = user
                    print('Accepted connection from client address: ({}, {})'.format(*clientAddress, clientSocket))
                    print(f'Connection to client established, waiting to receive messages from user \' {user["data"].decode("utf-8")} \'...')

                else: #it is a message 
                    message = receiveMessage(dataSocket)

                    if message is False: #if its empty because someone disconnected
                        
                        print()
                        
                    else:
                    
                        user = clients[dataSocket]  #print message to server
                        print(f'Received message from user {user["data"].decode("utf-8")} : {message["data"].decode("utf-8")}')
                        

                        #it doesnt care if the message came from what socket, just that the message exists
                        if message['data'].decode("utf-8").startswith("DISCONNECT"):
                            print('Disconnecting user {}'.format(clients[dataSocket]['data'].decode('utf-8')))
                            #clientSocket.send("Disconnected from server...exiting!".encode('utf-8'))
    
                            socketList.remove(dataSocket)   #remove user
                            del clients[dataSocket]
                            

                        else:
                        #send message to all clients
                            for clientSocket in clients:
                                if clientSocket != dataSocket:
                                    clientSocket.send(user['header'] + user['data'] + message['header'] + message['data'])
            

if __name__ == '__main__':
    main()