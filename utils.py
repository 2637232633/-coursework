import os
import hashlib
import json
import time
import threading
import argparse
import zlib

# root
path = "./share"
# current host IP address
host = ''
# current host name
pc_name = ''
# the time when the program last accepted or sent a file
last_receive_send_time = 0


def get_host():
    """ initial host and pc name """
    global host
    global pc_name

    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--ip', default='127.0.0.1')
    args = parser.parse_args()
    host = args.ip
    if host == '192.168.56.105':
        pc_name = "PC_A"
    else:
        pc_name = "PC_B"


def get_last_receive_send_time():
    """ initial the time when the program last accepted or sent a file """
    global last_receive_send_time
    last_receive_send_time = time.time()


def file_record_load() -> dict:
    """ load file_record into memory """
    with open("file_record.json", "r") as file_structure:
        file_record = json.load(file_structure)
    return file_record


class FileRecord:
    file_record_lock = threading.Lock()

    def __init__(self, file_record):
        self.file_record = file_record_load()

    def __getitem__(self, key):
        return self.file_record[key]

    def __setitem__(self, key, value):
        if type(value) == set:
            value = list(value)
        self.file_record_lock.acquire()
        self.file_record[key] = value
        self.file_record_lock.release()


file_record = FileRecord(file_record_load())


def all_files_path_without_tempfile(rootDir):
    """ get all files except those end with tempfile"""
    dir_list = set()
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file_path = os.path.join(root, file)
            if (file_path.endswith("tempfile")):
                continue
            dir_list.add(file_path)

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            all_files_path_without_tempfile(dir_path)
    return dir_list


def all_files_path_tempfile(rootDir) -> list():
    """ get all files end with "tempfile" """
    dir_list = set()
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file_path = os.path.join(root, file)
            if (file_path.endswith("tempfile")):
                dir_list.add(file_path)

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            all_files_path_without_tempfile(dir_path)
    dir_list = list(dir_list)
    return dir_list


def all_files_name_md5_size_time(rootDir) -> list:
    """ get name, md5, size, modify time for all files in the share folder """
    dir_list = list()
    for root, dirs, files in os.walk(rootDir):
        for file in files:
            file_path = os.path.join(root, file)
            file_md5 = get_file_md5(file_path)
            dir_list.append({"name": file_path, "md5": file_md5, "size": os.path.getsize(file_path),
                             "time": os.path.getmtime(file_path)})

        for dir in dirs:
            dir_path = os.path.join(root, dir)
            all_files_path_without_tempfile(dir_path)
    return dir_list


def generate_file_record() -> (dict, bool):
    global file_record
    transition_list, delete_list, file_now_list, file_now_info_list, is_diff = update()

    file_record["trans_list"] = transition_list
    file_record["del_list"] = delete_list
    file_record["file_list"] = file_now_list
    file_record["file_list_info"] = file_now_info_list
    return file_record, is_diff


def update() -> (list, list, list, list, bool):
    global host
    trans_set = set(file_record['trans_list'])
    file_prev = set(file_record["file_list"])
    file_recv = set(file_record["recv_list"])
    delete_set = set(file_record['del_list'])
    file_left = file_prev - file_recv
    file_now_info = all_files_name_md5_size_time(path)
    file_now = set()
    for dir in file_now_info:
        file_now.add(dir['name'])
    trans_set.update(file_now - file_prev)
    trans_set.update(file_left)
    delete_set.update(file_prev - file_now)
    file_intersect = file_prev & file_now
    diff_set = diff(file_intersect, file_now_info)
    trans_set.update(diff_set)
    trans_set = trans_set - set(file_record['get_list'])
    trans_set = list(trans_set)
    file_now = list(file_now)
    delete_set = list(delete_set)
    is_diff = False
    if trans_set or delete_set:
        is_diff = True
    return trans_set, delete_set, file_now, file_now_info, is_diff


def diff(file_intersect, file_now_info) -> list:
    trans_list = []
    for file_name in file_intersect:
        for info_dict in file_record['file_list_info']:
            if info_dict['name'] == file_name:
                if os.path.getmtime(file_name) != info_dict['time'] or os.path.getsize(file_name) != info_dict['size']:
                    trans_list.append(file_name)
                # else:
                #     for info_dict_now in file_now_info:
                #         if info_dict_now['name'] == info_dict['name']:
                #             if info_dict_now['md5'] != info_dict['md5']:
                #                 print("bei xiu gai le md5", file_name)
                #                 trans_list.append(file_name)
                #                 break
                # break

    return trans_list


def file_record_load() -> dict:
    """ load file_record into memory """
    with open("file_record.json", "r") as file_structure:
        file_record = json.load(file_structure)
    return file_record


def persist_file_record():
    """ persist file_record to disk"""
    with open("./file_record.json", "w") as f:
        file_record['trans_list'] = list()
        file_record['del_list'] = list(set(file_record['del_list']))
        file_record['recv_list'] = list(set(file_record['recv_list']))
        json.dump(file_record, f)


def get_file_record():
    """ get file_record """
    global file_record
    file_record = file_record_load()


def get_file_md5(file_path, chunk_size=8192):
    """ get md5 of file """
    h = hashlib.md5()

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def split(real_name: str, size: int) -> list:
    """ divide large files into chunks """
    part_num = 0
    temp_file = []
    with open(real_name, "rb") as file:
        while True:
            data = file.read(size)
            if data:
                part_num += 1
                if part_num < 10:
                    final_num = "0" + str(part_num)
                else:
                    final_num = str(part_num)
                filename = real_name + final_num + "tempfile"
                with open(filename, "wb") as f:
                    f.write(data)
                temp_file.append(filename)
            else:
                break
    return temp_file


def merge(target_path):
    """ merges large files that are transferred in chunks """
    global last_receive_send_time
    temp_file = all_files_path_tempfile("./share")
    temp_file.sort()

    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    with open(target_path, "wb") as tf:
        for file in temp_file:
            with open(file, "rb") as f:
                data = f.read()
                tf.write(data)
            try:
                due_del(file)
            except Exception as e:
                pass
            last_receive_send_time = time.time()
    write_success(target_path)


def write_success(file_name):
    """ write file information into file_record """
    file_record['file_list'].append(file_name)
    file_md5 = get_file_md5(file_name)
    file_record['file_list_info'].append(
        {"name": file_name, "md5": file_md5, "size": os.path.getsize(file_name),
         "time": os.path.getmtime(file_name)})
    temp_set = set(file_record['get_list'])
    file_record['get_list'] = list(temp_set)
    file_record['file_list'] = set(file_record['file_list'])
    file_record['file_list'] = list(file_record['file_list'])


def due_del(pathname):
    """ delete file and file information from file_record """
    os.remove(pathname)
    file_record['get_list']
    if pathname in file_record['file_list']:
        file_record['file_list'].remove(pathname)
        for file_info in file_record['file_list_info']:
            if file_info['name'] == pathname:
                file_record['file_list_info'].remove(file_info)
