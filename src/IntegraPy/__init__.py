# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function
'''
integra -- a module implementing Satel integration protocol for
Satel Integra and ETHM-1 modules
'''
import time
import logging
from datetime import datetime
from struct import unpack
from binascii import hexlify
from socket import socket, AF_INET, SOCK_STREAM


from .constants import HEADER, FOOTER, HARDWARE_MODEL, LANGUAGES
from .framing import (
    checksum, prepare_frame, parse_event, parse_name, set_bits_positions,
    bytes_with_bits_set, format_user_code
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


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
        # Name cache
        # Keys: (kind, number)
        # Values: NameRecords
        self._name_cache = {}

    def run_command(self, cmd):
        command = prepare_frame(cmd)
        log_frame('Sending command: ', command)

        for attempt in range(self.max_attempts):
            sock = socket(AF_INET, SOCK_STREAM)
            sock.connect((self.host, self.port))

            if not sock.send(command):
                raise Exception("Error sending frame.")

            resp = bytearray(sock.recv(100))
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
        log.debug('Output: %s', repr(output))

        # EF - result
        if output[0] == 0xEF:
            log.debug('Error output: %s', repr(output))
            # FF - command will be processed, 00 - OK
            if not output[1] in (0xFF, 0x00):
                raise Exception(
                    'Integra reported an error code %X' % output[1]
                )

        # Function result
        elif output[0] != command[2]:
            raise Exception(
                 "Response to a wrong command - got %s expected %s" % (
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
        '''
        Returns a dict describing connected Integra
        '''
        resp = self.run_command('7E')
        return dict(
            model='INTEGRA ' + HARDWARE_MODEL.get(resp[0], 'UNKNOWN'),
            version='{:c}.{:c}{:c} {:c}{:c}{:c}{:c}-{:c}{:c}-{:c}{:c}'.format(
                *resp[1:12]
            ),
            language=LANGUAGES.get(resp[12], 'Other'),
            settings_stored=(resp[13] == 255)
        )

    def get_time(self):
        '''
        Get current Integra time
        '''
        resp = hexlify(self.run_command('1A'))
        return datetime(
            year=int(resp[:4]),
            month=int(resp[4:6]),
            day=int(resp[6:8]),
            hour=int(resp[8:10]),
            minute=int(resp[10:12]),
            second=int(resp[12:14])
        )

    def get_name(self, kind, number):
        '''
        Gets Integras object name. Caches responses.
        '''
        try:
            name_rec = self._name_cache[(kind, number)]
        except KeyError:
            resp = self.run_command(b'EE' + hexlify(bytearray([kind, number])))
            name_rec = parse_name(resp)
            name_rec.encoding = self.encoding
            self._name_cache[(kind, number)] = name_rec

        return name_rec

    def get_event(self, event_id=b'FFFFFF'):
        '''
        Gets an event struct; to get a next event, call
        integra.get_event(last_event.event_index)
        '''
        current_time = self.get_time()
        resp = self.run_command(b'8C' + event_id)

        evt = parse_event(resp)
        evt.integra = self
        evt.current_year = current_time.year

        return evt

    def get_violated_zones(self):
        '''
        Gets a list of violated zones
        '''
        resp = self.run_command(b'00')
        return set_bits_positions(resp, 1)

    def get_active_outputs(self):
        '''
        Gets a list of numbers of outputs in ON state
        '''
        resp = self.run_command(b'17')
        return set_bits_positions(resp, 1)

    def toggle_outputs(self, indexes):
        '''
        Toggles outputs with selected indexes;
        !! Warning !! not tested
        '''
        self.run_command(
            b'91' +
            hexlify(format_user_code(self.user_code) +
            bytes_with_bits_set(indexes, 128, 1))
        )

    def get_armed_partitions(self):
        '''
        Gets a list of armed partitions
        '''
        resp = self.run_command(b'0A')
        return set_bits_positions(resp, 1)
