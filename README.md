# Transmission Control Protocol Using Go-Back-N
## Paul Kearns

This is an implementation of a protocol for reliable transfer, similar to TCP but using go-back-n instead of selective repeat. A client and server communicate over a simulated lossy network, with both potential bit corruption and dropped packets, to transmit a file from the client to the server.

Run the network, client, and server, respectively, using the following commands in terminal. The network must be launched first.\
python3 network.py 51000 '127.0.0.1' 50000 '127.0.0.1' 60000 Loss.txt\
python3 app_client.py 50000 127.0.0.1 51000 1460\
python3 app_server.py 60000 4096

The packet loss rate and bit error rate on the simulated network can be adjusted using the Loss.txt file. Specifically, each line in Loss.txt follows the form \<time\> \<segment loss rate\> \<bit error rate\>. For example, the line "5 .1 0.000005" indicates that at 5 seconds, the packet loss rate changes to 10% and the bit error rate changes to .0005%.

The server is launched using init(), which initializes necessary variables as well as two threads: one for receiving data over the server socket and writing it to a receive buffer, and another responsible for processing this data and writing data that is in order to the data buffer. The functions run on these threads are rcv_handler() and segment_handler() respectively. Using a state variable for whether the connection is closed, these threads do not take actions until the connection is established by the accept() function.

When accept() is called, the server begins waiting for a SYN for the handshake, as described in DESIGN.MD. Upon receiving one, it then sends a SYN ACK, and waits for a SYN ACK from the client to confirm the connection. If it receives this SYN ACK or that packet is dropped but the client begins sending data, the server sets connection_established = True and returns that connection.

The receive() function will return length bytes only once length bytes are received and placed in the data buffer. 

The client is also launched using init, which instantializes necessary variables and a thread for receiving data, made on a function called rcv handler which loops as long as the connection is not closed. This function processes and incoming segments and takes action accordingly, resetting the greatest received ack from the server, the current server buffer space, and more.

The client's connect() function will send SYNs until it receives a SYN ACK, in which case it sets the connection as established and then sends another SYN ACK. The send() function, if called, will begin sending data.

The send() function uses an instance of the timer from the Timer class to track if no ACK has been received for 5 seconds, and then the client will assume any sent packets were dropped and resend them.

If the server encounters a checksum that was incorrect, it flushes the current buffer, because it is possible that the bit indicating length was incorrect, which would lead to the buffer being offset. If this occurs, I will log the type as 'COR' and length and sequence number as -1.