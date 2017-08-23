# -*- coding: UTF-8 -*-
'''
integra -- a module implementing Satel intgration protocol for
Satel Integra and ETHM-1 modules
'''
import time
import logging


from struct import unpack
from binascii import hexlify
from socket import socket, AF_INET, SOCK_STREAM


log = logging.getLogger(__name__)


# device types as defined by Satel manual
PARTITION = "00"
ZONE = "01"
OUTPUT = "04"

HEADER = b'\xFE\xFE'
FOOTER = b'\xFE\x0D'
HARDWARE_MODEL = {
    0: "24",
    1: "32",
    2: "64",
    3: "128",
    4: "128-WRL SIM300",
    66: "64 PLUS",
    67: "128 PLUS",
    132: "128-WRL LEON"
}
LANGUAGES = {
    0: 'Polish',
    1: 'English'
}

def checksum(command):
    '''
    Satel communication checksum
    '''
    crc = 0x147A
    for b in command:
        # rotate (crc 1 bit left)
        crc = ((crc << 1) & 0xFFFF) | (crc & 0x8000) >> 15
        crc = crc ^ 0xFFFF
        crc = (crc + (crc >> 8) + b) & 0xFFFF

    return crc


def prepare_frame(command):
    '''
    Creates a communication frame (as per Satel manual)
    '''
    data = bytearray.fromhex(command)
    c = checksum(data)
    data.append(c >> 8)
    data.append(c & 0xFF)
    data = data.replace(b'\xFE', b'\xFE\xF0')

    return HEADER + data + FOOTER


def log_frame(msg, frame):
    log.debug(
        msg + '"{0}", length: {1}',
        hexlify(frame),
        len(frame)
    )


class Integra(object):

    def __init__(
        self,
        user_code,
        host,
        port=7094,
        encoding='cp1250',
        delay=0.002,
        max_attempts=3
    ):
        self.host = host
        self.user_code = user_code
        self.port = port
        self.encoding = encoding

        # Delay between commands
        self.delay = delay
        # Maximum repetitions
        self.max_attempts = max_attempts

    def run_command(self, cmd):
        command = prepare_frame(cmd)
        log_frame('Sending command: ', command)

        for attempt in range(self.max_attempts):
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((self.host, self.port))

            if not sock.send(command):
                raise Exception("Error sending frame.")

            resp = sock.recv(100)
            log_frame('Response received: ', resp)
            sock.close()

            # integra will respond "Busy!" if it gets next message too early
            if (resp[0:8] == b'\x10\x42\x75\x73\x79\x21\x0D\x0A'):
                time.sleep(self.delay * (attempt + 1))
            else:
                break

        # Check message
        if (resp[0:2] != HEADER):
            raise Exception('Wrong header - got {}'.format(hexlify(resp[:2])))

        if (resp[-2:] != FOOTER):
            raise Exception("Wrong footer - got {}".format(hexlify(resp[-2:])))

        output = resp[2:-2].replace(b'\xFE\xF0', b'\xFE')

        # EF - result
        if output[0] == b'\xEF':
            # FF - command will be processed, 00 - OK
            if not output[1] in b'\xFF\x00':
                raise Exception(
                    'Integra reported an error code %X' % output[1]
                )

        # Function result
        elif output[0] != command[2]:
            raise Exception(
                "Response to a wrong command - got %X expected %X" % (
                    output[0], command[2]
                )
            )

        # Calculate response checksum
        calc_resp_sum = checksum(output[:-2])
        extr_resp_sum = unpack('>H', output[-2:])[0]

        if extr_resp_sum != calc_resp_sum:
            raise Exception(
                "Wrong checksum - got %d expected %d" % (
                    extr_resp_sum, calc_resp_sum
                )
            )

        # return only data
        return output[1:-2]

    def get_version(self):
        resp = self.run_command('7E')
        print(resp[12])
        return dict(
            model='INTEGRA ' + HARDWARE_MODEL.get(resp[0], 'UNKNOWN'),
            version='{:c}.{:c}{:c} {:c}{:c}{:c}{:c}-{:c}{:c}-{:c}{:c}'.format(
                *resp[1:12]
            ),
            language=LANGUAGES.get(resp[12], 'Other'),
            settings_stored=(resp[13] == 255)
        )
# def ihex(byte):
#     return str(hex(byte)[2:])
#
#
#

#
#
# ''' I only bothered with few of them, feel free to add all newer models
# '''
#
#
#
#
#
# ''' Gets the firmware version as reported by panel, language and whether settings has been copied to flash
# again - I only check if language is English or other
# '''
#
#

#
#
# ''' Gets the Integra time. Unfortunately, it is being sent in a rather weird format, hence the mess below
# '''
#
#
# def iTime():
#     r = sendcommand("1A")
#     itime = ihex(r[0]) + ihex(r[1]) + "-" + ihex(r[2]) + "-" + ihex(r[3]) + " " + ihex(r[4]) + ":" + ihex(
#         r[5]) + ":" + ihex(r[6])
#     return itime
#
#
# ''' Gets name of the zone and output. Could be easily extended to get name of users, expanders and so on
# '''
#
#
# def iName(number, devicetype):
#     number = str(hex(number))[2:]
#     if len(number) == 1:
#         number = "0" + number
#     r = sendcommand("EE" + devicetype + str(number))
#     return r[3:].decode(config.encoding)
#
#
# ''' Checks violated zones. This make separate calls to get name of the violated zones. In a real life software,
# this should be cached and synchronised when data are change (i.e. rarely, as zones, outputs et ceterea usually
# keep their names for a long time). In this demo, the more enabled outputs you have, the longer this script  will
# take to execute
# '''
#
#
# def iViolation():
#     r = sendcommand("00")
#     v = ""
#     for i in range(0, 15):
#         for b in range(0, 7):
#             if 2 ** b & (r[i]):
#                 v += str(8 * i + b + 1) + " " + iName(8 * i + b + 1, ZONE) + ":*\n"
#     print(v)
#
#
# ''' Checks enabled outputs. See the comment for iViolation
# '''
#
#
# def iOutputs():
#     r = sendcommand("17")
#     o = ""
#     for i in range(0, 15):
#         for b in range(0, 7):
#             if 2 ** b & r[i]:
#                 o += str(8 * i + b + 1) + " " + iName(8 * i + b + 1, OUTPUT) + ": ON\n"
#     print(o)
#
#
# ''' Returns arm status for the partition (true: armed, false: disarmed)
# '''
#
#
# def iArmStatus(partition):
#     r = sendcommand("0A")
#     if 2 ** (partition % 8) & r[partition >> 3]:
#         return True
#     else:
#         return False
#
#
# ''' Returns a string that can be sent to enable/disable a given output
# '''
#
#
# def outputAsString (output):
#     string = ""
#     byte = output // 8 + 1
#     while byte > 1:
#         string += "00"
#         byte -= 1
#     out = 1 << (output % 8 - 1)
#     result = str(hex(out)[2:])
#     if len(result) == 1:
#         result = "0" + result
#     string += result
#     while len(string) < 32:
#         string += "0"
#     return string
#
#
# ''' Switches the state of a given output
# '''
#
#
# def iSwitchOutput(code, output):
#     while len(code) < 16:
#         code += "F"
#     output = outputAsString(output)
#     cmd = "91" + code + output
#     r = sendcommand(cmd)
#
#
# #### BASIC DEMO
# ''' ... and now it is the time to demonstrate what have we learnt today
# '''
# if len(sys.argv) < 1:
#     print("Execution: %s IP_ADDRESS_OF_THE_ETHM1_MODULE" % sys.argv[0], file=sys.stderr)
#     sys.exit(1)
#
# iVersion()
# print("Integra time: " + iTime())
# partname = iName(1, PARTITION)
# print("%s armed: %s" % (partname, iArmStatus(0)))
# print("Violated zones:")
# iViolation()
# print("Active outputs:")
# iOutputs()
# print("Switching output:")
# #iSwitchOutput(config.usercode, 11)
# print("Thanks for watching.")
