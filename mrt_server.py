#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# mrt_server.py - defining server APIs of the mini reliable transport protocol
#

from socket import *
import threading
import time  # for UDP connection
from segment import Segment

#
# Server
#


class Server:

    def init(self, src_port, receive_buffer_size):
        """
        initialize the server, create the UDP connection, and configure the receive buffer

        arguments:
        src_port -- the port the server is using to receive segments
        receive_buffer_size -- the maximum size of the receive buffer
        """
        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_socket.bind(("127.0.0.1", src_port))
        self.server_socket.settimeout(5)

        self.rcv_buffer = b''
        self.rcv_buffer_lock = threading.Lock()

        self.data_buffer = b''
        self.data_buffer_lock = threading.Lock()

        self.rcv_buffer_size = receive_buffer_size
        self.connection_established = False
        self.connection_closed = False
        self.src_port = src_port
        self.cur_seq_num = 0

        self.rcv_handler_thread = threading.Thread(target=self.rcv_handler)
        self.segment_handler_thread = threading.Thread(
            target=self.segment_handler)
        

        self.rcv_handler_thread.start()
        self.segment_handler_thread.start()

    def log_send(self, type, payload_length):
        """
        helper function to write data sent to the log file

        arguments:
        type -- the type of packet being sent eg. SYN, FIN, ACK, SYN ACK, FIN ACK, DAT
        payload_length -- the length of data being appended to the packet
        """
        with open('log.txt', 'a') as f:
            f.write(f'{time.time()} {self.src_port} {self.cur_connection[1]} {self.cur_seq_num} {type} {payload_length}\n')

    def log_rcv(self, type, payload_length, seq_num):
        """
        helper function to write data sent to the log file

        arguments:
        type -- the type of packet being sent eg. SYN, FIN, ACK, SYN ACK, FIN ACK, COR, DAT
        payload_length -- the length of data being appended to the packet
        seq_num -- The sequence number of the packet
        """
        with open('log.txt', 'a') as f:
            f.write(f'{time.time()} {self.cur_connection[1]} {self.src_port} {seq_num} {type} {payload_length}\n')

    def rcv_handler(self):
        """
        Receive data over server's socket and add it to the receive buffer for processing

        function run by a thread separate from segment handler to recv data and buffer it quickly so that data is not ignored or lost during processing
        """
        while not self.connection_closed:
            if self.connection_established:
                try:
                    data = self.server_socket.recv(self.rcv_buffer_size)
                    self.rcv_buffer_lock.acquire()
                    # rcv buffer can only read in defined number of bytes; beyond that, drop data
                    self.rcv_buffer += data[:self.rcv_buffer_size -
                                            len(self.rcv_buffer)]
                    self.rcv_buffer_lock.release()
                except timeout: # If we close the server, this will let us exit
                    continue

    def segment_handler(self):
        """
        Read data from receive buffer and respond appropriately

        Function to read from receive buffer and process packets. If a packet is in the expected order, add data to data buffer. Handle FINs by completing handshake.
        """
        while not self.connection_closed:
            if self.connection_established:
                try:
                    rcv_buffer_empty = False
                    self.rcv_buffer_lock.acquire()
                    if len(self.rcv_buffer) <= 0:
                        rcv_buffer_empty = True
                    else:
                        cur_packet = self.rcv_buffer[:29 +
                                                     int(self.rcv_buffer[15:19])]
                    self.rcv_buffer_lock.release()
                    if rcv_buffer_empty:
                        continue
                    processed_packet = Segment.process_segment(cur_packet)
                    if processed_packet[3]:  # Case: is FIN
                        if processed_packet[1]: # Case: is FIN ACK
                            self.log_rcv('FINACK', 0, processed_packet[0])
                            self.connection_closed = True
                            break
                        self.log_rcv('FIN', 0, processed_packet[0])
                        self.server_socket.sendto(Segment.create_segment(self.cur_seq_num, True, False, True, 0, b''), self.cur_connection)
                        self.log_send('FINACK', 0)
                        time.sleep(2) # wait for fin ack
                        self.connection_closed = True
                        if len(self.rcv_buffer): # Resend if still receiving from client
                            self.server_socket.sendto(Segment.create_segment(self.cur_seq_num, True, False, True, 0, b''), self.cur_connection)
                            self.log_send('FINACK', 0)
                    elif processed_packet[2]: # Case: duplicate SYN received
                        if processed_packet[1]:
                            self.log_send('SYNACK', 0)
                        else:
                            self.log_send('SYN', 0)
                    else:  # Case: data packet
                        self.log_rcv('DAT', len(processed_packet[5]), processed_packet[0])
                        if processed_packet[0] == self.cur_seq_num + 1:
                            #self.data_buffer_lock.acquire()
                            self.data_buffer += processed_packet[5]
                            #self.data_buffer_lock.release()
                            self.cur_seq_num += 1
                        print(f'received packet {processed_packet[0]}, {len(processed_packet[5])} bytes')
                        cur_buffer_space = None
                        self.rcv_buffer_lock.acquire()
                        self.rcv_buffer = self.rcv_buffer[len(cur_packet):]
                        cur_buffer_space = self.rcv_buffer_size - \
                            len(self.rcv_buffer)
                        self.rcv_buffer_lock.release()
                        self.server_socket.sendto(Segment.create_segment(
                            self.cur_seq_num, True, False, False, cur_buffer_space, b''), self.cur_connection)
                        self.log_send('ACK', 0)
                except ValueError:
                    # Flush buffer
                    print("VALUE ERROR recv")
                    self.log_rcv('COR', -1, -1)
                    self.rcv_buffer_lock.acquire()
                    self.rcv_buffer = b''
                    self.rcv_buffer_lock.release()
                    try:
                        self.server_socket.recv(4096)
                    except timeout:
                        continue

    def accept(self):
        """
        accept a client request
        blocking until a client is accepted

        it should support protection against segment loss/corruption/reordering 

        return:
        the connection to the client 
        """
        while not self.connection_established:
            try:
                data, self.cur_connection = self.server_socket.recvfrom(29)
                processed_packet = Segment.process_segment(data)
                self.log_rcv('SYN', 0, processed_packet[0])
                handshake_segment = Segment.create_segment(
                    0, True, True, False, self.rcv_buffer_size, b'')
                self.server_socket.sendto(
                    handshake_segment, self.cur_connection)
                self.log_send('SYNACK', 0)
                while True:  # Loop until we determine if client has acked
                    data, connection = self.server_socket.recvfrom(29)
                    if int(data[15:19]) > 0:
                        data += self.server_socket.recv(29)
                    if connection != self.cur_connection:
                        continue # ignore other clients
                    try:
                        new_segment = Segment.process_segment(data)
                        # new_segment is synack from client
                        if new_segment[2] and new_segment[1]:
                            self.log_rcv('SYNACK', 0, processed_packet[0])
                            self.cur_seq_num = 0
                            self.connection_established = True
                            break
                        elif new_segment[2]: # Case: client resent syn
                            self.server_socket.sendto(handshake_segment, self.cur_connection)
                            self.log_send('SYNACK', 0)
                            continue
                        else:  # synack dropped, but data is being sent ... elif new_segment
                            self.log_rcv('DAT', len(new_segment[5]), processed_packet[0])
                            self.rcv_buffer += data
                            self.connection_established = True
                            print("THIS WAS ACUTALY REACHED")
                            break
                    except ValueError:
                        print("VALUE ERROR 1")
                        self.log_rcv('COR', -1, -1)
                        # Flush buffer
                        #try:
                        #    self.server_socket.recv(4096)
                        #except timeout:
                        #    break
            except ValueError:
                print("VALUE ERROR 0")
                self.log_rcv('COR', -1, -1)
                # Flush buffer
                try:
                    self.server_socket.recv(4096)
                except timeout:
                    continue
                continue
            except timeout:
                continue

        print("Handshake complete :)")
        return self.cur_connection

    def receive(self, conn, length):
        """
        receive data from the given client
        blocking until the requested amount of data is received

        it should support protection against segment loss/corruption/reordering 
        the client should never overwhelm the server given the receive buffer size

        arguments:
        conn -- the connection to the client
        length -- the number of bytes to receive

        return:
        data -- the bytes received from the client, guaranteed to be in its original order
        """
        # Case: given client not connected
        if conn != self.cur_connection:
            return b''

        while len(self.data_buffer) <= length:
            continue

        data = self.data_buffer[:length]
        self.data_buffer = self.data_buffer[length:]
        return data

    def close(self):
        """
        close the server and the client if it is still connected
        blocking until the connection is closed
        """
        self.server_socket.sendto(Segment.create_segment(self.cur_seq_num, False, False, True, 0, b''), self.cur_connection)
        self.log_send('FIN', 0)
        time.sleep(3)
        if not self.connection_closed:
            self.log_send('FIN', 0)
            self.server_socket.sendto(Segment.create_segment(self.cur_seq_num, False, False, True, 0, b''), self.cur_connection)
        self.connection_closed = True
