# pysmartblinds
Python interface to control BLE-based
[MySmartBlinds](https://www.mysmartblinds.com/).

This library is not affiliated with nor condoned by MySmartBlinds, and has been
written without any knowledge of its internal workings. Be aware that this
software is provided as-is, and using it probably voids your [MySmartBlinds
warranty](https://www.mysmartblinds.com/pages/warranty).

Neither MySmartBlinds nor developers of this library are responsible for any
damage or misconfiguration to your blinds or MySmartBlinds system as a result
of using this library.


## Features
 * Enables direct control of [MySmartBlinds](https://www.mysmartblinds.com/)
   motorized blinds.
 * Converts the absolute position-based protocol of MySmartBlinds into a
   relative one, enabling natural up/down/stop control as well as timed
   transitions.


## Caveats

### Firmware version
This library has been tested to work with firmware version 2.0. No other
versions have been tested, and there is no guarantee that this library will work
if you update the firmware beyond 2.0.

### Concurrent usage
This library currently uses [pygatt](https://pypi.org/project/pygatt/), which
limits to using one blind at a time. In the future, a
[pygattlib](https://pypi.org/project/pygattlib/) backend would enable concurrent
multi-blind support.

### Pairing
This library does not emulate the pairing process. You must use a device
supported by MySmartBlinds, a MySmartBlinds account, as well as the official
app, to pair, configure, and calibrate your blinds.

### Key retrieval
Since the blinds are paired to your MySmartBlinds account, you will need to
sniff or scan the BLE traffic in order to recover the MAC address and account
pairing key. Once you have this data, you can use this library either to
complement or replace the MySmartBlinds app.

### External adjustments
The BLE protocol (as of firmware version 2.0) does not include state read-back
(it just returns 0xFF). If you use this library in conjunction with the
MySmartBlinds app, automations stored on the blinds, or the external tilt wand,
any adjustments to blind position made external to this library will not be
recognized. The next operation made with the library will reset the blind
position to the last recorded state. Keep in mind that uninstalling the
MySmartBlinds app does not disable any automations you may have created within
the app.


# Discovering MAC and keys for blinds
Once you have paired, configured and calibrated your blinds in the MySmartBlinds
app, you need to discover the MAC address and key in order to speak with it.

At a high level, you need to snoop the BLE packets being sent to the blinds. The
key is a packet sent to GATT handle `0x001b` (characteristic UUID
`00001409-1212-efde-1600-785feabcd123`).

However, it seems that only the first byte in the key is actually needed, so it
doesn't take too long to scan for it, and this library provides a means to do
so.

`scan.py` in the examples folder wraps this functionality; just run it and see
what it returns.
