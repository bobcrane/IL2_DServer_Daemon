""" Python class to handle TCP/IP communications with Dserver.exe program """

import socket
import struct
import re
import time
from urllib.parse import unquote


def pack_message(msg):
    """  Returns packed string msg for TCP send """
    enc_str = msg.encode(encoding='UTF-8')
    # packet = struct.pack("H{0}sx".format(len(msg)), len(msg) + 1, msg)
    return struct.pack(f"H{len(enc_str)}sx", len(enc_str) + 1, enc_str)


def unpack_message(data):
    # print(f"{data}; ", end='')
    try:
        # data_format = "H{0}sx".format(struct.unpack("h", data[0:2])[0] - 1)
        data_format = f"H{len(data) - 3}sx"  # subtract first two bytes (reprsenting length) and last null byte
        # print(f"unpack.format = {data_format}, len={len(data)}")
        upk_data = struct.unpack(data_format, data)
        return upk_data
    except struct.error as e:
        # print(f"\nstruct.error: {e}")
        raise ValueError("Structure Error.")


class RemoteConsoleClient:
    def __init__(self, host, port, login, password):
        self.host = host
        self.port = port
        self.login = login
        self.password = password
        self.client = None
        self.response_string = ""

        """ Il-2's remote console returned response dictionary """
        self.Dserver_response_dict = {
            0: 'Socket error',  # Dserver does not return this value but I added for a socket error
            1: 'OK',
            2: 'Unknown error',
            3: 'Unknown command',
            4: 'Parameter count error',
            5: 'Receiver buffer error',
            6: 'Authorization incorrect',
            7: 'DServer not running',
            8: 'DServer user error',
            9: 'Unknown user error'
        }

    """ Connect to Dserver and provide login credentials.  """
    def connect(self):
        print("Trying to connect to DServer.exe...")
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.host, self.port))
        except socket.error:
            print(f"Error: Failed to connect to IL-2 Dserver")
            return False
        else:
            print("Connected...attempting authorization...", end='')
            # send login credentials
            # time.sleep(1)
            self.send(f"auth {self.login} {self.password}")
            print("authorized.")
            return True

    def send(self, msg):
        """ Send message string to DServer string via TCP protocol.  Brute force send until it completes
            --reestablishing connection if needed """

        packet = pack_message(msg)

        completed = False
        return_code = -1
        while not completed or return_code != 1:
            try:
                self.client.send(packet)
                data = self.client.recv(4096)
                # print(data)
            except socket.error as e:
                print(f"Unable to send or receive message to or from Dserver: {e}\nReconnecting...")
                while not self.connect():  # connect to server--loops indefinitely until connect
                    time.sleep(3)
                continue  # try sending again now above
            else:
                # obtain return code in Dserver's binary response
                if len(data) == 0:  # rarely data returned is empty so catch this and try again
                    time.sleep(1)
                    continue
                try:
                    unpacked_return_str = unpack_message(data)
                    decoded_return_string = unpacked_return_str[1].decode()
                except (AttributeError, IndexError, ValueError) as e:
                    print(f"Exception error decoding received packet: {e}")
                    continue

                self.response_string = unquote(unquote(decoded_return_string))
                if msg == "getplayerlist":
                    print(f"'getplayerlist' response: {self.response_string}")
                return_code = int(re.search(r'\d+', decoded_return_string).group())  # get the first number in string and return only it
                if return_code == 1:
                    # sometimes getplayerlist command does not return a player list due to server status...
                    # continue sending until one is given
                    if msg == "getplayerlist" and "playerList" not in self.response_string:
                        print("Trying to get player list again....")
                        time.sleep(1)
                    else:
                        completed = True
                else:
                    print(f"Dserver code {return_code} trying to send message '{msg}': {self.response_lookup(return_code)}")
                    time.sleep(2)

    def close(self):
        self.client.close()

    def response_lookup(self, num):
        return self.Dserver_response_dict[num]

    def send_msg(self, message):
        """ Sends long message to console slowly to circumvent anti-spam filter """
        for s in message.split('\n'):
            self.send("chatmsg 0 0 " + s)
            time.sleep(.2)  # cannot flood remote console with messages too fast or lines get dropped
