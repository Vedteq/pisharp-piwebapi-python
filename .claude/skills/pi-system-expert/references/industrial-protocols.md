# Industrial Protocols & Systems -- Expert Technical Reference

## 1. OPC

### OPC DA (Data Access)
- Windows-only, COM/DCOM-based client/server
- Item addressing: hierarchical tag tree (e.g., `Channel1.Device1.Temperature`), vendor-specific syntax
- Data types: COM VARIANT (VT_R4, VT_R8, VT_I2, VT_I4, VT_BOOL, VT_BSTR)
- **Quality codes** (16-bit): QQ=Major (Good 11, Bad 00, Uncertain 01), SSSS=Substatus, LL=Limit
  - 0xC0 = Good, 0x00 = Bad, 0x40 = Uncertain
- Read modes: Synchronous, Asynchronous, Advise (subscription with deadband)

### OPC HDA (Historical Data Access)
- Raw reads, Interpolated reads, Aggregate reads (TimeAvg, Min, Max, Count, Range, StdDev)
- Aggregates only work with numeric types

### OPC AE (Alarms & Events)
- Event types: Simple (one-shot), Tracking (state), Condition (stateful alarms with transitions)
- Severity: 1-1000 scale
- Subscription filters by area, source, type, severity, category

### OPC UA (Unified Architecture)
- Platform-independent (Linux, Windows, embedded), TCP port **4840** or HTTPS
- Replaces all Classic OPC specs in single unified specification
- **Node addressing**: NodeId = NamespaceIndex + Identifier. Node types: Objects, Variables, Methods, ObjectTypes, etc.
- **Security (3 layers)**:
  1. Transport: X.509 certificates, policies: None, Basic256Sha256, Aes128_Sha256_RsaOaep, Aes256_Sha256_RsaPss
  2. User auth: Anonymous, Username/Password, X.509 Certificate, Kerberos/SAML
  3. Authorization: Role-based per node
- Subscriptions: MonitoredItems with sampling intervals and deadbands, push notifications

---

## 2. PI Interfaces and Connectors

### Three Generations

| Gen | Technology | Relay | OS |
|---|---|---|---|
| Legacy Interfaces | PI API | Direct to DA | Windows |
| PI Connectors | OMF | Connector Relay | Windows |
| AVEVA Adapters | OMF | PI Web API | Windows + Linux |

### PI Interface for OPC DA
- Windows service on Interface Node
- **Location codes**: Location1=Instance ID, Location2=Data type, Location3=Point type (0=Polled, 1=Advise, 2=Output), Location4=Scan class, Location5=Deadband
- Scan class 1 reserved for Advise tags (Location3 must be 1)
- `PointSource` identifies the interface; `InstrumentTag` holds OPC Item ID

### PI Interface for UFL (Universal File Loader)
- Parses CSV, fixed-width, XML, log files
- Config sections: `[INTERFACE]`, `[PLUG-IN]`, `[SETTING]`, `[FIELD]` (mandatory), `[DATA]`

### Buffering

| | PIBufSS (Recommended) | BufServ (Legacy) |
|---|---|---|
| Auto-detect collective | Yes | No |
| HA failover | Yes | Manual config |
| Constraint | Can't coexist with Connector on same point | - |

---

## 3. SCADA Systems

### Data Flow
```
Sensors → I/O Cards → PLC/DCS → SCADA/HMI → PI Data Archive → PI AF/Analytics
```

### Platform Integration

| Platform | PI Integration |
|---|---|
| **AVEVA System Platform** (Wonderware) | AVEVA Historian can replicate to PI; tight ecosystem |
| **Siemens WinCC** | OPC UA/DA server built-in; KEPServerEX common bridge |
| **Rockwell FactoryTalk** | **FactoryTalk Historian SE IS PI System** (licensed/branded PI) |
| **GE iFIX** | Via OPC DA (iFIX has built-in OPC server) |
| **Honeywell Experion** | OPC DA/UA, dedicated Honeywell-PI interfaces |

---

## 4. PLC/DCS Fundamentals

### I/O Types
- **DI/DO**: Discrete (1-bit) — switches, relays, solenoids
- **AI/AO**: Analog (12-16 bit) — 4-20mA, 0-10V, thermocouples, RTDs

### Tag Addressing by Vendor
- **Allen-Bradley (Rockwell)**: Tag-based names (`FIC_101.PV`, `Motor_1.Running`)
- **Siemens S7**: Address-based (`I0.0`, `Q1.0`, `MW100`, `DB1.DBW0`)
- **Modicon (Schneider)**: Register-based (`%I0.0.1`, `%MW100`, `400001`)

### Polling vs Exception
- **Polling**: Fixed interval reads. Predictable load, can miss fast transients.
- **Exception/Advise**: Server notifies on change. Lower bandwidth, captures transients.

---

## 5. Industrial Protocols

### Modbus TCP/RTU
- RTU: Serial RS-485, binary, CRC-16. TCP: Ethernet, port **502**, no CRC.

| Register Type | Range | Access | Size |
|---|---|---|---|
| Coils | 00001-09999 | R/W | 1 bit |
| Discrete Inputs | 10001-19999 | Read | 1 bit |
| Input Registers | 30001-39999 | Read | 16 bit |
| Holding Registers | 40001-49999 | R/W | 16 bit |

- **#1 gotcha**: Address 40001 = protocol offset 0 (1-offset vs 0-offset confusion)
- 32-bit values: two consecutive 16-bit registers, byte order is vendor-specific

### MQTT / Sparkplug B
- MQTT: pub/sub, port **1883**/8883 (TLS), QoS 0/1/2
- Sparkplug B topic: `spBv1.0/{group}/{msg_type}/{node}[/{device}]`
- Messages: NBIRTH/DBIRTH (online), NDEATH/DDEATH (offline), NDATA/DDATA (values), NCMD/DCMD (commands)
- Payload: Protobuf binary, supports metric aliasing for bandwidth

### BACnet
- Building automation (HVAC, lighting, fire). Port **47808** UDP.
- Object model: Analog/Binary/Multi-State Input/Output/Value, Schedule, Trend Log
- Addressing: Device Instance (unique) + Object Type + Object Instance
- Layers: BACnet/IP, BACnet/MSTP (RS-485), BACnet/Ethernet

### DNP3
- Utilities (electric/water). IEEE 1815.
- Master-Outstation model. Supports unsolicited responses.
- Class polling: Class 0 (static), Class 1/2/3 (events at priorities)
- Analog deadbands for event generation

### EtherNet/IP
- CIP over Ethernet. Port **44818** (TCP explicit), **2222** (UDP implicit).
- Explicit = request/response (config). Implicit = connection-oriented I/O (time-critical).
- PI integration: via OPC server (KEPServerEX), not direct.

### PROFINET
- Siemens industrial Ethernet. RT (250us-512ms), IRT (31.25us deterministic), NRT (standard TCP/IP).
- GSDML files describe device capabilities.
- PI integration: via OPC UA on Siemens PLC/HMI.

---

## 6. GMP/Regulated Environments

### 21 CFR Part 11 — Key Requirements
1. **System Validation**: Accuracy, reliability, consistent performance
2. **Audit Trails**: Computer-generated, timestamped, original/changed values, who/why, not modifiable
3. **Access Controls**: RBAC, operational checks, authority checks
4. **Electronic Signatures**: Unique to one individual, two distinct components (ID + password)
5. **Record Protection**: Operational checks, device checks, retrievable throughout retention

### ALCOA+ Principles
- **A**ttributable, **L**egible, **C**ontemporaneous, **O**riginal, **A**ccurate
- **+** Complete, Consistent, Enduring, Available

### PI System Compliance
- PI Audit Database tracks config changes
- Point Security: granular read/write per tag
- Annotations provide audit trail for manual data entry
- RtReports supports electronic signatures
- PI Manual Logger for 21 CFR Part 11 manual data entry

### Validation (IQ/OQ/PQ)
- **IQ**: Verify installation per specs (versions, patches, hardware, infrastructure)
- **OQ**: Test functionality (data collection, security, interfaces, backup/restore, failover)
- **PQ**: Verify in production with real data, confirm data integrity end-to-end

### GAMP 5 Classification
PI System = **Category 4 (Configured Products)**: requires supplier assessment, URS, functional spec, configuration spec, IQ/OQ/PQ, traceability matrix, risk assessment.

Sources: [OPC UA](https://en.wikipedia.org/wiki/OPC_Unified_Architecture), [OPC DA Quality Codes](https://support.softwaretoolbox.com/app/answers/detail/a_id/414), [PI Interface for OPC DA](https://docs.aveva.com/bundle/pi-interface-for-opc-da/page/1011307.html), [PI Buffer Subsystem](https://docs.aveva.com/bundle/pi-server-s-buf-ha/page/1020154.html), [Sparkplug Spec](https://www.eclipse.org/tahu/spec/sparkplug_spec.pdf), [21 CFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11), [GAMP 5](https://intuitionlabs.ai/articles/gamp-5-categories-explained)
