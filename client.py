import socket
import utils
import time
import struct
import os
import threading


def client():
    connect()
    # send a request to the other part's server four seconds after the system has not received or sent messages
    while True:
        if time.time() - utils.last_receive_send_time > 5:
            connect_threading = threading.Thread(
                target=connect,
                name="check"
            )
            connect_threading.start()
            time.sleep(2)
        time.sleep(0.1)

def connect():
    port = 22222
    d_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            d_connection.connect((utils.host, port))
            utils.last_receive_send_time = time.time()
            break
        except ConnectionRefusedError:
            time.sleep(0.05)
            continue


    def receive(d_connection: socket):
        """accepts files returned by the server"""

        header_len = struct.unpack('i', d_connection.recv(4))[0]
        header = eval(d_connection.recv(header_len).decode())

        if header['command'] == "TRA":
            # persist single file
            write(header['name'], header['data_len'], d_connection)

        if header['command'] == "MER":
            # join all temp file into one big file which is split
            utils.merge(header['name'])
            d_connection.send('F'.encode())

    while True:
       try:
           receive(d_connection)
       except ConnectionResetError as e2:
           break
       except Exception as e:
           break




def write(file_name, file_size, data_connection):
    data_connection.send('O'.encode())
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'wb') as f:
        utils.file_record['get_list'].append(file_name)
        rev_size = 0
        while rev_size < file_size:
            data_len = data_connection.recv(1024)
            f.write(data_len)
            rev_size += len(data_len)
    utils.last_receive_send_time = time.time()
    utils.write_success(file_name)
    data_connection.send('A'.encode())




