#!/usr/bin/env python3
""" Provides a webserver with the following endpoints for controlling blinds:

GET /blind_name/pos: Returns the blind tilt, from 0 (down) to 200 (up).
POST /blind_name/up: Tilt blind up. Multiple POSTs will increase the speed.
POST /blind_name/down: Tilt blind down. Multiple POSTs will increase the speed.
POST /blind_name/stop: Stop the blind at its current tilt.
POST /blind_name/set/pos: Moves the blind quickly to tilt position [pos].
POST /blind_name/set/pos/seconds: Moves the blind over the course of [seconds].

Server address and blinds configuration are set via the global variables below.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from pysmartblinds import Blind

SERVER_ADDRESS = ('', 1500)

BLINDS = {
    'living_room': {
        'description': 'Living Room',
        'mac': '12:34:56:78:9A:BC',
        'key': (0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE)
    },
}


def init_devices():
    """ Configures devices and puts them into known states. """
    for blind in BLINDS:
        blind = BLINDS[blind]
        blind['blind'] = Blind(blind['mac'], blind['key'])
        blind['blind'].pos(200)


class HTTPHandler(BaseHTTPRequestHandler):
    """ Handles HTTP events """

    # pylint: disable=invalid-name
    def do_POST(self):
        """ Handles POST requests """
        params = self.path.split('/')
        # Parse and check command
        if len(params) < 3:
            self.send_error(404)
            return
        blind, action = params[1:3]
        params = params[3:]

        # Parse and check command
        if blind not in BLINDS or action not in ('up', 'down', 'stop', 'set'):
            self.send_error(404)
            return
        if action == 'set' and (len(params) == 0 or not params[0].isdigit()):
            self.send_error(404)
            return

        # Get the device to control
        blind = BLINDS[blind]['blind']
        # Send the command
        response = 500
        try:
            if action == 'up':
                response = blind.up()
            elif action == 'down':
                response = blind.down()
            elif action == 'stop':
                response = blind.stop()
            elif action == 'set':
                response = blind.pos(params[0], len(params) >= 2 and params[1])
            response = response and 204 or 504
        except Blind.BLEError as exception:
            self.send_response(500)
            self.end_headers()
            raise exception

        # Reply to the request
        self.send_response(response)
        self.end_headers()

    def do_GET(self):
        """ Handles GET requests """
        params = self.path.split('/')
        if len(params) != 3:
            self.send_error(404)
            return

        # Parse and check command
        _, blind, action = params
        if action != 'pos' or blind not in BLINDS:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'%d' % BLINDS[blind]['blind'].pos())


if __name__ == "__main__":
    init_devices()
    HTTPServer(SERVER_ADDRESS, HTTPHandler).serve_forever()
