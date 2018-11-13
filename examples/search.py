#!/usr/bin/env python3
""" Simple script to scanning for blinds and their keys.
Run with no parameters to do a BLE scan and keysearch the discovered blinds.
Run with one or more MAC addresses to attempt a keysearch on those.
"""
# pylint: disable=import-error

import sys
import pysmartblinds

SCAN_SECONDS = 10


def log(text):
    """ Logs to stderr, if specified. """
    sys.stderr.write(text)
    sys.stderr.flush()


def scan(seconds):
    """ Initiates a search for blind MAC addresses. """
    log("Scanning for %d seconds..." % seconds)
    macs = pysmartblinds.scan(seconds)
    if macs:
        log("\nFound %s\n" % ', '.join(macs))
    else:
        log('no blinds detected\n')
    return macs


def keyscan(mac):
    """ Searches a MAC address for a working key. """
    log("[%s]: .." % mac)
    blind = pysmartblinds.Blind(mac)
    key = None
    while key is None:
        log("\b\b%02x" % blind.key())
        key = blind.keyscan()
    if key >= 0:
        log('\n')
    else:
        log('\b\bkeyscan failed\n')
    return key


def main():
    """ Scans for MAC addresses and/or keys. """
    if len(sys.argv) == 1:
        macs = scan(SCAN_SECONDS)
    else:
        macs = sys.argv[1:]
    for mac in macs:
        data = keyscan(mac)
        if data >= 0:
            sys.stdout.write("%s = %02x\n" % (mac, data))

if __name__ == "__main__":
    main()
