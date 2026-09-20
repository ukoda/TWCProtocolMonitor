# Tesla Wall Connector Gen 2 Protocol

This is details of the protocol used between Gen 2 of the Tesla Wall Connector (TWC). The TWC is a Tesla EVSE for AC EV charging from fixed connection AC supply connection.

There does not appear to be a published complete document for TWC protocol so this document pulls together information from multiple sources, see the credits section.  As these sources are typically reverse engineering efforts there are sometimes multiple names used for the same message and these are merged for the names used here.

## ISO model

The Open Systems Interconnection (OSI) model, [Wikipedia](https://en.wikipedia.org/wiki/OSI_model) can be used to describe the way two or more TWC communicate.

NB: In this document a `packet` refers to a sequence of bytes that includes special framing characters to mark the start and end of the sequence and the related escape characters, whereas a `message` is the sequence of bytes that is used to exchange information between TWCs.  A message is encapsulated within a packet.  Packets are used at the data link layer and messages are used at the network layer and above.


### 1. Physical layer

The physical layer is two wire half duplex [RS-485](https://en.wikipedia.org/wiki/RS-485).  Up to 4 TWCs can be connected in a daisy chain of a single twisted pair cable.  The TWC has 4 connections for two pairs of RS-485 signals `+` and `-`.  The pairs are wired in parallel in the TWC so either connector pair can be wired to.  For RS-485 adaptors with signal lines labelled `A` and `B` the A signal is the same as the + signal and the B signal is the same as the - signal.

There is no RS-485 ground reference signal connection on the TWC as EVSE typically have very strict grounding requirements related to the AC supply and the RS-485 is referenced to this.  Where third party devices are connected to the TWC RS-485 cabling it is recommend that the device also has the same ground reference.

If there is an issues with reliable message exchange then termination and bias can be added using three resistors:

* 120 ohms termination between the `+` and `-` at each end of the daisy chain.
* 680 ohms bias between the `+` and a 5V supply.
* 680 ohms bias between the `-` and ground.

Generally modern RS-485 transceivers do not need bias.  Termination should not be needed over short distances.

### 2. Data link layer

The data is sent in packets using [Asynchronous serial communication](https://en.wikipedia.org/wiki/Asynchronous_serial_communication) in the common 8N1 format at 9600 baud for each byte.

The packets use [SLIP](https://en.wikipedia.org/wiki/Serial_Line_Internet_Protocol) encapsulation with the SLIP 0xC0 marker at both ends of the packet.

There is additionally a 0xFE byte added after the packet end 0xC0 marker.  This may be to ensure the RTS signal to the RS-485 transceiver chip is asserted for the full duration of the end 0xC0 marker.  If the 0xFE byte is absent some messages may be ignored by some TWC causing erratic communications.  Some programs are missing this byte.  If you see code such as:

	msg = bytearray(b'\xc0' + msg + b'\xc0')

Consider changing it to:

	msg = bytearray(b'\xc0' + msg + b'\xc0\xfe')

### 3. Network layer

Inside messages multi-byte numbers are in big-endian order.  There are three general message types:

A request for information or a command:
* 16 bits - Command
* 16 bits - Sender's ID
* 16 bits - Destination's ID
* 9 bytes - Command specific payload
* 8 bits - Checksum

A short reply or broadcast:
* 16 bits - Command
* 16 bits - Sender's ID
* 11 bytes - Command specific payload
* 8 bits - Checksum

A long reply or broadcast:
* 16 bits - Command
* 16 bits - Sender's ID
* 15 bytes - Command specific payload
* 8 bits - Checksum

The network must have one and only one TWC as master, or a device acting as master.  It can have 1 to 3 slaves.  A TWC is put in slave mode by setting it's rotary switch to position `F`.

Only the master can send the first message type and it will supply a destination ID that matches the slave's ID that it wishes get information from or to issue a command to.  The exception is slaves uses this message type when sending a neartbeat reply.

When a slave receives a request or command  addressed to it it will send a reply that all devices, including the master that requested it, can see.  The master can also send the same reply type messages as a broadcast of information for all the slaves to see.

By default a TWC's ID number will be the last 4 digits of it's serial number, but if TWC see another device with the same ID it will generate a new random ID to use.

### 4. Transport layer

The transport layer support is limited to confirming the checksum value of a message is correct.  There is no retry method, a message with a bad checksum is simply discarded.  All information is sent periodically so a lost message will not affect overall operation.

The checksum is the sum of all bytes messages in a message except the first and last byte.  The last byte is the checksum to compare with.  If the first byte is corrupted it would go undetected.

All information message are 20 bytes or less so there is no assembly of multiple messages.  Some information, such as a vehicle's VIN number are spread over multiple messages but are assembled at layer 7, the application layer.

In normal operations a slave will never send a message unless the master has requested it.  Slaves will typically send a reply with 150 to 200mS.  A master will typically not send a packet within 400mS of the last packet sent or seen.  This prevents packet collisions.  The exception is slaves at power up as detailed in the Session layer section.

### 5. Session layer

The session layer is where the master finds the connected slaves.

At power up the master will first send six `FCE1 - PRIMARY_PRESENCE - linkready1` messages at 1 second spacing then three `FBE2 - PRIMARY_PRESENCE2 - linkready2` messages.  After that it will repeatedly send `FDEB - RESP_PWR_STATUS` every 2 seconds to advertise it's presence.

At power up the slaves will repeatedly send `FDE2 - SECONDARY_PRESENCE` every 6 seconds to advertise their presence.

When the master sees a slaves `FDE2 - SECONDARY_PRESENCE` it will save the slaves details and add the slave to it regular polling sequence.  The master's polling sequence will start with a `FBE0 - PRIMARY_HEARTBEAT` message addressed to the slave.  When the slave see this it will cease sending `FDE2 - SECONDARY_PRESENCE` messages and will reply to the master with a `FDE0 - SECONDARY_HEARTBEAT`.

If a slaves stops seeing a poll from a master for about 30 seconds it will resume sending `FDE2 - SECONDARY_PRESENCE` messages.

### 6. Presentation layer

This layer relates to how fields in messages are formatted.  In the case of the TWC is applies to multi-byte integers and strings.

16 and 32 bit integers are in big-endian order format which processing code will need to convert to the local processor's endian order.

String should be null terminated unless they take up the full space in the field.

Unused and padding fields are filled with zeros.

### 7. Application layer

This is the complete messages.  The first 16 bits of all messages is the `Command` and rest of the fields are specific to the command number.  This covered in detail in the [Messages](#messages) section.

---

## Messages

As detailed in the Network layer section there are three general message types:
*	A 16 byte request, or SECONDARY_HEARTBEAT reply, with a destination ID.
*	A 16 byte short reply with a 11 byte payload.
*	A 20 byte long reply with a 15 byte payload

NB: The term `Master` and `Primary` are used interchangeably, as are `Slave` and `Secondary`.

| Command | Name | Length | Payload |
| :------ | :--- | :----- | :------ |
| | Requests with master and slave IDs | | |
| 0xFB19 | GET_SERIAL_NUMBER_OLD | 16 | See [Request messages](#request-messages) |
| 0xFB1A | GET_MODEL_NUMBER | 16 | See [Request messages](#request-messages) |
| 0xFB1B | GET_FIRMWARE_VER | 16 | See [Request messages](#request-messages) |
| 0xFBB4 | GET_PLUG_STATE | 16 | See [Request messages](#request-messages) |
| - | | | |
| [0xFBE0](#0xfbe0) | PRIMARY_HEARTBEAT | 16 | See description |
| [0xFBE2](#0xfbe2) | PRIMARY_PRESENCE2 | 16 | See description |
| - | Requests with master and slave IDs |  |  |
| 0xFBEB | GET_PWR_STATE | 16 | See [Request messages](#request-messages) |
| 0xFBEC | GET_FIRMWARE_VER_EXT | 16 | See [Request messages](#request-messages) |
| 0xFBED | GET_SERIAL_NUMBER | 16 | See [Request messages](#request-messages) |
| 0xFBEE | GET_VIN_FIRST | 16 | See [Request messages](#request-messages) |
| 0xFBEF | GET_VIN_MIDDLE | 16 | See [Request messages](#request-messages) |
| 0xFBF1 | GET_VIN_LAST | 16 | See [Request messages](#request-messages) |
| - | <font color="red">NEVER use the next two commands</font> |  |  |
| [0xFC19](#0xfc19) | *WRITE_ID_DATE* |  | See [warning](#dangerous-commands) |
| [0xFC1A](#0xfc1a) | *WRITE_MODEL_NO* |  | See [warning](#dangerous-commands) |
| - | Commands without responses (0xFC) |  |  |
| [0xFC1D](#0xfc1d) | IDLE_MESSAGE | ? | Definition unknown |
| 0xFCB1 | START_CHARGING | 16 | See [Request messages](#request-messages) |
| 0xFCB2 | STOP_CHARGING | 16 | See [Request messages](#request-messages) |
| [0xFCE1](#0xfce1) | PRIMARY_PRESENCE | 16 | See description |
| - | Responses (0xFD) |  |  |
| [0xFD19](#0xfd19) | RESP_SERIAL_NUMBER_OLD | 20 | See description |
| [0xFD1A](#0xfd1a) | RESP_MODEL_NUMBER | 20 | See description |
| [0xFD1B](#0xfd1b) | RESP_FIRMWARE_VER | 16 | See description |
| [0xFDB4](#0xfdb4) | RESP_PLUG_STATE | 16 | See description |
| - |  |  |  |
| [0xFDE0](#0xfde0) | SECONDARY_HEARTBEAT | 16 | See description |
| - |  |  |  |
| [0xFDE2](#0xfde2) | SECONDARY_PRESENCE | 16 | See description |
| [0xFDEB](#0xfdeb) | RESP_PWR_STATUS | 20 | See description |
| [0xFDEC](#0xfdec) | RESP_FIRMWARE_VER_EXT | 16 | See description |
| [0xFDED](#0xfded) | RESP_SERIAL_NUMBER | 20 | See description |
| [0xFDEE](#0xfdee) | RESP_VIN_FIRST | 20 | See description |
| [0xFDEF](#0xfdef) | RESP_VIN_MIDDLE | 20 | See description |
| [0xFDF1](#0xfdf1) | RESP_VIN_LAST | 20 | See description |

### Request messages

* GET_SERIAL_NUMBER_OLD, GET_MODEL_NUMBER, GET_FIRMWARE_VER and GET_PLUG_STATE.
* GET_PWR_STATE, GET_FIRMWARE_VER_EXT, GET_SERIAL_NUMBER, GET_VIN_FIRST, GET_VIN_MIDDLE and GET_VIN_LAST.
* START_CHARGING and STOP_CHARGING.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | See [Messages](#messages) table |
| 2 - 3 | Master ID | Source |
| 4 - 5 | Slave ID | Destination |
| 6 - 14 | 9 x zeros | |
| 15 | Checksum | |

Has destination slave ID from which it it expects a respective response.

### 0xFBE0

PRIMARY_HEARTBEAT.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFBE0 |
| 2 - 3 | Master ID | Source |
| 4 - 5 | Slave ID | Destination |
| 6 | State | See below |
| 7 - 8 | Maximum current or error code depending on state| Current is 10mA units, i.e. multiply by 100 for Amps |
| 9 | 0 = Unplugged, 1 = Plugged in | |
| 10 - 14 | 5 x zeros | |
| 15 | Checksum | |

The State byte can be:
| State | Meaning |
| :---- | :------ |
| 0x00 | Make no change |
| 0x02 | Set error state on slave.  Will require reset to clear |
| | 0000 0001 Blink red LED 3 times, means 'Incorrect rotary switch setting' |
| | 0000 0010 Blink red LED 5 times, means 'More than three Wall Connectors are set to Slave'|
| | 0000 0100 Blink red LED 6 times, means 'The networked Wall Connectors have different maximum current capabilities' |
| 0x05 | Set slave current limit to 'Max Current' before the car has started charging.  Send in response to slave state 0x04 heartbeat with 'Maximum current' set to 0. |
| 0x06 | Increase charge current by 2 amps.  Slave changes its heartbeat state to 0x06 in response. After 44 seconds, slave state changes to 0x0A but amp value doesn't change |
| 0x07 | Lower charge current by 2 amps. Slave changes its heartbeat state to 0x07 in response. After 10 seconds, slave raises its amp setting back up by 2A and changes state to 0x0A, unless it doesn't want the extra current |
| 0x08 | Master acknowledges that slave stopped charging, but maximum current contain an amp value the slave could be using |
| 0x09 | Tell slave charger to limit power to 'Max current'.

Has destination slave ID from which it it expects a [0xFDE0](#0xfde0) SECONDARY_HEARTBEAT response.

### 0xFBE2

PRIMARY_PRESENCE2.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFBE0 |
| 2 - 3 | Master ID | Source |
| 4 | Sign | |
| 5 - 6 | Maximum allowed current | In 10mA units, i.e. multiply by 100 for Amps |
| 7 - 14 | 8 x zeros | |
| 15 | Checksum | |

No reply is expected.

### Dangerous commands

WRITE_ID_DATE 0xFC19 and WRITE_MODEL_NO 0xFC1A.

<font color="red">NEVER use these two commands, they can brick your TWC!</font>

They write two a small area of memory that will fill up and cause boot and other failures.  It can not be erased without erasing all the firmware and restoring it using a physically connected JTag programmer.

There is no known used case where these commands are needed or are useful.

### 0xFC1D

IDLE_MESSAGE.

Unable to find any documentation on this command and have not captured any yet.

### 0xFCE1

PRIMARY_PRESENCE.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFCE1 |
| 2 - 3 | Master ID | Source |
| 4 | Sign | |
| 5 - 6 | Maximum allowed current | In 10mA units, i.e. multiply by 100 for Amps |
| 7 - 14 | 8 x zeros | |
| 15 | Checksum | |

No reply is expected.

### 0xFD19

RESP_SERIAL_NUMBER_OLD.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFD19 |
| 2 - 3 | ID | Source |
| 4 - 18| Serial number | A string that may not be zero terminated |
| 19 | Checksum | |

This message not normally seen, as the [0xFDED](#0xfded) RESP_SERIAL_NUMBER message is normally used.

### 0xFD1A

RESP_MODEL_NUMBER.

The expected format is:
| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFD1A |
| 2 - 3 | ID | Source |
| 4 - 18| Model number | A string that may not be zero terminated |
| 19 | Checksum | |

The actual format seen is:
| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFD1A |
| 2 - 12| Model number | A string that may not be zero terminated |
| 13 | Checksum | |
May be protocol 1?  Model number seen 'EVW2T32HLC'.

### 0xFD1B

RESP_FIRMWARE_VER.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFD1B |
| 2 - 3 | ID | Source |
| 4 | Major version number | |
| 5 | Minor version number | |
| 6 | Revision version number | |
| 7 - 14 | 8 x zeros | |
| 15 | Checksum | |

### 0xFDB4

RESP_PLUG_STATE.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDB4 |
| 2 - 3 | ID | Source |
| 4 | Plug state | See below |
| 5 - 14 | 10 x zeros | |
| 15 | Checksum | |

Known plug states are:

0. Unplugged.
1. Plugged in and charging.
3. Plugged in and not charging.

### 0xFDE0

SECONDARY_HEARTBEAT - Slave heartbeat

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDE0 |
| 2 - 3 | Slave ID | Source |
| 4 - 5 | Master ID | Destination |
| 6 | State | See below |
| 7 - 8 | Maximum current | In 10mA units, i.e. multiply by 100 for Amps |
| 9 - 10 | Actual current | In 10mA units, i.e. multiply by 100 for Amps |
| 11 - 14 | 4 x zeros | |
| 15 | Checksum | |

The State byte can be:
| State | Meaning |
| :---- | :------ |
| 0x00 | Ready |
| 0x01 | Plugged in, charging |
| 0x02 | Error. Such as not seeing the master recently |
| 0x03 | Plugged in, do not charge.  Can be transient, seen at end of charge or charging stop by vehicle.  It may also remain indefinitely if is master offline for too long while car is charging, in which case you may need to unplug vehicle to recover |
| 0x04 | Plugged in, ready to charge or charge scheduled |
| | Set Maximum current to 0 to request maximum available current if not already given a max value on a master 0x05 or 0x08 heartbeat state |
| | Set Maximum current to value to confirm maximum sent in earlier master heartbeat state 0x05 earlier. Later master sends state 0x00 with 0 values to ok that current use |
| 0x05 | Busy? Transient only last 1 second |
| 0x06 | Response to primary heartbeat state 6 to increase current by 2 A. 'Maximum current' will show the new current value |
| 0x07 | Response to primary heartbeat state 7 to increase current by 2 A. 'Maximum current' will show the new current value |
| 0x08 | Starting to charge? This state may remain for a few seconds while car ramps up from 0A to 1.3A, then state usually changes to 0x01. Sometimes car skips 0x08 and goes directly to 0x01 |
| | Set Maximum current to 0 to request maximum available current if not already given a max value on a master 0x05 or 0x08 heartbeat state |
| | Set Maximum current to value to confirm maximum sent in earlier master heartbeat state 0x05 earlier. Later master sends state 0x00 with 0 values to ok that current use |
| 0x09 | Response to primary heartbeat state 9. 'Maximum current' will confirm the new current value |
| 0x0A | Amp adjustment period complete. Master uses state 0x06 and 0x07 to raise or lower the slave by 2A temporarily.  When that temporary period is over, it changes state to 0A. |

Sent as a reply to a [0xFBE0](#0xfbe0) PRIMARY_HEARTBEAT.

### 0xFDE2

SECONDARY_PRESENCE.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDE2 |
| 2 - 3 | Master ID | Source |
| 4 | Sign | |
| 5 - 6 | Maximum allowed current | In 10mA units, i.e. multiply by 100 for Amps |
| 7 - 14 | 8 x zeros | |
| 15 | Checksum | |

Only sent, every 6 seconds, until it is sent a message from the master.

### 0xFDEB

RESP_PWR_STATUS.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDEB |
| 2 - 3 | ID | Source |
| 4 - 7 | Total power | Lifetime kWh delivered |
| 8 - 9 | Phase 1 voltage | |
| 10 - 11 | Phase 2 voltage | |
| 12 - 13 | Phase 3 voltage | |
| 14 | Phase 1 current | |
| 15 | Phase 2 current | |
| 16 | Phase 3 current | |
| 17 - 18 | 2 x zeros | |
| 19 | Checksum | |

* Send by master unsolicited.
* Send by slave in reply to 0xFBEB GET_PWR_STATE.

### 0xFDEC

RESP_FIRMWARE_VER_EXT.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDEC |
| 2 - 3 | ID | Source |
| 4 | Major version number | |
| 5 | Minor version number | |
| 6 | Revision version number | |
| 7 | Extended version number | |
| 8 - 14 | 7 x zeros | |
| 15 | Checksum | |

* Send by master unsolicited.
* Send by slave in reply to 0xFBEC GET_FIRMWARE_VER_EXT.

### 0xFDED

RESP_SERIAL_NUMBER.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDED |
| 2 - 3 | ID | Source |
| 4 - 14| Serial number | A string |
| 15 - 18 | 4 x zeros | |
| 19 | Checksum | |

* Send by master unsolicited.
* Send by slave in reply to 0xFBED GET_SERIAL_NUMBER.

### 0xFDEE

RESP_VIN_FIRST.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDEE |
| 2 - 3 | ID | Source |
| 4 - 10| First part of VIN number | |
| 11 - 18 | 8 x zeros | |
| 19 | Checksum | |

* Send by master unsolicited.
* Send by slave in reply to 0xFBEE GET_VIN_FIRST.

### 0xFDEF

RESP_VIN_MIDDLE.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDEF |
| 2 - 3 | ID | Source |
| 4 - 10| Middle part of VIN number | |
| 11 - 18 | 8 x zeros | |
| 19 | Checksum | |

* Send by master unsolicited.
* Send by slave in reply to 0xFBEF GET_VIN_MIDDLE.

### 0xFDF1

RESP_VIN_LAST.

| Bytes | Contents | Notes |
| :---- | :------- | :---- |
| 0 - 1 | Command | 0xFDF1 |
| 2 - 3 | ID | Source |
| 4 - 10| Last part of VIN number | |
| 11 - 18 | 8 x zeros | |
| 19 | Checksum | |

* Send by master unsolicited.
* Send by slave in reply to 0xFBF1 GET_VIN_LAST.

## Information sources and credits

Most of this information is thanks to the hard work by:
*	WinterDragoness at teslamotorsclub.com, dracoventions at github.com.
*	Craig Peacock, Craig 128 at teslamotorsclub.com, craigpeacock at github.com.

These are the links to the information sources:
* [Original TWCManager](https://github.com/dracoventions/TWCManager)
	* Replaced by [newer TWCManager](https://github.com/ngardiner/TWCManager)
	* Or [SmartTWC](https://github.com/wido/smarttwc)
	* A [C version](https://github.com/craigpeacock/TWC).
	* A [esphome](https://github.com/jnicolson/esphome-twc-controller/tree/main)  version and a [fork](https://github.com/benjaminfrombe/esphome-twc-controller) with start stop support.
* Thread on [reverse engineering](https://teslamotorsclub.com/tmc/threads/tesla-wall-connector-load-sharing-protocol.72830/page-5) comms. Also page 29.
* Discussions about [starting and stopping](https://github.com/jnicolson/esphome-twc-controller/issues/14) charge without errors and a related [pull request](https://github.com/jnicolson/esphome-twc-controller/pull/15) discussion.

The are also notes on observations from the capture of messages between a real master and slave in [Real_TWC_Comms](Real_TWC_Comms.md).
