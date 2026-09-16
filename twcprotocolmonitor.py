#! /usr/bin/python3 -u

################################################################################
#
# twcprotocolmonitor
#
# A Tesla Wall Connector (TWC) Gen 2 protocol monitor
#
# David Annett (david@annett.co.nz) 3 September 2026
#
# A simple tool to monitor the comms between a master and slave TWC.
# Based on TWCManger code from Chris Dragon.
#
# To prevent most noise between messages, add a 120ohm
# "termination" resistor in parallel to the D+ and D- lines.
# Also add a 680ohm "bias" resistor between the D+ line and +5V
# and a second 680ohm "bias" resistor between the D- line and
# ground. See here for more information:
#   https://www.ni.com/support/serial/resinfo.htm
#   http://www.ti.com/lit/an/slyt514/slyt514.pdf
# This explains what happens without "termination" resistors:
#   https://e2e.ti.com/blogs_/b/analogwire/archive/2016/07/28/rs-485-basics-when-termination-is-necessary-and-how-to-do-it-properly
#
# TODO:
#   Serial numbers and VIN numbers are not decoded.
#   Tag related to message length is misleading, probably should just show length.
#
################################################################################

import serial
import time
import re
import sys
import traceback
from datetime import datetime


#
#   Functions
#

def time_now():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]
#    return datetime.now().strftime("%H:%M:%S.%f")



def hex_str(s:str):
    return " ".join("{:02X}".format(ord(c)) for c in s)



def hex_str(ba:bytearray):
    return " ".join("{:02X}".format(c) for c in ba)



def trim_pad(s:bytearray, makeLen):
    # Trim or pad s with zeros so that it's makeLen length.
    while len(s) < makeLen:
        s += b'\x00'

    if len(s) > makeLen:
        s = s[0:makeLen]

    return s



def unescape_msg(msg:bytearray, msgLen):
    # Given a message received on the RS485 network, remove leading and trailing
    # C0 byte, unescape special byte values, and verify its data matches the CRC
    # byte.
    msg = msg[0:msgLen]

    # See notes in send_msg() for the way certain bytes in messages are escaped.
    # We basically want to change db dc into c0 and db dd into db.
    # Only scan to one less than the length of the string to avoid running off
    # the end looking at i+1.
    i = 0
    while i < len(msg):
        if msg[i] == 0xdb:
            if msg[i+1] == 0xdc:
                # Replace characters at msg[i] and msg[i+1] with 0xc0,
                # shortening the string by one character. In Python, msg[x:y]
                # refers to a substring starting at x and ending immediately
                # before y. y - x is the length of the substring.
                msg[i:i+2] = [0xc0]
            elif msg[i+1] == 0xdd:
                msg[i:i+2] = [0xdb]
            else:
                print(time_now(), "ERROR: Special character 0xDB in message is " \
                  "followed by invalid character 0x%02X.  " \
                  "Message may be corrupted." %
                  (msg[i+1]))

                # Replace the character with something even though it's probably
                # not the right thing.
                msg[i:i+2] = [0xdb]
        i = i+1

    # Remove leading and trailing C0 byte.
    msg = msg[1:len(msg)-1]
    return msg



def currentasstr(hi, low):
    current = float(hi * 256 + low) / 100
    return f'{current:.2f}'



def print_msg(msg):
    if len(msg) < 14:
        return

    # Decode message and print it

    pktlen = len(msg)

    if pktlen == 14:
        print(f'Packet:      {hex_str(msg)}')
    elif pktlen == 16:
        print(f'Response:    {hex_str(msg)}')
    elif pktlen == 20:
        print(f'Ex response: {hex_str(msg)}')

    cmd = msg[0] * 256 + msg[1]
    print(f'  Command:   {cmd:04X}', end=" ")

    if cmd == 0xfb19:
        print('  GET_SERIAL_NUMBER_OLD')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfb1a:
        print('  GET_MODEL_NUMBER')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfb1b:
        print('  GET_FIRMWARE_VER')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbb4:
        print('  GET_PLUG_STATE')
        print(f'  SRC TWCID:  {msg[2]:02X}{msg[3]:02X}')
        print(f'  DST TWCID:  {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbe0:
        print('  PRIMARY_HEARTBEAT')
        print(f'  SRC TWCID:  {msg[2]:02X}{msg[3]:02X}')
        print(f'  DST TWCID:  {msg[4]:02X}{msg[5]:02X}')
        print(f'    State:           {msg[6]:02X}', end=" ")
        if msg[6] == 0x09:
            print('Limit to max current')
        elif msg[6] == 0x00:
            print('No current limit')
        else:
            print('Unknown state')
        print(f'    Max current:     {currentasstr(msg[7], msg[8])}A')
        print(f'    Plug inserted:   {msg[9]:02X}')

    elif cmd == 0xfbe2:
        print('  PRIMARY_PRESENCE2 - linkready2')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'    Sign:            {msg[4]:02X}')
        print(f'    Allowed current: {currentasstr(msg[5], msg[6])}A')

    elif cmd == 0xfbeb:
        print('  GET_PWR_STATE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbec:
        print('  GET_FIRMWARE_VER_EXT')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbed:
        print('  GET_SERIAL_NUMBER')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbee:
        print('  GET_VIN_FIRST')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbef:
        print('  GET_VIN_MIDDLE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfbf1:
        print('  GET_VIN_LAST')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfc19:
        print('  WRITE_ID_DATE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print('  WARNING: Dangerous command!')

    elif cmd == 0xfc1a:
        print('  WRITE_MODEL_NO')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print('  WARNING: Dangerous command!')

    elif cmd == 0xfc1d:
        print('  IDLE_MESSAGE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    elif cmd == 0xfcb1:
        print('  START_CHARGING')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfcb2:
        print('  STOP_CHARGING')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'  STWCID:    {msg[4]:02X}{msg[5]:02X}')

    elif cmd == 0xfce1:
        print('  PRIMARY_PRESENCE - linkready1')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'    Sign:            {msg[4]:02X}')
        print(f'    Allowed current: {currentasstr(msg[5], msg[6])}A')

    elif cmd == 0xfd19:
        print('  RESP_SERIAL_NUMBER_OLD')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    elif cmd == 0xfd1a:
        print('  RESP_MODEL_NUMBER')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    elif cmd == 0xfd1b:
        print('  RESP_FIRMWARE_VER')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'    Version:         {msg[4]}.{msg[5]}.{msg[6]}')

    elif cmd == 0xfdb4:
        print('  RESP_PLUG_STATE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'    Plug state:      {msg[4]:02X}', end=" ")
        if msg[4] == 0:
            print('Unplugged')
        elif msg[4] == 1:
            print('Plugged in and charging')
        elif msg[4] == 3:
            print('Plugged in and not charging')
        else:
            print('Unknown')

    elif cmd == 0xfde0:
        print('  SECONDARY_HEARTBEAT')
        print(f'  SRC TWCID:  {msg[2]:02X}{msg[3]:02X}')
        print(f'  DST TWCID:  {msg[4]:02X}{msg[5]:02X}')
        print(f'    State:           {msg[6]:02X}', end=" ")
        if msg[6] == 0x09:
            print('Limit to max current')
        elif msg[6] == 0x00:
            print('No current limit')
        else:
            print('Unknown state')
        print(f'    Max current:     {currentasstr(msg[7], msg[8])}A')
        print(f'    Actual current:  {currentasstr(msg[9], msg[10])}A')

    elif cmd == 0xfde2:
        print('  SECONDARY_PRESENCE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'    Sign:            {msg[4]:02X}')
        print(f'    Allowed current: {currentasstr(msg[5], msg[6])}A')

    elif cmd == 0xfdeb:
        print('  RESP_PWR_STATUS')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        totalpwr = msg[4] * 16777216 + msg[5] * 65536 + msg[6] * 256 + msg[7]
        v1 = msg[8] * 256 + msg[9]
        v2 = msg[10] * 256 + msg[11]
        v3 = msg[12] * 256 + msg[13]
        a1 = msg[14]
        a2 = msg[15]
        a3 = msg[16]
        print(f'    Total power:     {totalpwr}kWh')
        print(f'    Phase 1:         {v1:>3}V {a1:>3}A')
        print(f'    Phase 2:         {v2:>3}V {a2:>3}A')
        print(f'    Phase 3:         {v3:>3}V {a3:>3}A')

    elif cmd == 0xfdec:
        print('  RESP_FIRMWARE_VER_EXT')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')
        print(f'    Version:         {msg[4]}.{msg[5]}.{msg[6]}.{msg[7]}')

    elif cmd == 0xfded:
        print('  RESP_SERIAL_NUMBER')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    elif cmd == 0xfdee:
        print('  RESP_VIN_FIRST')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    elif cmd == 0xfdef:
        print('  RESP_VIN_MIDDLE')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    elif cmd == 0xfdf1:
        print('  RESP_VIN_LAST')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    else:
        print('  Unknown')
        print(f'  TWCID:     {msg[2]:02X}{msg[3]:02X}')

    print()



def poll_msg():
    global ser, msg, ignoredData, msgLen, msgRxCount, timeMsgRxStart, timeMsgRxEnd

    # See if there's an incoming message on the RS485 interface.

    timeCharRxStart = time.time()
    while True:
        now = time.time()
        if ser.inWaiting() < 1:

            # No new data

            if msgLen == 0:
                # No message data waiting and we haven't received the
                # start of a new message yet.  So nothing to do
                return False

            else:
                # No message data waiting but we've received a partial
                # message, check for taking too long

                if (now - timeCharRxStart) >= 0.1:
                    if debugLevel >= 3:
                        print(time_now() + ": Msg timeout (" + hex_str(ignoredData) +
                                ') ' + hex_str(msg[0:msgLen]))
                    msgLen = 0
                    msg = bytearray()
                    ignoredData = bytearray()
                    return False

                # Not too long yet so just wait a short time

                time.sleep(0.025)
                continue

        # We have atleast 1 byte of data so grab it to process

        data = ser.read(1)
        timeCharRxStart = now

        # Skip byte before start of packet

        if msgLen == 0 and data[0] != 0xc0:
            # We expect to find these non-c0 bytes between messages, so
            # we don't print any warning at standard debug levels.
            if debugLevel >= 11:
                print("Ignoring byte %02X between messages." % (data[0]))
            ignoredData += data
            continue

        # Look for a premature packet end

        elif msgLen > 0 and msgLen < 15 and data[0] == 0xc0:
            # If you see this when the program is first started, it
            # means we started listening in the middle of the TWC
            # sending a message so we didn't see the whole message and
            # must discard it. That's unavoidable.
            # If you see this any other time, it means there was some
            # corruption in what we received. It's normal for that to
            # happen every once in awhile but there may be a problem
            # such as incorrect termination or bias resistors on the
            # rs485 wiring if you see it frequently.
            if debugLevel >= 8:
                print("Found end of message before full-length message received.  " \
                        "Discard and wait for new message.")

            msg = data
            msgLen = 1
            continue

        # Handle start of packet

        if msgLen == 0:
            msg = bytearray()
            starttimestr = time_now()
            timeMsgRxStart = now
            gap = timeMsgRxStart - timeMsgRxEnd

        # Save packet data

        msg += data
        msgLen += 1

        # Messages are usually 17 bytes or longer and end with \xc0\xfe.
        # However, when the network lacks termination and bias
        # resistors, the last byte (\xfe) may be corrupted or even
        # missing, and you may receive additional garbage bytes between
        # messages.
        #
        # TWCs seem to account for corruption at the end and between
        # messages by simply ignoring anything after the final \xc0 in a
        # message, so we use the same tactic. If c0 happens to be within
        # the corrupt noise between messages, we ignore it by starting a
        # new message whenever we see a c0 before 15 or more bytes are
        # received.
        #
        # Uncorrupted messages can be over 17 bytes long when special
        # values are "escaped" as two bytes. See notes in send_msg.
        #

        # Test for end of a packet

        if msgLen >= 16 and data[0] == 0xc0:
            break

    #
    # Finished collecting a potential packet, check it
    #

    if msgLen < 16:
        return False

    endtimestr = time_now()
    timeMsgRxEnd = now

    msg = unescape_msg(msg, msgLen)
    # Set msgLen = 0 at start so we don't have to do it on errors below.
    # len($msg) now contains the unescaped message length.
    msgLen = 0

    msgRxCount += 1
    if debugLevel >= 2:
        # print(f'Message {msgRxCount} gap {gap:.3f} from {starttimestr} to {endtimestr}')
        print(f'{starttimestr} (+{gap:.3f}) Message {msgRxCount}')

    if debugLevel >= 9:
        print(time_now() + ": (" + hex_str(ignoredData) + ') ' \
                + hex_str(msg) + "")
    elif debugLevel >= 2:
        print("Ignored: (" + hex_str(ignoredData) + ')')

    ignoredData = bytearray()

    # After unescaping special values and removing the leading and
    # trailing C0 bytes, the messages we know about are always 14 bytes
    # long in original TWCs, or 16 bytes in newer TWCs (protocolVersion
    # == 2).
    if len(msg) != 14 and len(msg) != 16 and len(msg) != 20:
        # In firmware 4.5.3, FD EB (kWh and voltage report), FD ED, FD
        # EE, FD EF, FD F1, and FB A4 messages are length 20 while most
        # other messages are length 16. I'm not sure if there are any
        # length 14 messages remaining.
        print(time_now() + ": ERROR: Message of unexpected length %d: %s" % \
                (len(msg), hex_str(msg)))
        #continue

    checksumExpected = msg[len(msg) - 1]
    checksum = 0
    for i in range(1, len(msg) - 1):
        checksum += msg[i]

    if (checksum & 0xFF) != checksumExpected:
        print("ERROR: Checksum %X does not match %02X.  Ignoring message: %s" %
            (checksum, checksumExpected, hex_str(msg)))
        return False

    return True



################################################################################
#
# Main program
#
################################################################################

# Global vars

# Choose how much debugging info to output.
# 0 is no output other than errors.
# 1 is just the most useful info.
# 2-8 add debugging info
# 9 includes raw RS-485 messages transmitted and received (2-3 per sec)
# 10 is all info.
# 11 is more than all info.  ;)
debugLevel = 8

ignoredData         = bytearray()
msg                 = bytearray()
msgLen              = 0
msgRxCount          = 0
timeMsgRxStart      = time.time()
timeMsgRxEnd        = time.time()

#   Check we have been given a device file name.

if len(sys.argv) > 1:
    rs485Adapter = sys.argv[1]
    baud = 9600
else:
    print('TWC protocol monitor\nPlease supply serial port device name')
    sys.exit(10)

#   Open the serial port in RS485 device

ser = None
ser = serial.Serial(rs485Adapter, baud, timeout=0)

#   Loop receiving and displaying packets

print('Watching for data from TWCs')

while True:
    try:
        if poll_msg():
            print_msg(msg)

        # Don't over work the CPU

        time.sleep(0.05)

    except KeyboardInterrupt:
        print(" Keyboard interrupt, exiting monitor")
        break

    except Exception as e:
        # Print info about unhandled exceptions, then continue.  Search for
        # 'Traceback' to find these in the log.
        traceback.print_exc()
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')

ser.close()
