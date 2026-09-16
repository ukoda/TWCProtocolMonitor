# TWCProtocolMonitor

Tesla Wall Connector Gen 2 Protocol Monitor

David Annett (david@annett.co.nz)

This is a program to snoop on the RS-485 communications between a Tesla Wall Connector (TWC) Gen 2 master and slave(s).  It will decode the messages in to a human readable format.

The program takes a single argument, the serial port device name.

NB: This program has only be tested on Linux but other OSes should work fine.

## Example output

For example here is a master sending a heartbeat message to a slave and the slave sending back a heartbeat reply:

```
16:34:14.321 (+0.401) Message 14
Ignored: (FC)
Response:    FB E0 79 73 34 95 00 00 00 00 00 00 00 00 00 95
  Command:   FBE0   PRIMARY_HEARTBEAT
  SRC TWCID:  7973
  DST TWCID:  3495
    State:           00 No current limit
    Max current:     0.00A
    Plug inserted:   00

16:34:14.522 (+0.201) Message 15
Ignored: (FC)
Response:    FD E0 34 95 79 73 00 00 00 00 00 00 00 00 00 95
  Command:   FDE0   SECONDARY_HEARTBEAT
  SRC TWCID:  3495
  DST TWCID:  7973
    State:           00 No current limit
    Max current:     0.00A
    Actual current:  0.00A
```

* The first line gives the local time, down to milliseconds, the lapsed time since the prior message and an incrementing message count.
* The second line show any characters send outside if the message packet frame.  NB: One characters is actually needed, see [Protocol.md](Protocol.md) for why.
* The third line shows the raw message, after the SLIP encapsulation has been removed, but including the checksum.
* The forth line show the message type.
* The fifth line shows the ID number of the sender.
* The subsequent lines depend on the message type.

## Further reading

* [Protocol.md](Protocol.md) gives a definition of the TWC Gen 2 protocol based on the limited public information available.  It includes links to the information sources used.
* [Real_TWC_Comms.md](Real_TWC_Comms.md) gives a break down of the message exchanged between real a TWC master and slave and notes on how the protocol is used.  The related captures are in txt files include in this repo.

## To do

This program is complete enough to be useful as is.  Remain to do, but not a priority, are:
*   Serial numbers and VIN numbers are not decoded.
*   Tag related to message length is misleading, probably should just show length.
