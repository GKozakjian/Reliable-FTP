import threading
import time
import socket
import pickle
import hashlib
from PDU.client_rftp_pdu import *
import random


class Client(threading.Thread):
    local_host_ip = None
    local_host_port = None
    remote_host_ip = None
    remote_host_port = None
    client_udp_socket = None
    file_name = None
    hash_function = None
    file_to_write = None
    timeout_value = None
    auto_timeout_optimization = None
    timer = None
    MTU = None
    offset = None
    transmission_state = None
    data_chunk_received_in_time = None
    verbose_mode = None

    def __init__(self, remote_host_ip, remote_host_port, flag_verbose):
        threading.Thread.__init__(self)
        self.client_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.remote_host_ip = remote_host_ip
        self.remote_host_port = remote_host_port
        self.file_name = "Files/ctest.pdf"
        self.timeout_value = 1
        self.hash_function = hashlib.md5()
        self.MTU = 1506
        self.offset = 0
        self.transmission_state = "setup"
        self.data_chunk_received_in_time = 0

        # verbose mode
        self.verbose_mode = False

        # check for verbose mode
        if flag_verbose == '-v':
            self.verbose_mode = True

    def run(self):
        self.bind_socket()

    def bind_socket(self):
        # set socket as reusable and bind it
        self.client_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.local_host_port = random.randint(30000, 60000)
        self.client_udp_socket.bind(("localhost", self.local_host_port))
        self.client_udp_socket.settimeout(self.timeout_value)

        # send a hello to server
        self.hello_server()

    def hello_server(self):
        while True:
            try:
                # hello the server to check its availability
                hello_message = client_rftp_pdu(1, 3, "", "", "", "")
                serialized_hello_message = pickle.dumps(hello_message, pickle.HIGHEST_PROTOCOL)
                self.client_udp_socket.sendto(serialized_hello_message, (self.remote_host_ip, self.remote_host_port))

                # if verbose mode, print messages
                if self.verbose_mode:
                    print("          + Client: Hello Request Sent")

                # wait for hello reply from server
                hello_reply, remote_socket_address = self.client_udp_socket.recvfrom(self.MTU)
                serialized_hello_reply = pickle.loads(hello_reply)
                if serialized_hello_reply.answer_code == 200:
                    break
            except:
                # if the server reply not received in time, then increase timeout to next value
                self.increase_timout()
                if self.verbose_mode:
                    print("          + Client: Hello phase not completed with server")
        self.create_file()

    def create_file(self):
        self.file_to_write = open(self.file_name, 'wb')
        self.transmission_state = "running"
        self.start_file_transfer()

    def start_file_transfer(self):
        if self.verbose_mode:
            print("          + Client: Started File Transfer")
            print(" 3- Client: Started Receiving Blocks")

        while True:
            try:
                # request next block/chunk of data
                next_data_chunk_request_pdu = client_rftp_pdu(1, 1, "", 1, self.offset, self.file_name)
                self.client_udp_socket.sendto(pickle.dumps(next_data_chunk_request_pdu, pickle.HIGHEST_PROTOCOL), (self.remote_host_ip, self.remote_host_port))
                #
                if self.verbose_mode:
                    print("          + Client (Data Block Request): [oppcode: " + str(next_data_chunk_request_pdu.opcode) + ", offset: " + str(next_data_chunk_request_pdu.offset) +", file_id: " + str(next_data_chunk_request_pdu.file_id) +", file name: " + next_data_chunk_request_pdu.file_name + "]")

                # increment the offset
                self.offset += 1024

                # receive requested data block/chunk
                received_datagram, remote_socket_address = self.client_udp_socket.recvfrom(1506)

                # increment well received data cunks
                self.increment_data_chunk_received_count_in_time()

                # pickle to get the payload object
                serialized_datagram = pickle.loads(received_datagram)

                # check if transmission is over
                if serialized_datagram.opcode == 4:
                    self.transmission_state = "stopped"

                # check signature
                received_signature = serialized_datagram.checksum
                self.hash_function.update(serialized_datagram.buffer)
                message_signature = self.hash_function.hexdigest()

                # if data received with no corruption, write it to the file
                if received_signature == message_signature:
                    self.file_to_write.write(serialized_datagram.buffer)
                    if self.verbose_mode:
                        print("          + Client (Data Block Reply): [oppcode: " + str(serialized_datagram.opcode)  + ", checksum: " + str(serialized_datagram.checksum) +"]" )

                # if hash does not match, then data corrupt
                else:
                    # if final packet, hash will mismatch so pass
                    if self.transmission_state == "stopped":
                        pass
                    else:
                        self.offset -= 1024
                        if self.verbose_mode:
                            print("  - checksum mismatch detected, and re-transmission request will be sent")

                # optimize channel: if after incrementing the timout, channel returns normal, decrease the timout
                if self.data_chunk_received_in_time % 3 == 0 and self.auto_timeout_optimization:
                    self.optimize_timout()
                    self.auto_timeout_optimization = False

                # add some sleep time between transmissions
                time.sleep(0.01)
            # some error or timeout
            except:
                if self.transmission_state == "stopped":
                    self.file_to_write.close()
                    self.stop_client()

                elif self.transmission_state == "running":
                    self.increase_timout()
                    self.auto_timeout_optimization = True
                    if self.verbose_mode:
                        print(" - Client: timeout value increased to " + str(self.timeout_value))
                    self.offset -= 1024

                    # if timout is 10, then close connection
                    if self.timeout_value == 10:
                        # notify server to stop transmission
                        # request next block/chunk of data
                        next_data_chunk_request_pdu = client_rftp_pdu(1, 5, "", 1, "", "")
                        self.client_udp_socket.sendto(
                            pickle.dumps(next_data_chunk_request_pdu, pickle.HIGHEST_PROTOCOL),
                            (self.remote_host_ip, self.remote_host_port))
                        if self.verbose_mode:
                            print(" - Client: High timout value, connection is closing")

                        self.stop_client()

    def increase_timout(self):
        self.timeout_value = (2 * self.timeout_value) + 2
    # if response more than 10 seconds, terminate the transmission

    def terminate_transmission(self):
        print(" - Client: Session terminated. Receiver not responding")

    def stop_client(self):
        print(" - Client: Stopped RFTP Client")
        exit()

    def increment_data_chunk_received_count_in_time(self):
        self.data_chunk_received_in_time = (self.data_chunk_received_in_time + 1) % 4

    def optimize_timout(self):
        self.timeout_value = (self.timeout_value / 2) - 1
