#  Copyright 2018 The pysmartblinds authors.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
pysmartblinds:
Python interface to control BLE-based MySmartBlinds.

This library is not affiliated with nor condoned by MySmartBlinds, and has been
written without any knowledge of its internal workings. Be aware that this
software is provided as-is, and using it probably voids your MySmartBlinds
warranty.

Neither MySmartBlinds nor developers of this library are responsible for any
damage or misconfiguration to your blinds or MySmartBlinds system as a result
of using this library.
"""

# Depends: pygatt, pexpect
# Config: sudo setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
# pylint: disable=import-error,too-many-instance-attributes

from math import ceil
from threading import Timer
import pygatt


def scan(seconds=10):
    """ Performs a scan for MySmartBlinds blinds.
    Returns a list of MAC address strings.
    """
    ble_names = {'SmartBlind_DFU'}
    gatt = pygatt.GATTToolBackend()
    try:
        gatt.start(reset_on_start=False)
        devices = gatt.scan(timeout=seconds)
    finally:
        gatt.stop()
    return [dev['address'] for dev in devices if dev['name'] in ble_names]


class Blind(object):
    """ Manages a single MySmartBlinds blind. """
    BLEError = pygatt.exceptions.BLEError

    _KEYSCAN_RETRIES = 5
    _MIN_STEP = 1
    _MIN_DELAY = 0.5
    _MIN_TRANSITION_TIME = 1
    _BASE_RATE = 200.0 / 10.0
    _KEY_HANDLE = 0x001b
    _SET_HANDLE = 0x001f
    _BLE_TIMEOUT = 7.0

    def __init__(self, mac, key=0):
        """ Initializes the blind device.
        mac: MAC address string in the form of "12:34:56:78:9A:BC"
        key: 1-byte key either as an int or a string in the form of "ab"
        """
        self._mac = mac[:17].upper()
        if isinstance(key, str):
            self._key = int(key[0:2], 16)
        elif isinstance(key, int):
            self._key = key
        else:
            self._key = key[0]
        self._callback = None

        self._pos = 0
        self._dir = 0
        self._target = None

        self._gatt = None
        self._dev = None
        self._pending = Timer(0, None)

    def _connect(self):
        try:
            if not self._gatt:
                self._gatt = pygatt.GATTToolBackend()
                self._gatt.start(reset_on_start=False)
            if not self._dev:
                self._dev = self._gatt.connect(
                    self._mac,
                    timeout=self._BLE_TIMEOUT,
                    address_type=pygatt.backends.BLEAddressType.random)
                self._dev.char_write_handle(Blind._KEY_HANDLE, (self._key,),
                                            True)
        except pygatt.exceptions.NotConnectedError:
            self._disconnect()
            return False
        except pygatt.exceptions.NotificationTimeout:
            self._disconnect()
            return False
        except pygatt.exceptions.BLEError as exception:
            self._disconnect()
            raise exception
        return True

    def _disconnect(self):
        self._pending.cancel()
        self._dev = None
        if self._gatt:
            self._gatt.stop()
            self._gatt = None

    def _set(self, pos):
        if not self._connect():
            return False
        pos = int(min(max(pos, 0), 200))
        try:
            self._dev.char_write_handle(Blind._SET_HANDLE, (pos,), True)
        except pygatt.exceptions.NotConnectedError:
            self._disconnect()
            return False
        except pygatt.exceptions.NotificationTimeout:
            self._disconnect()
            return False
        except pygatt.exceptions.BLEError as exception:
            self._disconnect()
            raise exception
        self._pos = pos
        if self._callback:
            self._callback()
        return True

    def _update(self):
        if not self._dir:
            return True
        ideal_step = abs(self._dir) * Blind._MIN_DELAY
        actual_step = max(ceil(ideal_step), Blind._MIN_STEP)
        delay = Blind._MIN_DELAY * actual_step / ideal_step
        if self._dir < 0:
            pos = max(self._pos - actual_step, self._target or 0)
        else:
            pos = min(self._pos + actual_step, self._target or 200)
        if not self._set(pos):
            return False
        if 0 < self._pos < 200 and self._pos != self._target:
            self._pending = Timer(delay, self._update)
            self._pending.start()
        else:
            self.stop()
        return True

    def keyscan(self):
        """ Continues a search for the blind's key.
        returns None if the scan should be continued.
        returns False if the scan failed.
        returns True if the key was found (see key())
        """
        self.stop()
        tries = Blind._KEYSCAN_RETRIES
        while not self._set(200):
            tries -= 1
            if tries == 0:
                return False
        if self._set(200):
            return True
        elif self._key == 0xFF:
            self._key = 0
            return False
        else:
            self._key += 1
            return None

    def key(self):
        """ Returns the current key. """
        return self._key

    def set_callback(self, callback=None):
        """ Sets or clears a callback for whenever the blinds change state. """
        self._callback = callback

    def dir(self):
        """ Returns the current rate of movement of the blinds. """
        return self._dir

    def pos(self, pos=None, duration=0):
        """ Gets or sets the blind position, with an optional transition. """
        if pos is None:
            return self._pos
        self._pending.cancel()
        self._target = min(max(int(pos), 0), 200)
        self._dir = ((self._target - self._pos) /
                     max(float(duration), Blind._MIN_DELAY / 2))
        return self._update()

    # pylint: disable=invalid-name
    def up(self):
        """ Makes the blinds tilt up. Repeated calls speed it up. """
        self._pending.cancel()
        self._target = None
        self._dir = max(Blind._BASE_RATE, self._dir * 2)
        return self._update()

    def down(self):
        """ Makes the blinds tilt down. Repeated calls speed it up. """
        self._pending.cancel()
        self._target = None
        self._dir = min(-Blind._BASE_RATE, self._dir * 2)
        return self._update()

    def stop(self):
        """ Stops any motion of the blinds. """
        self._pending.cancel()
        self._target = None
        self._dir = 0
        self._disconnect()
        if self._callback:
            self._callback()
        return True
