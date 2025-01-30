import struct
import zlib


class Segment:
    # Seq num is used as ack num when packets are sent from server to client
    # Assume data is already a byte string
    def create_segment(seq_num, is_ack, is_syn, is_fin, recv_window, data):
        is_ack = '1' if is_ack else '0'
        is_syn = '1' if is_syn else '0'
        is_fin = '1' if is_fin else '0'

        packet = f'{str(seq_num).zfill(4)}{is_ack}{is_syn}{is_fin}{str(recv_window).zfill(8)}{str(len(data)).zfill(4)}'.encode() + data

        checksum = zlib.crc32(packet)

        packet = packet[:19] + str(checksum).zfill(10).encode() + packet[19:]

        return packet
        

    def process_segment(segment):
        seq_num = int(segment[:4])
        is_ack = chr(segment[4]) == '1'
        is_syn = chr(segment[5]) == '1'
        is_fin = chr(segment[6]) == '1'
        recv_window = int(segment[7:15])
        data_len = int(segment[15:19])
        data = segment[29:29 + data_len]
        checksum = int(segment[19:29])

        packet_without_checksum = segment[:19] + segment[29:]
        computed_checksum = zlib.crc32(packet_without_checksum)
 
        if checksum != computed_checksum:
            raise ValueError("Checksum mismatch")

        return seq_num, is_ack, is_syn, is_fin, recv_window, data