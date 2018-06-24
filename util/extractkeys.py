#!/usr/bin/env python3
"""
Extracts MySmartBlinds MAC and key from a Bluetooth HCI log
Assumes MySmartBlinds MAC addresses all start with D9:96:AD
"""

import re
import sys
import zipfile

MAC_FILTER = b'(.{3}\xAD\x96\xD9)'
KEY_FILTER = b'\x02\x40\x00\x0E\x00\x0A\x00\x04\x00\x12\x1B\x00(.{7})'

if len(sys.argv) != 2:
    sys.stderr.write("Usage: %s bugreport.zip\n" % sys.argv[0] +
                     "       %s btsnoop_hci.log\n" % sys.argv[0])
    sys.exit(2)

f = sys.argv[1]
if zipfile.is_zipfile(f):
    f = zipfile.ZipFile(f).open('FS/data/misc/bluetooth/logs/btsnoop_hci.log')
else:
    f = open(f, 'rb')

results = {}
mac = ''
for match in re.finditer(b'%s|%s' % (MAC_FILTER, KEY_FILTER), f.read()):
    if match.group(1):
        mac = ':'.join('%02X' % x for x in match.group(1)[::-1])
    if mac and match.group(2):
        results[mac] = ''.join('%02x' % x for x in match.group(2))

for mac in results:
    sys.stdout.write('%s = %s\n' % (mac, results[mac]))
