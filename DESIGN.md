# CSEE 4119 Spring 2024, Assignment 2 Design File
## Paul Kearns
## GitHub username: PaulKearns

*Please replace this text with your protocol design, which includes the types of messages, message type, and protocol elements to achieve reliable data transfer.*

I implemented a client/server application to transfer data from the client to the server using Go-Back-N.

Messages carry the following data in a header: sequence number, whether the packet is an ACK, whether the packet is a SYN, whether the packet is a FIN, the receive window size, the size in bytes of any data attached after the header, and checksum value. I am defining messages carrying data from the client as DATs. If data size is nonzero, the data comes directly after the header and the packet is a DAT. All messages without matching checksums (calculated using both data and header excluding checksum) compared to what is calculated are discarded. Messages can be DATs, ACKs, SYNs, FINs, and if 2 of these bits are true, they are SYN ACKs or FIN ACKs.

First, the client and server communicate using a 3-way handshake. The client sends a SYN to the server, which responds with a SYN ACK, and the client finally responds with a SYN ACK as well. If the first SYN is dropped (determined by no response after a certain amount of time), the client resends. If the server's SYN ACK is dropped, then the client won't respond with an ACK and the server will time out, waiting for a new ACK. If the client's SYN ACK is dropped, the client will start sending data anyway and the server will infer that the client sent a SYN ACK.

Sequence numbers count up from 0. If the server receives a packet other than its current sequence number + 1, it will discard it. We assume sequence numbers cannot go high enough to require more than 4 bytes. If the client receives an ACK for a sequence number greater than its last recorded ACK from the server, it will update this last recorded ACK to the current value.

The window size is maintained by the client using the free space advertised from the server in the latest ACK, and the client sends as many packets as it can without overwhelming this server size.

The client will resend packets that have not been ACKed after 5 seconds.

Once the client sends all of its data or the server receives all that is requested by the receive function, the program calling the API is expected to call the close function if desired. This will initiate a close handshake.

In this handshake, it doesn't matter whether client or server initiate. The closing party will send a FIN, resending if it hears no response. The other party will send a FIN ACK, and if it receives another FIN, it will resend this FIN ACK. It is assumed that after these 2 packets are sent with no response (in either direction), the network is stable enough that one of the packets made it successfully, as was suggested on Ed Discussion.

Multiple SYNS, SYNACKs, or FINACKs may be sent for redundancy, and this is acceptable. For the SYN handshake, I make sequence number 0 for all parts.