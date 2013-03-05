#!/usr/bin/python

import socket
from struct import pack, unpack

PROTOCOL_VERSION = 0x200
TYPE_BOOL = 0
TYPE_NUMBER = 1
TYPE_STRING = 2
TYPE_BOOL_ARRAY = 16
TYPE_NUMBER_ARRAY = 17
TYPE_STRING_ARRAY = 18
MSG_NOOP = 0
MSG_HELLO = 1
MSG_UNSUPPORTED = 2
MSG_HELLO_COMPLETE = 3
MSG_ASSIGN = 16
MSG_UPDATE = 17

class NetworkTablesClient(object):
    def __init__(self, server, port=1735, debug=False):
        self.server = server
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server, port))
        self.sock.settimeout(1)
        self.tables = {}
        self.debug = debug
        self.sendHello()

    def __iter__(self):
        return iter([[x[0], x[2]] for x in self.tables.values()])

    def send(self, data):
        self.sock.send(data)

    def sendHello(self):
        if self.debug:
            print "Sending Hello"
        self.send(pack(">bH", 1, PROTOCOL_VERSION))

    def _recv(self, count):
        buf = ""
        for i in range(0, count):
            buf += self.sock.recv(1)
        return buf

    def readType(self, entry_type):
        if entry_type == TYPE_BOOL:
            value = self._readBool()
        elif entry_type == TYPE_NUMBER:
            value = self._readNumber()
        elif entry_type == TYPE_STRING:
            value = self._readString()
        elif entry_type == TYPE_BOOL_ARRAY:
            value = self._readBoolArray()
        elif entry_type == TYPE_NUMBER_ARRAY:
            value = self._readNumberArray()
        elif entry_type == TYPE_STRING_ARRAY:
            value = self._readStringArray()
        else:
            value = None
        return value

    def process(self):
        first_byte = ord(self._recv(1))
        if self.debug:
            print "First byte: %d" % first_byte
        if first_byte == MSG_NOOP:
            pass
        elif first_byte == MSG_HELLO:
            version = unpack(">H", self._recv(2))[0]
            if self.debug:
                print "Hello from client: version %d. Why is client receiving Hello?" % version
        elif first_byte == MSG_UNSUPPORTED:
            version = unpack(">H", self._recv(2))[0]
            if self.debug:
                print "Unsupported version, supports %d" % version
        elif first_byte == MSG_HELLO_COMPLETE:
            if self.debug:
                print "Hello complete."
        elif first_byte == MSG_ASSIGN:
            bytes_to_read = unpack(">H", self._recv(2))[0]
            data = self._recv(bytes_to_read)
            entry_type, entry_id, seq_num = unpack(">BHH", self._recv(5))
            value = self.readType(entry_type)
            self.tables[entry_id] = [data, entry_type, value]
        elif first_byte == MSG_UPDATE:
            entry_id, seq_num = unpack(">HH", self._recv(4))
            if self.debug:
                print "Update (%d)" % entry_id
            name, entry_type = self.tables[entry_id][:2]
            value = self.readType(entry_type)
            self.tables[entry_id] = [name, entry_type, value]
        else:
            if self.debug:
                print "Unknown value %d" % first_byte

    def _readBool(self):
        return unpack(">?", self._recv(1))[0]

    def _readNumber(self):
        return unpack(">d", self._recv(8))[0]

    def _readString(self):
        length = unpack(">H", self._recv(2))[0]
        return self._recv(length)

    def _readBoolArray(self):
        length = unpack(">B", self._recv(1))[0]
        data = []
        for i in range(0, length):
            data.append(self._readBool())
        return data

    def _readNumberArray(self):
        length = unpack(">B", self._recv(1))[0]
        data = []
        for i in range(0, length):
            data.append(self._readNumber())
        return data

    def _readStringArray(self):
        length = unpack(">B", self._recv(1))[0]
        data = []
        for i in range(0, length):
            data.append(self._readString())
        return data

if __name__ == "__main__":
    import sys
    nt = NetworkTablesClient(sys.argv[1])
    old = {}
    while 1:
        nt.process()
        new = dict(nt)
        for i in new:
            if i not in old or old[i] != new[i]:
                print "------"
                print i, new[i]
            old[i] = new[i]
