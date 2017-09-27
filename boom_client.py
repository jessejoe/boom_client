import time
import json
import struct
import socket
import logging
from datetime import datetime
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


class Boom:

    def __init__(self,
                 scan_delay: int = 0,
                 client_name: str = 'BoomPythonClient',
                 **kwargs):
        """
        Calls find_boom_hosts() to discover an available Boom server. See
        find_boom_host() for more info.

        :param scan_delay: see find_boom_host()
        :param client_name: name to identify client to Boom server as
        :param kwargs: see find_boom_hosts()
        """
        self.conn = None
        self.boom_status = None
        self.client_name = client_name
        self.current_eq = None
        self.all_boom_hosts = self.find_boom_hosts(scan_delay, **kwargs)
        if self.all_boom_hosts:
            self.boom_host = self.all_boom_hosts[0]
            logging.info('Using first boom host found: %s', self.boom_host)
        else:
            logging.error('No hosts found, quitting')
            exit(1)

        self.connect_to_host()

    def __del__(self):
        if self.conn:
            # Always close TCP connection
            logging.info('Closing connection')
            self.conn.close()

    @staticmethod
    def find_boom_hosts(scan_delay: int = 0, **kwargs):
        """
        Use mDNS to find hosts with Boom service listening. Run without any
        params to scan for 10s and find all hosts and filterable attributes.
        NOTE: If calling this shortly after itself, it may not be able to find
        anything, not sure why. Must be an mDNS TTL or something.

        :param scan_delay: seconds to wait for Boom server discovery, useful
         if running multiple servers to discover them all.
        :param kwargs: key=value to filter by
        :return: list of Boom servers
        :rtype: list
        """
        discovered_services = []

        # See https://github.com/jstasiak/python-zeroconf/blob/9035c6a246b6856b5087b1bba9a9f3ce5873fcda/examples/browser.py
        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                service = zeroconf.get_service_info(service_type, name)
                # get_service_info() sometimes returns None for some reason...
                if service:
                    # Convert IP address to a more usable non-hex object
                    service.address = socket.inet_ntoa(service.address)
                    logging.info('Found {} service: {}'.format(name, service))
                    discovered_services.append(service)

        zc1 = Zeroconf()
        zc2 = Zeroconf()
        # Inspecting the Boom remote packets shows it scans for two types of
        # Boom mDNS services, so look for both just in case
        ServiceBrowser(
            zc1, "_boom2._tcp.local.", handlers=[on_service_state_change])
        ServiceBrowser(
            zc2, "_boom3._tcp.local.", handlers=[on_service_state_change])

        max_wait = 10
        start_time = datetime.now()
        found_services = []
        while not found_services:
            if (datetime.now() - start_time).seconds > max_wait:
                logging.error(
                    'No services found matching %s, %ss max timeout reached',
                    kwargs, max_wait)
                break
            if kwargs:
                # Filter found services by any specified attributes
                for key, value in kwargs.items():
                    found_services = [
                        service for service in discovered_services
                        if getattr(service, key) == value
                    ]
            else:
                # Just listen for max_wait seconds, useful for searching the
                # first time
                if scan_delay:
                    logging.info('Scanning network for %ss...', max_wait)
                    time.sleep(scan_delay)
                found_services = discovered_services

        zc1.close()
        zc2.close()

        return found_services

    def receive_min_bytes(self, min_bytes: int, max_wait: int = 10):
        """
        Receive from socket until min_bytes has been received

        :param min_bytes: amount of bytes to receive
        :param max_wait: amount of seconds to wait for min_bytes
        :return: received bytes
        :rtype: bytes
        """
        bytes_received = 0
        data = []
        start_time = datetime.now()
        while bytes_received < min_bytes:
            if (datetime.now() - start_time).seconds > max_wait:
                logging.error(
                    'Only %d of %d bytes of data received, %ss max timeout reached',
                    len(data), min_bytes, max_wait)
                break
            # Receive 2 bytes at a time to not receive more than min_bytes
            temp_data = self.conn.recv(2)
            bytes_received += len(temp_data)
            data.append(temp_data)

        return b''.join(data)

    def receive_from_server(self):
        """
        Receive message from the Boom server

        :return: message data
        :rtype: str
        """
        # Boom server always sends qty2 4-byte hex integers before data
        next_size = self.receive_min_bytes(8)
        # Unsure what the first 4 bytes are, the the second 4 is the message
        # content size as little-endian ordered hex
        next_size_int = int.from_bytes(
            next_size[4:], byteorder='little', signed=False)
        connect_status = self.receive_min_bytes(next_size_int)
        return connect_status.decode()

    def send_to_server(self, request: dict):
        """
        Send request to the Boom server

        :param request: message as a dict
        """
        # Must send \x11\x00\x00\x00 (little-endian unsigned 17) first,
        # maybe to tell the server what to expect? Unsure if this is the same
        # for every type of request.
        self.conn.send(bytearray(struct.pack('<I', 17)))

        # Must send request as JSON string bytes
        request_bytes = json.dumps(request).encode()
        # Must send data length as little-endian unsigned int preceding data
        request_prefix = bytearray(struct.pack('<I', len(request_bytes)))
        # Send data length bytes and data bytes together. Since status is
        # continually sent by the server once the connection was established,
        # we can't really check if the request worked unless we constantly
        # listen to updates to see if it changes. Perhaps a future improvement.
        self.conn.send(request_prefix + request_bytes)

    def connect_to_host(self):
        """
        Open connection to Boom host. This will prompt approval by the Boom
        server to allow the connection from self.client_name.

        Once this is done the boom server will start sending status updates
        non-stop until the connection is broken.
        """
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.boom_host.address, self.boom_host.port))
        # Connection string must begin with 1.3- and end with a \n
        connection_string = '1.3-{}\n'.format(self.client_name)
        self.conn.send(connection_string.encode())
        connect_status_string = self.receive_from_server()
        if connect_status_string != 'Accepted':
            if not connect_status_string:
                raise Exception(
                    'Unable to connect to Boom server, no response received. Did you turn on Boom '
                    'remote and allow the connection on the server when prompted from "{}"?'.
                    format(self.client_name))
            else:
                raise Exception('Unable to connect to Boom server, received: '.
                                format(connect_status_string))
        logging.info('Login result: %s', connect_status_string)

        # Once logged in, the boom server will send status updates non-stop,
        # store the first one so we know the available presets. After that,
        # messages from the Boom server cannot be considered a response to
        # anything since they are just non-stop current state updates. Maybe
        # eventually have a separate thread constantly listening and updating
        # the current status?
        status = self.receive_from_server()
        self.boom_status = json.loads(status)
        self.current_eq = self.boom_status['RemoteContextInfo']['ActivePreset']

    def set_eq(self, name: str):
        """
        Set the current EQ preset

        :param name: name of preset
        """
        current_preset = self.current_eq['PresetName']
        if current_preset == name:
            logging.info('Current EQ already set to "%s"', current_preset)
            return

        # Find current EQ dict
        new_eq = next(
            (preset
             for preset in self.boom_status['RemoteContextInfo']['PresetList']
             if preset['PresetDisplayName'].lower() == name.lower()), None)
        if new_eq:
            logging.info('Setting preset to: %s', name)
            self.send_to_server({
                'RemoteRequestType': 23,
                'ActivePreset': new_eq
            })
        else:
            logging.error('No preset found named "%s"', name)
