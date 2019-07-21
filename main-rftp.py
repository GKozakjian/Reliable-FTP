from Client.client import *
from Server.server import *
import time
import sys


def main(flag_verbose, flag_error):
    # #create the receiver node and start it
    server_node = Server("localhost", 22222, flag_verbose, flag_error)
    server_node.start()
    time.sleep(2)

    #create the sender node and start it
    # client_node = Client("localhost", 22222, argv1_file)
    client_node = Client("localhost", 22222, flag_verbose)
    client_node.start()

    #join the threads, so that the main does not exit
    server_node.join()
    client_node.join()

    #finish execution when both child threads join
    exit()


# simulator starting point
    # take the arguments, and initialize the nodes
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

