#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# mrt_client.py - defining client APIs of the mini reliable transport protocol
#

import math
import os
from socket import *
import threading
import time  # for UDP connection
from segment import Segment
from timer import Timer


class Client:
    def init(self, src_port, dst_addr, dst_port, segment_size):
        """
        initialize the client and create the client UDP channel

        arguments:
        src_port -- the port the client is using to send segments
        dst_addr -- the address of the server/network simulator
        dst_port -- the port of the server/network simulator
        segment_size -- the maximum size of a segment (including the header)
        """
        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        self.client_socket.bind(("127.0.0.1", src_port))
        # self.client_socket.settimeout(5)

        self.cur_server_buffer_space_lock = threading.Lock()

        self.rcv_handler_thread = threading.Thread(target=self.rcv_handler)
        self.segment_size = segment_size

        if os.path.exists("log.txt"):
            os.remove('log.txt')

        self.packets_to_be_acked = {}  # key = seq num, value = segment byte string
        self.ack_lock = threading.Lock()

        self.src_port = src_port

        self.greatest_received_ack = None
        self.greatest_ack_lock = threading.Lock()

        self.connection_closed = False

        self.dst_socket = (dst_addr, dst_port)
        self.data_acked = 0

        self.data_to_resend = b''
        self.data_to_resend_lock = threading.Lock()

        self.timer = Timer()

        self.rcv_handler_thread.start()

    def rcv_handler(self):
        """
        Receive data over client's socket and process that data, updating relevant values accordingly

        After the connection is open and before the connection is closed, loops and receives data from the server, and processes these segments to determine action to take
        """
        while not self.connection_closed:
            try:
                server_packet = Segment.process_segment(
                    self.client_socket.recv(29))
                # Case: is SYN
                if server_packet[3]:  # Case: is FIN
                    if server_packet[1]: # Case: is FIN ACK
                        self.log_rcv('FINACK', 0, server_packet[0])
                        self.connection_closed = True
                        break
                    self.log_rcv('FIN', 0, server_packet[0])
                    self.client_socket.sendto(Segment.create_segment(self.cur_seq_num, True, False, True, 0, b''), self.dst_socket)
                    self.log_send('FINACK', 0)
                    self.client_socket.settimeout(3)
                    self.connection_closed = True
                    try:
                        self.client_socket.recv(29) # Resend if still receiving from server
                        self.client_socket.sendto(Segment.create_segment(self.cur_seq_num, True, False, True, 0, b''), self.dst_socket)
                        self.log_send('FINACK', 0)
                    except timeout: # If not receiving from the server, can quit
                        continue
                elif server_packet[2]: # Case: SYNACK
                    self.log_rcv('SYNACK', 0, server_packet[0])
                    self.cur_server_buffer_space = server_packet[4]
                    self.server_buffer_space = self.cur_server_buffer_space
                    # value of last ack from server
                    self.greatest_received_ack = server_packet[0]
                    self.connection_established = True
                elif server_packet[1]:  # Case: is ACK
                    self.log_rcv('ACK', 0, server_packet[0])
                    self.cur_server_buffer_space_lock.acquire()
                    self.cur_server_buffer_space = server_packet[4]
                    self.cur_server_buffer_space_lock.release()
                    ack_update = False
                    self.greatest_ack_lock.acquire()
                    if server_packet[0] > self.greatest_received_ack:
                        self.greatest_received_ack = server_packet[0]
                        ack_update = True
                        self.ack_lock.acquire()
                        for key in self.packets_to_be_acked.copy().keys():
                            if key <= self.greatest_received_ack:
                                self.data_acked += len(self.packets_to_be_acked[key])
                                self.packets_to_be_acked.pop(key)
                        self.ack_lock.release()
                    self.greatest_ack_lock.release()
                    self.timer.reset_timer()
            except ValueError:
                self.log_rcv('COR', -1, -1)
                continue
    
    def log_send(self, type, payload_length):
        """
        helper function to write data sent to the log file

        arguments:
        type -- the type of packet being sent eg. SYN, FIN, ACK, SYN ACK, FIN ACK
        payload_length -- the length of data being appended to the packet
        """
        with open('log.txt', 'a') as f:
            f.write(f'{time.time()} {self.src_port} {self.dst_socket[1]} {self.cur_seq_num} {type} {payload_length}\n')
    
    def log_rcv(self, type, payload_length, seq_num):
        """
        helper function to write data sent to the log file

        arguments:
        type -- the type of packet being sent eg. SYN, FIN, ACK, SYN ACK, FIN ACK, COR, DAT
        payload_length -- the length of data being appended to the packet
        seq_num -- The sequence number of the packet
        """
        with open('log.txt', 'a') as f:
            f.write(f'{time.time()} {self.dst_socket[1]} {self.src_port} {seq_num} {type} {payload_length}\n')

    def connect(self):
        """
        connect to the server
        blocking until the connection is established

        it should support protection against segment loss/corruption/reordering 
        """
        self.connection_established = False
        while not self.connection_established:
            try:
                handshake_segment = Segment.create_segment(
                    0, False, True, False, 0, b'')
                self.cur_seq_num = 0
                self.client_socket.sendto(handshake_segment, self.dst_socket)
                self.log_send('SYN', 0)
                self.max_seq_num = 1
                time.sleep(1)  # Wait so as to not flood server
            except ValueError:
                continue

        # Send SYN ACK
        syn_ack = Segment.create_segment(
            0, True, True, False, 0, b'')
        self.client_socket.sendto(syn_ack, self.dst_socket)
        self.log_send('SYNACK', 0)
        time.sleep(1) # allow server to flush buffer if necessary
        self.cur_seq_num += 1

    def send(self, data):
        """
        send a chunk of data of arbitrary size to the server
        blocking until all data is sent

        it should support protection against segment loss/corruption/reordering and flow control

        arguments:
        data -- the bytes to be sent to the server
        """
        total_data_to_send = len(data)
        max_seq_num = math.ceil(len(data) / self.segment_size)
        while True:
            self.greatest_ack_lock.acquire()
            if (self.greatest_received_ack >= max_seq_num and len(data) <= 0) or self.connection_closed:
                self.greatest_ack_lock.release()
                break
            if self.timer.should_resend():
                self.cur_seq_num = self.greatest_received_ack + 1
                self.ack_lock.acquire()
                for key in sorted(self.packets_to_be_acked.copy().keys(), reverse=True):
                    data = self.packets_to_be_acked[key] + data
                self.ack_lock.release()
                self.cur_server_buffer_space_lock.acquire()
                self.cur_server_buffer_space = self.server_buffer_space
                self.cur_server_buffer_space_lock.release()
                self.timer.reset_timer()
            self.greatest_ack_lock.release()

            self.cur_server_buffer_space_lock.acquire()
            if len(data) > 0 and self.cur_server_buffer_space >= self.segment_size + 29:  # Segment + header size
                #self.max_seq_num = max(self.max_seq_num, self.cur_seq_num +
                 #                      (min(len(data), self.cur_server_buffer_space) // (self.segment_size + 29)))
                data_to_package = data[0:self.segment_size - 29]
                data = data[self.segment_size - 29:]
                # Making recv window 0 because this information is not applicable
                cur_segment = Segment.create_segment(
                    self.cur_seq_num, False, False, False, 0, data_to_package)
                self.ack_lock.acquire()
                self.packets_to_be_acked[self.cur_seq_num] = data_to_package
                # Now send data over socket, set timer
                self.packets_to_be_acked[self.cur_seq_num] = data_to_package # TODO: am i adding the right thing?
                self.ack_lock.release()
                self.client_socket.sendto(cur_segment, self.dst_socket)
                self.log_send('DAT', len(data_to_package))
                self.cur_seq_num = min(self.cur_seq_num + 1, max_seq_num)
                self.timer.reset_timer()
                self.cur_server_buffer_space -= len(data_to_package) + 29
            self.cur_server_buffer_space_lock.release()
        return total_data_to_send

    def close(self):
        """
        request to close the connection with the server
        blocking until the connection is closed
        """
        self.client_socket.sendto(Segment.create_segment(self.cur_seq_num, False, False, True, 0, b''), self.dst_socket)
        self.log_send('FIN', 0)
        time.sleep(3)
        if not self.connection_closed:
            self.client_socket.sendto(Segment.create_segment(self.cur_seq_num, False, False, True, 0, b''), self.dst_socket)
            self.log_send('FIN', 0)
        self.connection_closed = True
