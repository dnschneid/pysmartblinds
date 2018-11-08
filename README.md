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
sniff the BLE traffic in order to recover the MAC address and account pairing
key. Once you have this data, you can use this library either to complement or
replace the MySmartBlinds app.

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

There are several ways to find this data. At a high level, you need to snoop the
BLE packets being sent to the blinds. The key is the 3- or 7-byte packet sent to
GATT handle `0x001b` (characteristic UUID
`00001409-1212-efde-1600-785feabcd123`).

The exact method depends on what device you have at your disposal.

## Android
On Android, you can capture a bluetooth packet log using the built-in developer
tools.

### Record the bluetooth packet log
These instructions depend on the OS version and phone manufacturer.  See [this
page](https://stackoverflow.com/a/30352487/2288993) if the following doesn't
work.

1. [Enable developer options](https://developer.android.com/studio/debug/dev-options#enable).
2. Turn on "Enable Bluetooth HCI snoop log" in the developer options menu.
3. Reboot your phone.
4. Use the MySmartBlinds app to change the tilt of your blinds.
5. [Capture a bug report](https://developer.android.com/studio/debug/bug-report),
   and copy it to your computer.
6. Turn off "Enable Bluetooth HCI snoop log" (and developer options in general
   if you do not need it).
7. Reboot your phone again. Until you reboot, all bluetooth traffic will
   continue to be recorded on your phone.

### Parse the bugreport
1. Use the `util/extractkeys.py` on the bugreport zip file to extract the MAC
   and key for any blinds your phone communicated with.

## iPhone
Unknown. Probably best to borrow an Android device for this task. You may also
be able to externally sniff the traffic using a device like the
[Bluefruit](https://learn.adafruit.com/reverse-engineering-a-bluetooth-low-energy-light-bulb/sniff-protocol).
Once you have the log, you can try using `util/extractkeys.py` to parse out
the MAC and key, or you can open the log with Wireshark and find it yourself.
