import struct


class DataHeader:
    def __wrap(self, header: dict):
        header = str(header).encode()
        self.header = header
        self.header_length = len(header)
        return struct.pack("i", self.header_length),self.header

    # transfer files command
    def trans(self, filename: bytes, data_len: int):
        self.command = "TRA"
        self.name = filename
        self.data_len = data_len
        header_len, header = DataHeader().__wrap(self.__dict__)
        return header_len, header

    # send merge file command (file be merged is filename)
    def merge(self, filename: bytes, data_len: int):
        self.command = "MER"
        self.name = filename
        self.data_len = data_len
        header_len, header = DataHeader().__wrap(self.__dict__)
        return header_len, header

