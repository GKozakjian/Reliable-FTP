import threading
import time
import socket
import pickle
from PDU.server_rftp_pdu import *
import hashlib
import random
import os


class Server(threading.Thread):
    local_host_ip = None
    local_host_port = None
    remote_host_ip = None
    remote_host_port = None
    server_udp_socket = None
    hash_function = None
    file_name = None
    file_size = None
    file_to_transmit = None
    transmitted_chunk = None
    timeout_value = None
    timer = None
    MTU = None
    offset = None
    error_rate = None
    transmission_state = None

    def __init__(self, local_host_ip, local_host_port, flag_verbose, flag_error):
        threading.Thread.__init__(self)
        self.server_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.local_host_ip = local_host_ip
        self.local_host_port = local_host_port
        self.hash_function = hashlib.md5()
        self.MTU = 1024
        self.timeout_value = 1
        self.file_name = "Files/stest.pdf"
        self.file_size = os.path.getsize(self.file_name)
        self.offset = 0
        self.transmission_state = "setup" \
                                  ""
        # verbose mode
        self.verbose_mode = False

        # check for verbose mode
        if flag_verbose == '-v':
            self.verbose_mode = True
        # error rate
        if flag_error is None:
            self.error_rate = 0
        else:
            self.error_rate = random.randint(1, 3)
            print(" 0- Channel Error Rate: " +str(self.error_rate) +"0%")

    def run(self):
        self.bind_socket()

    def bind_socket(self):
        # set socket as reusable and bind it
        self.server_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_udp_socket.bind((self.local_host_ip, int(self.local_host_port)))
        self.server_udp_socket.settimeout(self.timeout_value)
        self.wait_for_hello()

    def wait_for_hello(self):
        if self.verbose_mode:
            print(" 1- Server Waiting for Hello Message: ")

        while True:
            try:
                # receive hello from client
                hello_message, remote_socket_address = self.server_udp_socket.recvfrom(self.MTU)

                # set remote host socket IP and Port numbers
                self.remote_host_ip = remote_socket_address[0]
                self.remote_host_port = remote_socket_address[1]

                # get message, and check for opcode
                serialized_hello_message = pickle.loads(hello_message)
                if serialized_hello_message.opcode == 3:
                    hello_reply = server_rftp_pdu(1, 3, "", "", "", 200, "", "")
                    serialized_hello_reply = pickle.dumps(hello_reply, pickle.HIGHEST_PROTOCOL)
                    self.server_udp_socket.sendto(serialized_hello_reply, (self.remote_host_ip, self.remote_host_port))

                    # if verbose mode, print messages
                    if self.verbose_mode:
                        print("          + Server: Hello Reply Sent")
                    break
            except:
                print("          + Server: still waiting for hello")
        self.setup_file()

    def setup_file(self):
        self.file_to_transmit = open(self.file_name, 'rb')
        self.transmission_state = "running"
        self.start_file_transfer()

    def start_file_transfer(self):
        if self.verbose_mode:
            print(" 2- Client: File Transfer Initiated")
            print("          + Server: Started File Transfer")
        i = 1
        while True:
            try:
                # receive next chunk request from the client
                next_data_chunk_pdu, remote_socket_address = self.server_udp_socket.recvfrom(self.MTU)
                serialized_next_data_chunk_pdu = pickle.loads(next_data_chunk_pdu)

                # if transmission stopped by client due to high latency, stop server
                if serialized_next_data_chunk_pdu.opcode == 5:
                    break

                # sync offset and seek file to read next block
                self.offset = serialized_next_data_chunk_pdu.offset
                self.file_to_transmit.seek(serialized_next_data_chunk_pdu.offset, 0)
                self.transmitted_chunk = self.file_to_transmit.read(1024)



                # if end of file, notify the client
                if self.transmitted_chunk == b'':
                    self.transmission_state = "stopped"
                    next_rftp_pdu = server_rftp_pdu(1, 4, "", 1, self.offset, 200, self.file_to_transmit.tell(),
                                                    self.transmitted_chunk)
                    self.server_udp_socket.sendto(pickle.dumps(next_rftp_pdu, pickle.HIGHEST_PROTOCOL),
                                                  (self.remote_host_ip, self.remote_host_port))
                    break

                if i == 10:
                    i = 1
                if i + self.error_rate >= 10:
                    i += 1
                    continue
                # calculate hash of new data and create new pdu
                self.hash_function.update(self.transmitted_chunk)
                message_signature = self.hash_function.hexdigest()
                next_rftp_pdu = server_rftp_pdu(1, 2, message_signature, 1, self.offset, 200, 512, self.transmitted_chunk)
                self.server_udp_socket.sendto(pickle.dumps(next_rftp_pdu, pickle.HIGHEST_PROTOCOL), (self.remote_host_ip, self.remote_host_port))
                i += 1


            except:
                if self.verbose_mode:
                    print(" - Server: Timed out")
                    # self.increase_timout()
                    # print(" - Server: timeout value increased to " + str(self.timeout_value))
                if self.transmission_state == "stopped":
                    print("tiimed out, server stopping ... ")
                    self.stop_server()
        self.stop_server()

    def increase_timout(self):
        self.timeout_value = (2 * self.timeout_value) + 2

    def stop_server(self):
        print(" - Server: Stopped RFTP Server")
        exit()

