# Real Tesla Wall Connector Comms

This is some notes based on the capture of real Real Tesla Wall Connector (TWC) Gen 2 Communications between a master and a slave using the `twcprotocolmonitor.py` utility.

The master is a several years old new charger that had never been installed.
*	Serial number A18G0017973.
*	It has the TWCID of 7973.
*	It is running firmware version 4.5.3.2.
*	Total power is 11kWh.
*	It is set to 32A.

The slave is an old charger that has had heavy use and was reported faulty.  Bench testing found if may have had an issue with the CP signal but otherwise appears ok.
*	Serial number A17A0003495
*	It has the TWCID of 3495.
*	It is running firmware version 4.5.10.2.
*	Total power is 6782kWh.

Both the master and slave where connected to a single phase 240 supply and were not plugged into a vehicle.

The details of the message formats are in [Protocol.md](Protocol.md).

NB: Some fields of some messages are not yet decoded.  Specifically the serial numbers and VIN number fields.

In the summary tables the columns are:

1.	Message type sent by the master.
2.	The direction of the message or the time in seconds between the message above and below.
3.	Message type sent by the slave.

## Capture tests

These are the results from several tests.  For each test it shows:
*	The test conditions.
*	The file holding the full test data.
*	A summary of the message flow and timing.
*	Detailed samples of each messages type seen.

The tests run are:
*	[Master by itself](#master-by-itself)
*	[Slave by itself](#slave-by-itself)
*	[Master and slave with no vehicles connected](#master-and-slave-with-no-vehicles-connected)

---

### Master by itself

This is a summary of the messages from a master by itself.  The full cature is in the file `master_first_power_on.txt`.  The capture was started before the master was powered on for it's first time since it's shipping from Tesla.

| Master | Direction | Slave |
| :----- | :-------: | :---- |
| FCE1 - PRIMARY_PRESENCE - linkready1 | -> | |
| | 1.003 | |
| FCE1 - PRIMARY_PRESENCE - linkready1 | -> | |
| | 0.902 | |
| FCE1 - PRIMARY_PRESENCE - linkready1 | -> | |
| | 0.602 | |
| FCE1 - PRIMARY_PRESENCE - linkready1 | -> | |
| | 0.702 | |
| FCE1 - PRIMARY_PRESENCE - linkready1 | -> | |
| | 0.652 | |
| FCE1 - PRIMARY_PRESENCE - linkready1 | -> | |
| | 1.303 | |
| FBE2 - PRIMARY_PRESENCE2 - linkready2 | -> | |
| | 0.601 | |
| FBE2 - PRIMARY_PRESENCE2 - linkready2 | -> | |
| | 0.301 | |
| FBE2 - PRIMARY_PRESENCE2 - linkready2 | -> | |
| | 0.702 | |
| FDEB - RESP_PWR_STATUS | -> | |
| | 1.905 | |
| FDEB - RESP_PWR_STATUS | -> | |
| | Repeats every 2 seconds | |

The `FCE1 - PRIMARY_PRESENCE - linkready1` message contains:

```
Response:    FC E1 79 73 76 00 00 00 00 00 00 00 00 00 00 43
  Command:   FCE1   PRIMARY_PRESENCE - linkready1
  TWCID:     7973
    Sign:            76
    Allowed current: 0.00A
```

The `FBE2 - PRIMARY_PRESENCE2 - linkready2` message contains:

```
Response:    FB E2 79 73 76 00 00 00 00 00 00 00 00 00 00 44
  Command:   FBE2   PRIMARY_PRESENCE2 - linkready2
  TWCID:     7973
    Sign:            76
    Allowed current: 0.00A
```

The `FDEB - RESP_PWR_STATUS` message contains:

```
Ex response: FD EB 79 73 00 00 00 0B 00 F3 00 00 00 00 00 00 00 00 00 D5
  Command:   FDEB   RESP_PWR_STATUS
  TWCID:     7973
    Total power:     11kWh
    Phase 1:         243V   0A
    Phase 2:           0V   0A
    Phase 3:           0V   0A
```

NB: The `Total power:` figure is total power delivered over the lifetime of the TWC, not the power for the current charging session.  The low value seen here is probably the amount used during post manufature product verification testing.

---

### Slave by itself

This is a summary if the messages from a slave by itself.  The full cature is in the file `slave_reset.txt`.  The capture was from a running slave and the reset button was held to force a reset.

| Master | Direction | Slave |
| :----- | :-------: | :---- |
| | <- | FDE2 - SECONDARY_PRESENCE |
| | Repeats every 6 seconds | |
| | <- | FDE2 - SECONDARY_PRESENCE |
| | Reset button held down until reset | |
| | <- | FDE2 - SECONDARY_PRESENCE |
| | Repeats every 6 seconds | |
| | <- | FDE2 - SECONDARY_PRESENCE |

The `FDE2 - SECONDARY_PRESENCE` message contains:

```
Response:    FD E2 34 95 8E 0C 80 00 00 00 00 00 00 00 00 C5
  Command:   FDE2   SECONDARY_PRESENCE
  TWCID:     3495
    Sign:            8E
    Allowed current: 32.00A
```

---

### Master and slave with no vehicles connected

This is a summary if the messages between a master and a slave.  The full cature is in the file `master_and_slave.txt`.  Both master and slave running but slave's RS485 not intially connected, then the slave's RS485 is connected.

| Master | Direction | Slave |
| :----- | :-------: | :---- |
| FDEB - RESP_PWR_STATUS | -> | |
| | Repeats every 2 seconds | |
| FDEB - RESP_PWR_STATUS | -> | |
| | Slave connected | |
| | <- | FDE2 - SECONDARY_PRESENCE |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.201 | |
| FDEB - RESP_PWR_STATUS | -> | |
| | 0.301 | |
| FBEB - GET_PWR_STATE | -> | |
| | 0.201 | |
| | <- | FDEB - RESP_PWR_STATUS |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.150 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.551 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.150 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.251 | |
| FDEC - RESP_FIRMWARE_VER_EXT | -> | |
| | 0.301 | |
| FBEC - GET_FIRMWARE_VER_EXT | -> | |
| | 0.150 | |
| | <- | FDEC - RESP_FIRMWARE_VER_EXT |
| | 0.451 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.151 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.451 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.151 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.251 | |
| FDEE - RESP_VIN_FIRST | -> | |
| | 0.301 | |
| FBEE - GET_VIN_FIRST | -> | |
| | 0.150 | |
| | <- | FDEE - RESP_VIN_FIRST |
| | 0.451 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.151 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.451 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.151 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.251 | |
| FDEF - RESP_VIN_MIDDLE | -> | |
| | 0.301 | |
| FBEF - GET_VIN_MIDDLE | -> | |
| | 0.151 | |
| | <- | FDEF - RESP_VIN_MIDDLE | |
| | 0.451 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.151 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.552 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.151 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.251 | |
| FDF1 - RESP_VIN_LAST | -> | |
| | 0.251 | |
| FBF1 - GET_VIN_LAST | -> | |
| | 0.201 | |
| | <- | FDF1 - RESP_VIN_LAST |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.501 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.201 | |
| FDED - RESP_SERIAL_NUMBER | -> | |
| | 0.301 | |
| FBED - GET_SERIAL_NUMBER | -> | |
| | 0.201 | |
| | <- | FDED - RESP_SERIAL_NUMBER |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.401 | |
| FBE0 - PRIMARY_HEARTBEAT | -> | |
| | 0.201 | |
| | <- | FDE0 - SECONDARY_HEARTBEAT |
| | 0.201 | |
| FDEB - RESP_PWR_STATUS | -> | |
| | 0.301 | |
| FBEB - GET_PWR_STATE | -> | |
| | 0.201 | |
| | <- | FDEB - RESP_PWR_STATUS |
| | 0.501 | |

Then cycles back to getting firmware version, VIN, serial number and power status repeatedly.

New messages details are:

The master's `FDEB - RESP_PWR_STATUS` message contains:

```
Ex response: FD EB 79 73 00 00 00 0B 00 F3 00 00 00 00 00 00 00 00 00 D5
  Command:   FDEB   RESP_PWR_STATUS
  TWCID:     7973
    Total power:     11kWh
    Phase 1:         243V   0A
    Phase 2:           0V   0A
    Phase 3:           0V   0A
```

The slaves's `FDEB - RESP_PWR_STATUS` message contains:

```
Ex response: FD EB 34 95 00 00 1A 7E 00 F7 00 00 00 00 00 00 00 00 00 43
  Command:   FDEB   RESP_PWR_STATUS
  TWCID:     3495
    Total power:     6782kWh
    Phase 1:         247V   0A
    Phase 2:           0V   0A
    Phase 3:           0V   0A
```

The `FBEB - GET_PWR_STATE` message contains:

```
Response:    FB EB 79 73 34 95 00 00 00 00 00 00 00 00 00 A0
  Command:   FBEB   GET_PWR_STATE
  TWCID:     7973
  STWCID:    3495
```


The `FDE2 - SECONDARY_PRESENCE` message contains:

```
Response:    FD E2 34 95 81 0C 80 00 00 00 00 00 00 00 00 B8
  Command:   FDE2   SECONDARY_PRESENCE
  TWCID:     3495
    Sign:            81
    Allowed current: 32.00A
```

The `FBE0 - PRIMARY_HEARTBEAT` message contains

```
Response:    FB E0 79 73 34 95 00 00 00 00 00 00 00 00 00 95
  Command:   FBE0   PRIMARY_HEARTBEAT
  SRC TWCID:  7973
  DST TWCID:  3495
    State:           00 No current limit
    Max current:     0.00A
    Plug inserted:   00
```

The `FDE0 - SECONDARY_HEARTBEAT` message contains:

```
Response:    FD E0 34 95 79 73 00 00 00 00 00 00 00 00 00 95
  Command:   FDE0   SECONDARY_HEARTBEAT
  SRC TWCID:  3495
  DST TWCID:  7973
    State:           00 No current limit
    Max current:     0.00A
    Actual current:  0.00A
```

The `FDEC - RESP_FIRMWARE_VER_EXT` message contains:

```
Response:    FD EC 79 73 04 05 03 02 00 00 00 00 00 00 00 E6
  Command:   FDEC   RESP_FIRMWARE_VER_EXT
  TWCID:     7973
    Version:         4.5.3.2
```

The `FBEC - GET_FIRMWARE_VER_EXT` message contains:

```
Response:    FB EC 79 73 34 95 00 00 00 00 00 00 00 00 00 A1
  Command:   FBEC   GET_FIRMWARE_VER_EXT
  TWCID:     7973
  STWCID:    3495
```

The `FDEE - RESP_VIN_FIRST` message contains:

```
Ex response: FD EE 79 73 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 DA
  Command:   FDEE   RESP_VIN_FIRST
  TWCID:     7973
```

The `FBEE - GET_VIN_FIRST` message contains:

```
Response:    FB EE 79 73 34 95 00 00 00 00 00 00 00 00 00 A3
  Command:   FBEE   GET_VIN_FIRST
  TWCID:     7973
  STWCID:    3495
```

The middle and last VIN messages are similar to the first VIN message.

The `FDED   RESP_SERIAL_NUMBER` message contains:

```
Ex response: FD ED 79 73 41 31 38 47 30 30 31 37 39 37 33 00 00 00 00 35
  Command:   FDED   RESP_SERIAL_NUMBER
  TWCID:     7973
```

The `FBED - GET_SERIAL_NUMBER` message contains:

```
Response:    FB ED 79 73 34 95 00 00 00 00 00 00 00 00 00 A2
  Command:   FBED   GET_SERIAL_NUMBER
  TWCID:     7973
  STWCID:    3495
```

---

## Normal exchange summary

Before the master and slave are connected together:
*	The master sends a `FDEB - RESP_PWR_STATUS` message every 2 seconds.
*	The slave sends a `FDE2 - SECONDARY_PRESENCE` message every 6 seconds.

When the master and slave are first connected together:
*	When the master sees the slave's `FDE2 - SECONDARY_PRESENCE` message it will start it's normal polling sequence loop with a `FBE0 - PRIMARY_HEARTBEAT` message sent after the normal delay of about 0.4 seconds before sending that message type.
*	The slave no longer sends any messages unless they are an explist response to a mesage from the master.

The overall message exchange is a loop of alternating heartbeat exchanges and a parameter exchanges, where it works thru a defined list of parameters:
*	The heartbeat exchanges are two pairs `FBE0 - PRIMARY_HEARTBEAT` and `FDE0 - SECONDARY_HEARTBEAT` messages.
*	The paramater exchanges are three messages:
	*	A 'response' messages sent by the master so the slave knows that parameter for the master.
	*	A 'get' request from the master addressed to the slave for the same parameter.
	*	A 'response' message sent by the slave so the master knows that parameter for the slave.
*	The parameter requested after the heartbeat exchanges goes in this repeating sequence:
	*	The `FDEB - RESP_PWR_STATUS`.
	*	The `FDEC - RESP_FIRMWARE_VER_EXT`.
	*	The `FDEE - RESP_VIN_FIRST`.
	*	The `FDEF - RESP_VIN_MIDDLE`.
	*	The `FDF1 - RESP_VIN_LAST`.  With the prior VIN messages the complete VIN is now known.
	*	The `FDED - RESP_SERIAL_NUMBER`.
	
The timing of messages is:
*	The slave typically responds to the master in 150 to 200mS.
*	There is typically 400 to 500mS delay after the last slave response and the master sending a `FBE0 - PRIMARY_HEARTBEAT` message.
*	There is typically 250 to 300mS delay after the master sending a parameter and sending the related parameter get message to the slave.

NB: From testing with fake masters if the 0xFE character is not append to messages after the closing 0xC0 of the SLIP framing then the slave will not response to some messages.  The 0xFE is seen as `Ignored: (FC)` lines in the capture files.

