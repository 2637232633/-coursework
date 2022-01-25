import socket
import threading
import time
import utils
import os
import dataheader




def server():
    listen()

def listen() -> socket:
    """listen on the port and pass the connect socket to the receiver
    """
    port_data = 22222
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_socket.bind(("", port_data))
    data_socket.listen(1)

    while True:
        try:

            data_connection, _ = data_socket.accept()
            # the execution of the program at this point indicates that the receiver is ready to receive the data
            asdfAS, is_diff = utils.generate_file_record()
            # if trans_list or delete list in file_record is not empty
            if is_diff:
                send_all(data_connection)

            while True:
                if time.time() - utils.last_receive_send_time > 2:
                    asdfAS, is_diff = utils.generate_file_record()
                    if is_diff:
                        send_all(data_connection)
                time.sleep(1)
        except Exception as e:
            pass



def send_all(data_connection : socket):
    """send all file in trans_list of file_record"""
    trans_file = utils.file_record["trans_list"]
    for t_file in trans_file:
        total_size = os.path.getsize(t_file)
        if total_size > 400 * 1024 * 1024:
            block_size = 1024 * 1024 * 20
            temp_file = utils.split(t_file, block_size)
            num = len(temp_file)
            for file in temp_file:
                signal = send_file(file,data_connection)
                if signal:
                    num -= 1
                    os.remove(file)

            if num == 0:
                data_len = os.path.getsize(t_file)

                # send header with command "BIG" means the large file has
                # been transferred and the receiver can begin merging

                header_len, header = dataheader.DataHeader().merge(t_file, data_len)
                data_connection.send(header_len)
                data_connection.send(header)
                is_finished = data_connection.recv(1)
                if is_finished:
                    utils.file_record["recv_list"].append(t_file)
        else:
            send_file(t_file,data_connection)

def send_file(t_file, data_connection):

    """ send single file"""

    data_len = os.path.getsize(t_file)
    header_len, header = dataheader.DataHeader().trans(t_file, data_len)
    data_connection.send(header_len)
    data_connection.send(header)

    msg = data_connection.recv(1).decode()
    if msg:
        with open(t_file, "rb") as f:
            for line in f:
                data_connection.send(line)
        utils.last_receive_send_time = time.time()
        signal = data_connection.recv(1).decode()

        # if the transfer is complete

        if signal:
            utils.file_record["recv_list"].append(t_file)
            utils.persist_file_record()
            utils.persist = time.time()
            return 1

