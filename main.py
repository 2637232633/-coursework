import threading
import utils
import time
import client
import server

utils.get_host()
utils.get_file_record()
utils.generate_file_record()
utils.get_last_receive_send_time
a = utils.file_record


server_threading = threading.Thread(
    target=server.server,
    name="server"
)
server_threading.start()

client_threading = threading.Thread(
            target=client.client,
            name="sent"
        )
client_threading.start()

server_threading.join()
client_threading.join()
